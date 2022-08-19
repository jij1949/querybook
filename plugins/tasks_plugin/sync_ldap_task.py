import ldap3
from ldap3 import Server, Connection
import os
import re
import sys
import time

from app.db import DBSession, with_session
from app.flask_app import celery
from lib.logger import get_logger
from logic.user import get_user_by_name
from logic.schedule import with_task_logging
from env import QuerybookSettings
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
    '''
    :param ad_server: LDAP server connection
    :param ad_bind_user: Ldap service account users
    :param ad_bind_password: Password to the ldap users
    :return: return the ldap connection
    '''

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

    LOG.info(f"AD server: {ad_server}, bind user: {conn.extend.standard.who_am_i()}")

    return conn


def ad_query_group_existence(args, conn, ad_group):
    '''
    :param conn: ldap connection object
    :param ad_group: string of security group
    :return: if group does not exists, will return false else would return the searched group
    '''
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
            f"Unable to query AD for existence of group {ad_group}: {e.message}")
        success = False

    return success


def ad_query_group_membership(args, conn, ad_group, level=1, visited_groups=[]):
    '''
    :param conn: ldap connection object
    :param ad_group: string of security group
    :param level: interger
    :param visited_groups: list of visited groups
    :return: returns a tuple of success bool and a set of the member list
    '''
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
                                        f"Already queried group {entry['attributes']['sAMAccountName']}, skipping.")
                        # Filter users with no email or
                        #  is a Service account
                        elif (
                            entry["attributes"]["sAMAccountName"] is not None
                            and (
                                not entry["attributes"]["sAMAccountName"].startswith(
                                    "s-")
                            )
                        ):
                            if args.tracead:
                                LOG.info(
                                    f"Found user {entry['attributes']['sAMAccountName']}")
                            ad_group_members.append(
                                entry["attributes"]["sAMAccountName"])
                        else:
                            LOG.warning(
                                f"Warning - user {entry['attributes']['sAMAccountName']} has no email address or service account (not following naming standard)"
                                ", not syncing to querybook"
                            )
                        total_entries += 1
        end = time.time()
        LOG.info(
            f"Examined {total_entries} entries, took {round(end - start, 1)} seconds"
        )
        success = True
    except Exception as e:
        LOG.error(
            f"Unable to query AD for members of {ad_group}: {e.message}", exc_info=True)
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
    '''
    :param environment_id: int id of the querybook  env
    :param user_groups: a set of users that will be added to environment
    :param session: session object
    :return: a set of users to add and users to remove from the querybook env
    '''
    # todo: don't hack the limit

    users_in_environment = get_users_in_environment(
        environment_id,
        0,
        1000000,
        session=session
    )
    users_in_environment_set = set(map(
        lambda u: u.username,
        users_in_environment
    ))

    # Returns users to add, users to remove
    return user_groups - users_in_environment_set, users_in_environment_set - user_groups


@with_session
def update_user_environments_with_groups(environment_id, user_groups, session=None):
    '''
    :param environment_id: int id of the querybook env
    :param user_groups: set of users to update to the env
    :param session: session object
    :return: None
    '''
    users_to_add, users_to_remove = get_environment_users_delta(
        environment_id, user_groups, session=session)

    LOG.info(f'Total users: {len(user_groups)}')
    LOG.info(f'Users to add: {len(users_to_add)}')
    LOG.info(f'Users to remove: {len(users_to_remove)}')

    for username in users_to_add:
        user = get_user_by_name(username, session=session)
        if user:
            LOG.debug(f'Adding {username} from {environment_id}')
            add_user_to_environment(
                user.id,
                environment_id,
                commit=False,
                session=session
            )

    for username in users_to_remove:
        user = get_user_by_name(username, session=session)
        if user:
            LOG.debug(f'Removing {username} from {environment_id}')
            remove_user_to_environment(
                user.id, environment_id, commit=False, session=session)
    session.commit()


#####################################
# ------- Running task ------- #
#####################################

@celery.task(bind=True)
@with_task_logging()
def sync_ldap_task(self):
    '''
    :return: returns None , runs the task of grabbing users from each env and syncing them to querybook
    '''
    LOG.info('Syncing LDAP...')
    with DBSession() as session:
        args = Object()
        args.dryrun = False
        args.tracead = False

        env_list = get_all_environment(False, session=session)

        # Creating a dictionary to map each env to a security group format  { <env>: 'qb-env-{{ env }} }
        security_env_list = {env.name: f"qb-env-{env.name}" for env in env_list}

        conn = ad_connect(args, ad_server, ad_bind_user, ad_bind_password)

        # Get global groups members since they should be added to all environments
        LOG.debug(f'Getting global groups members: {global_groups}')
        global_groups_members = get_groups_members_list(args, global_groups, conn)

        for env in env_list:
            try:
                LOG.debug(f'Environment {env}')
                env_security_group = security_env_list[env.name]
                members_list = get_groups_members_list(args, [env_security_group], conn)
                members_list.extend(global_groups_members)

                update_user_environments_with_groups(
                    environment_id=env.id, user_groups=set(members_list), session=session)
            except Exception as e:
                LOG.error(e, exc_info=True)
                raise e


def get_groups_members_list(args, groups, conn):
    groups_members = []
    for security_group in groups:
        group_info = ad_query_group_existence(args, conn, security_group)
        if group_info:
            membership = ad_query_group_membership(args, conn, security_group)
            groups_members.extend(membership[1])
            LOG.debug(f'Found {len(membership[1])} members for {security_group}')
        else:
            LOG.warning(f'Group "{security_group}" does not exist')
    return groups_members
