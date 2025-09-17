import ldap3
from ldap3 import Server, Connection
import re
import time

from app.db import DBSession, with_session
from app.flask_app import celery
from const.user import UserGroup
from const.user_roles import UserRoleType
from lib.logger import get_logger
from logic.user import (
    create_or_update_user_group,
    create_user_role,
    delete_user_role,
    get_all_admin_user_roles,
    get_user_by_name,
)
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
from models.user import User

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


def ad_query_group(args, conn, ad_group):
    """
    :param conn: ldap connection object
    :param ad_group: string of security group
    :return: if group does not exists, will return None else would return the searched group
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

        if success and len(conn.entries) > 0:
            return conn.entries[0]
    except Exception as e:
        LOG.warning(
            f"Unable to query AD for existence of group {ad_group}: {e.message}"
        )

    return None


def ad_query_group_membership(args, conn, ad_group, level=1, visited_groups=[], skip_service_accounts=False):
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
                        # If the entry is a group, recursively query its members unless unfurlGroups is False
                        if (
                            entry["attributes"]["sAMAccountType"] == SAM_GROUP_OBJECT
                            and args.unfurlGroups == True
                        ):
                            # Check if we've already queried this group
                            if (
                                entry["attributes"]["sAMAccountName"]
                                not in visited_groups
                            ):
                                if args.tracead:
                                    LOG.debug(
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
                                    LOG.debug(
                                        f"Already queried group {entry['attributes']['sAMAccountName']}, skipping."
                                    )
                        # Filter out service accounts (s-*)
                        elif entry["attributes"]["sAMAccountName"] is None or (
                            entry["attributes"]["sAMAccountName"].startswith("s-") and skip_service_accounts
                        ):
                            LOG.debug(
                                f"Warning - user {entry['attributes']['sAMAccountName']} is a service account, skipping."
                            )
                        else:
                            if args.tracead:
                                LOG.debug(
                                    f"Found user {entry['attributes']['sAMAccountName']}"
                                )
                            ad_group_members.append(
                                entry["attributes"]["sAMAccountName"]
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

    # Unfurling groups might result in duplicates, so we need to dedupe
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

    LOG.debug(f"Total users: {len(user_groups)}")
    LOG.debug(f"Users to add: {len(users_to_add)}")
    LOG.debug(f"Users to remove: {len(users_to_remove)}")

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

    LOG.debug(f"Total users: {len(user_groups)}")
    LOG.debug(f"Users to add: {len(users_to_add)}")
    LOG.debug(f"Users to remove: {len(users_to_remove)}")

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


def get_groups_members_list(args, groups, conn):
    groups_members = []
    for security_group in groups:
        group_info = ad_query_group(args, conn, security_group)
        if group_info:
            membership = ad_query_group_membership(args, conn, security_group)
            groups_members.extend(membership[1])
            LOG.debug(f"Found {len(membership[1])} members for {security_group}")
        else:
            LOG.warning(f'Group "{security_group}" does not exist')
    return groups_members


#####################################
# ------- Tasks ------- #
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
        args.unfurlGroups = True

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

            LOG.debug(f"Access control groups: {access_control_groups}")

            if enable_ad_sync:
                try:
                    LOG.debug(f"Syncing Environment: {env.name} ({env.id})")
                    LOG.debug(f"Feature Params: {env.feature_params}")
                    LOG.debug(f"Access control groups: {access_control_groups}")

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
                LOG.debug(f"Skipping Environment: {env.name} ({env.id})")

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
                    LOG.debug(
                        f"Syncing Query Engine: {query_engine.name} ({query_engine.id})"
                    )
                    LOG.debug(f"Feature Params: {query_engine.feature_params}")
                    LOG.debug(f"Access control groups: {access_control_groups}")

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
                LOG.debug(
                    f"Skipping Query Engine: {query_engine.name} ({query_engine.id})"
                )


@celery.task(bind=True)
@with_task_logging()
def sync_ldap_groups(self):
    """
    This task refreshes the group membership of all current groups in Querybook.
    All rows in the `user` table where `is_group` is True are synced
    Group membership is retrieved from LDAP and matched against the `user` table.
    No new users are created, only existing users are matched to existing groups.

    During the sync, the following happens:
    - If the group exists in LDAP, it is updated
    - All users in the group are added as members of the group
    - If the group does not exist in LDAP, it is ignored (TODO: delete the group?)
    """
    LOG.info("Starting LDAP Sync Groups Task...")

    args = Object()
    args.dryrun = False
    args.tracead = False

    # Don't unfurl nested groups, just return the group name(s)
    args.unfurlGroups = False

    ad_connection = ad_connect(args, ad_server, ad_bind_user, ad_bind_password)

    with DBSession() as session:
        # Get all groups in Querybook
        groups = session.query(User).filter(User.is_group == True).all()

        for group in groups:
            sync_ldap_group(args, group, ad_connection, session=session)

        session.commit()


def sync_ldap_group(args, group, ad_connection, session=None):
    """
    Syncs a single group from LDAP.
    """
    LOG.info(f"Syncing group: {group.username} ({group.id})")
    if not group or not group.is_group:
        LOG.error(f"Invalid group: {group}")
        return

    ad_group = ad_query_group(args, ad_connection, group.username)

    if not ad_group:
        LOG.warning(f'Group "{group.username}" does not exist')
        return

    descriptions = ad_group.entry_attributes_as_dict.get("description", "")
    description = descriptions[0] if isinstance(descriptions, list) else descriptions

    # Get group members
    group_members = get_groups_members_list(args, [group.username], ad_connection)

    LOG.debug(f"Group {group.username} has {len(group_members)} members")

    # Update group with updated members
    create_or_update_user_group(
        UserGroup(
            name=group.username,
            display_name=group.fullname,
            description=description,
            email=group.email,
            members=group_members,
        ),
        session=session,
    )


@celery.task(bind=True)
@with_task_logging()
def sync_querybook_admins(self):
    """
    This task syncs Querybook admins from LDAP.

    During the sync, the following happens:
    - All users in the `querybook-admins` group in LDAP are added as admins in Querybook
    - Users who are currently admins in Querybook but are not in the `querybook-admins` group are removed as admins

    Uses the environment variable `LDAP_QUERYBOOK_ADMINS_GROUP` to determine the group name.
    """
    LOG.info("Starting LDAP Sync Querybook Admins Task...")

    args = Object()
    args.dryrun = False
    args.tracead = False

    admin_group = QuerybookSettings.LDAP_QUERYBOOK_ADMINS_GROUP
    if not admin_group:
        LOG.error("LDAP_QUERYBOOK_ADMINS_GROUP is not set")
        return

    LOG.debug(f"Querying group {admin_group} for Querybook admins")

    ad_connection = ad_connect(args, ad_server, ad_bind_user, ad_bind_password)

    with DBSession() as session:

        ad_group = ad_query_group(args, ad_connection, admin_group)

        if not ad_group:
            LOG.warning(f'Group "{admin_group}" does not exist')
            return

        # Get group members
        group_members = get_groups_members_list(args, [admin_group], ad_connection)

        LOG.debug(f"Group {admin_group} has {len(group_members)} members")
        LOG.debug(f"Querybook admins: {group_members}")

        # Find matching users in Querybook (if they exist)
        matching_users = (
            session.query(User).filter(User.username.in_(group_members)).all()
        )

        LOG.debug(f"Querybook admins: {matching_users}")

        # Get all existing admins
        existing_admins = get_all_admin_user_roles(session=session)

        LOG.debug(f"Existing admins: {existing_admins}")

        # Iterate through matching users and add them as admins
        for user in matching_users:
            # If existing admin
            if user.id in [admin.uid for admin in existing_admins]:
                LOG.debug(f"{user.username} is already an admin")
                existing_admins = [
                    admin for admin in existing_admins if admin.uid != user.id
                ]
            else:
                # Add user as admin
                LOG.debug(f"Adding {user.username} as Querybook admin")

                # Add record in user_role table with role="ADMIN"
                create_user_role(
                    user.id, UserRoleType.ADMIN, commit=False, session=session
                )

        # Remove users who are no longer admins
        for user_role in existing_admins:
            LOG.debug(f"Removing {user_role.uid} from Querybook admin role")
            delete_user_role(user_role.id, commit=False, session=session)

        session.commit()
