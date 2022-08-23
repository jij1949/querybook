import ldap3
from ldap3 import Server, Connection
import re
import time

from app.db import DBSession, with_session
from app.flask_app import celery
from lib.logger import get_logger
from logic.user import get_user_by_name
from logic.schedule import with_task_logging
from env import QuerybookSettings
from logic.admin import (
    get_users_in_query_engine,
    add_user_to_query_engine,
    remove_user_to_query_engine,
    get_all_query_engines,
)
from logic.environment import (
    get_users_in_environment,
    add_user_to_environment,
    remove_user_to_environment,
    get_all_environment,
)

LOG = get_logger(__file__)

################################
# ------- LDAP Helpers ------- #
################################


ldap_uid_pattern = re.compile(r"uid=([^,]+)")

ad_server = QuerybookSettings.LDAP_CONN
ad_bind_user = QuerybookSettings.LDAP_BIND_USER
ad_bind_password = QuerybookSettings.LDAP_BIND_PASSWORD
bind_domain = QuerybookSettings.LDAP_SEARCH
global_groups = QuerybookSettings.LDAP_GLOBAL_GROUPS


def ad_connect(args, ad_server, ad_bind_user, ad_bind_password):
    """
    :param ad_server: LDAP server connection
    :param ad_bind_user: Ldap service account users
    :param ad_bind_password: Password to the ldap users
    :return: return the ldap connection
    """

    server = Server(ad_server, use_ssl=False, get_info=ldap3.ALL)
    conn = Connection(
        server,
        user=ad_bind_user,
        password=ad_bind_password,
        auto_bind=True,
        client_strategy=ldap3.SYNC,
        auto_referrals=True,
        use_referral_cache=True,
    )

    LOG.debug(f"AD server: {ad_server}, bind user: {conn.extend.standard.who_am_i()}")

    return conn


def ad_query_group_existence(args, conn, ad_group):
    """
    :param conn: ldap connection object
    :param ad_group: string of security group
    :return: if group does not exists, will return false else would return the searched group
    """
    search_base = "CN={0},OU=Security Groups,{1}".format(ad_group, bind_domain)

    # Check if group exists, because second query (members of group) always returns success (with empty members)
    # if the group does NOT exist.
    try:
        success = conn.search(
            search_base=search_base,
            search_filter="(objectclass=group)",
            attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES],
            size_limit=0,
        )
    except Exception as e:
        LOG.warning(
            f"Unable to query AD for existence of group {ad_group}: {e.message}"
        )
        success = False

    return success


def ad_query_group_membership(args, conn, ad_group, level=1, visited_groups=[]):
    """
    :param conn: ldap connection object
    :param ad_group: string of security group
    :param level: interger
    :param visited_groups: list of visited groups
    :return: returns a tuple of success bool and a set of the member list
    """
    ad_group_members = []
    search_base = "CN={0},OU=Security Groups,{1}".format(ad_group, bind_domain)
    # filter disabled users, with UserAccountControl
    user_search_filter = "(&(|(objectCategory=group)(objectCategory=user))(memberOf={0})(!(UserAccountControl:1.2.840.113556.1.4.803:=2)))".format(
        search_base
    )

    SAM_GROUP_OBJECT = 0x10000000

    if level == 1:
        visited_groups = []

    try:
        LOG.info(f"Querying AD membership of group {ad_group}... ")
        visited_groups.append(ad_group)
        start = time.time()

        # pagination with generator to overcome 1000 search result limit by AD
        entries = conn.extend.standard.paged_search(
            search_base=bind_domain,
            search_filter=user_search_filter,
            attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES],
            search_scope=ldap3.SUBTREE,
            size_limit=0,
            paged_size=1000,
            generator=True,
        )

        if entries is not None:
            total_entries = 0
            for entry in entries:
                if "attributes" in entry:
                    if "sAMAccountType" in entry["attributes"]:
                        if entry["attributes"]["sAMAccountType"] == SAM_GROUP_OBJECT:
                            if (
                                entry["attributes"]["sAMAccountName"]
                                not in visited_groups
                            ):
                                if args.tracead:
                                    LOG.info(
                                        "Found member group {0}".format(
                                            entry["attributes"]["sAMAccountName"]
                                        )
                                    )
                                (sub_success, sub_members) = ad_query_group_membership(
                                    args,
                                    conn,
                                    entry["attributes"]["sAMAccountName"],
                                    level=level + 1,
                                    visited_groups=visited_groups,
                                )
                                if sub_success:
                                    ad_group_members.extend(sub_members)
                            else:
                                if args.tracead:
                                    LOG.info(
                                        f"Already queried group {entry['attributes']['sAMAccountName']}, skipping."
                                    )
                        # Filter users with no email or
                        #  is a Service account
                        elif entry["attributes"]["sAMAccountName"] is not None and (
                            not entry["attributes"]["sAMAccountName"].startswith("s-")
                        ):
                            if args.tracead:
                                LOG.info(
                                    f"Found user {entry['attributes']['sAMAccountName']}"
                                )
                            ad_group_members.append(
                                entry["attributes"]["sAMAccountName"]
                            )
                        else:
                            LOG.debug(
                                f"Warning - user {entry['attributes']['sAMAccountName']} has no email address or service account (not following naming standard)"
                                ", not syncing to querybook"
                            )
                        total_entries += 1
        end = time.time()
        LOG.debug(
            f"Examined {total_entries} entries, took {round(end - start, 1)} seconds"
        )
        success = True
    except Exception as e:
        LOG.error(
            f"Unable to query AD for members of {ad_group}: {e.message}", exc_info=True
        )
        success = False
        # return members, but remove duplicates in case querying members of sub-groups added dupes.
    return success, list(set(ad_group_members))


class Object(object):
    pass


#####################################
# ------- Querybook Helpers ------- #
#####################################


@with_session
def get_environment_users_delta(environment_id, user_groups, session=None):
    """
    :param environment_id: int id of the environment
    :param user_groups: a set of users that will be added to environment
    :param session: session object
    :return: a set of users to add and users to remove from the environment
    """
    # todo: don't hack the limit

    users_in_environment = get_users_in_environment(
        environment_id, 0, 1000000, session=session
    )
    users_in_environment_set = set(map(lambda u: u.username, users_in_environment))

    # Returns users to add, users to remove
    return (
        user_groups - users_in_environment_set,
        users_in_environment_set - user_groups,
    )


@with_session
def update_user_environments_with_groups(environment, user_groups, session=None):
    """
    :param environment: querybook env
    :param user_groups: set of users to update to the env
    :param session: session object
    :return: None
    """
    users_to_add, users_to_remove = get_environment_users_delta(
        environment.id, user_groups, session=session
    )

    LOG.info(f"Total users: {len(user_groups)}")
    LOG.info(f"Users to add: {len(users_to_add)}")
    LOG.info(f"Users to remove: {len(users_to_remove)}")

    for username in users_to_add:
        user = get_user_by_name(username, session=session)
        if user:
            LOG.debug(f"Adding {username} to {environment.name} ({environment.id})")
            add_user_to_environment(
                user.id, environment.id, commit=False, session=session
            )

    for username in users_to_remove:
        user = get_user_by_name(username, session=session)
        if user:
            LOG.debug(f"Removing {username} from {environment.name} ({environment.id})")
            remove_user_to_environment(
                user.id, environment.id, commit=False, session=session
            )
    session.commit()


@with_session
def get_query_engine_users_delta(query_engine_id, user_groups, session=None):
    """
    :param query_engine_id: int id of the query engine
    :param user_groups: a set of users that will be added to query_engine
    :param session: session object
    :return: a set of users to add and users to remove from the query engine
    """
    # todo: don't hack the limit

    users_in_query_engine = get_users_in_query_engine(
        query_engine_id, 0, 1000000, session=session
    )
    users_in_query_engine_set = set(map(lambda u: u.username, users_in_query_engine))

    # Returns users to add, users to remove
    return (
        user_groups - users_in_query_engine_set,
        users_in_query_engine_set - user_groups,
    )


@with_session
def update_user_query_engines_with_groups(query_engine, user_groups, session=None):
    """
    :param query_engine: querybook env
    :param user_groups: set of users to update to the env
    :param session: session object
    :return: None
    """
    users_to_add, users_to_remove = get_query_engine_users_delta(
        query_engine.id, user_groups, session=session
    )

    LOG.info(f"Total users: {len(user_groups)}")
    LOG.info(f"Users to add: {len(users_to_add)}")
    LOG.info(f"Users to remove: {len(users_to_remove)}")

    for username in users_to_add:
        user = get_user_by_name(username, session=session)
        if user:
            LOG.debug(f"Adding {username} to {query_engine.name} ({query_engine.id})")
            add_user_to_query_engine(
                user.id, query_engine.id, commit=False, session=session
            )

    for username in users_to_remove:
        user = get_user_by_name(username, session=session)
        if user:
            LOG.debug(
                f"Removing {username} from {query_engine.name} ({query_engine.id})"
            )
            remove_user_to_query_engine(
                user.id, query_engine.id, commit=False, session=session
            )
    session.commit()


#####################################
# ------- Running task ------- #
#####################################


@celery.task(bind=True)
@with_task_logging()
def sync_ldap_task(self):
    """
    :return: returns None, runs the task of syncing permissions via LDAP
    """
    LOG.info("Starting LDAP Sync Task...")

    with DBSession() as session:
        args = Object()
        args.dryrun = False
        args.tracead = False

        conn = ad_connect(args, ad_server, ad_bind_user, ad_bind_password)

        # Get global groups members since they should be added to all environments
        LOG.debug(f"Getting global groups members: {global_groups}")
        global_groups_members = get_groups_members_list(args, global_groups, conn)

        ### Sync Environments ###

        LOG.info("Syncing Environments...")
        env_list = get_all_environment(False, session=session)

        for env in env_list:
            feature_params = env.feature_params or {}

            # Enable or disable the sync
            enable_ad_sync = feature_params.get("enable_ad_sync", False)

            # Controls whether global groups are added to the environment
            sync_global_groups = feature_params.get("sync_global_groups", False)

            # Comma-separated list of groups to sync to the environment
            access_control_groups = [
                group
                for group in feature_params.get("access_control_groups", "").split(",")
                if group
            ]

            LOG.info(f"Access control groups: {access_control_groups}")

            if enable_ad_sync:
                try:
                    LOG.info(f"Syncing Environment: {env.name} ({env.id})")
                    LOG.debug(f"Feature Params: {env.feature_params}")
                    LOG.info(f"Access control groups: {access_control_groups}")

                    members_list = []

                    if sync_global_groups:
                        members_list.extend(global_groups_members)

                    members_list.extend(
                        get_groups_members_list(args, access_control_groups, conn)
                    )

                    update_user_environments_with_groups(
                        environment=env, user_groups=set(members_list), session=session
                    )
                except Exception as e:
                    LOG.error(e, exc_info=True)
                    raise e
            else:
                LOG.info(f"Skipping Environment: {env.name} ({env.id})")

        ### Sync Query Engines ###

        LOG.info("Syncing Query Engines...")
        query_engine_list = get_all_query_engines(session=session)

        for query_engine in query_engine_list:
            feature_params = query_engine.feature_params or {}

            # Enable or disable the sync
            enable_ad_sync = feature_params.get("enable_ad_sync", False)

            # Controls whether global groups are added to the query engine
            sync_global_groups = feature_params.get("sync_global_groups", False)

            # Comma-separated list of groups to sync to the query engine
            access_control_groups = [
                group
                for group in feature_params.get("access_control_groups", "").split(",")
                if group
            ]

            if enable_ad_sync:
                try:
                    LOG.info(
                        f"Syncing Query Engine: {query_engine.name} ({query_engine.id})"
                    )
                    LOG.debug(f"Feature Params: {query_engine.feature_params}")
                    LOG.info(f"Access control groups: {access_control_groups}")

                    members_list = []

                    if sync_global_groups:
                        members_list.extend(global_groups_members)

                    members_list.extend(
                        get_groups_members_list(args, access_control_groups, conn)
                    )

                    update_user_query_engines_with_groups(
                        query_engine=query_engine,
                        user_groups=set(members_list),
                        session=session,
                    )
                except Exception as e:
                    LOG.error(e, exc_info=True)
                    raise e

            else:
                LOG.info(
                    f"Skipping Query Engine: {query_engine.name} ({query_engine.id})"
                )


def get_groups_members_list(args, groups, conn):
    groups_members = []
    for security_group in groups:
        group_info = ad_query_group_existence(args, conn, security_group)
        if group_info:
            membership = ad_query_group_membership(args, conn, security_group)
            groups_members.extend(membership[1])
            LOG.info(f"Found {len(membership[1])} members for {security_group}")
        else:
            LOG.warning(f'Group "{security_group}" does not exist')
    return groups_members
