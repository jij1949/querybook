import ldap3
from ldap3 import Server, Connection
import re
import time

from app.db import DBSession
from app.flask_app import celery
from lib.logger import get_logger
from logic.user import get_user_by_name
from logic.schedule import with_task_logging
from env import QuerybookSettings
from logic.admin import (
    add_user_to_query_engine,
    remove_user_to_query_engine,
    get_all_query_engines,
)
from logic.environment import (
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


# Returns a list of groups that the user is a member of.
# Only the sAMAcountName is returned for each group.
# This takes a lazy approach by parsing it out of the DN. If this causes issues,
# it can be modified to use the LDAP search function to get the group name from the DN (slower)
#
# Only groups matching a specific OU are returned.
# If needed, this can be modified to include additional OUs
#
def ad_query_user_membership(conn, sAMAccountName):
    """
    :param conn: ldap connection object
    :param sAMAccountName: string of user
    :return: returns a set of the group list
    """
    security_group_regex = re.compile(
        rf"^CN=([^,]+),OU=Security Groups,{bind_domain}$", re.IGNORECASE
    )
    search_base = "OU=All Users,{0}".format(bind_domain)
    # filter disabled users, with UserAccountControl
    user_search_filter = "(sAMAccountName={0})".format(sAMAccountName)

    try:
        LOG.info(f"Querying AD membership of user {sAMAccountName}... ")

        start = time.time()

        # pagination with generator to overcome 1000 search result limit by AD
        entries = conn.extend.standard.paged_search(
            search_base=search_base,
            search_filter=user_search_filter,
            attributes=[ldap3.ALL_ATTRIBUTES, ldap3.ALL_OPERATIONAL_ATTRIBUTES],
            search_scope=ldap3.SUBTREE,
            size_limit=10,
            generator=False,
        )

        if entries is None:
            raise Exception(
                f"Unable to query AD for membership of {sAMAccountName}, skipping."
            )

        # Check if more than 1 entry was returned (should not happen)
        if len(entries) > 1:
            raise Exception(
                f"More than 1 entry returned for user {sAMAccountName}, skipping."
            )

        # Map the DN to the Group name
        memberOf = []
        for group in entries[0]["attributes"]["memberOf"]:
            # Filter out any groups that don't match the OU
            match = security_group_regex.search(group)
            if match:
                # Return just the sAMAcountName for each group
                memberOf.append(match.group(1))

        end = time.time()
        LOG.debug(
            f"Examined user's AD membership, took {round(end - start, 1)} seconds"
        )

    except Exception as e:
        LOG.error(
            f"Unable to query AD for membership of {sAMAccountName}: {e}",
            exc_info=True,
        )
        raise e

    return list(set(memberOf))


class Object(object):
    pass


#####################################
# ------- Running task ------- #
#####################################

#
# This task syncs a single user's permissions via LDAP
# This handles environments and query engines
#
# Compared to sync_ldap_task, which syncs the full list of users for each environment/query engine,
# this task only syncs a single user by matching their group membership to the access control groups
# for each environment/query engine
#
# Caveats:
# - This task only syncs environments and query engines that have `enable_ad_sync` set to True
# - This task only syncs environments and query engines that have access control groups
#
@celery.task(bind=True)
@with_task_logging()
def sync_ldap_user_task(self, username):
    """
    :return: returns None, runs the task of syncing permissions via LDAP
    """
    LOG.info("Starting LDAP Sync User Task...")

    with DBSession() as session:
        args = Object()
        args.dryrun = False
        args.tracead = False

        # Get user record
        user = get_user_by_name(username, session=session)

        if not user:
            LOG.error(f"User {username} not found")
            return

        conn = ad_connect(args, ad_server, ad_bind_user, ad_bind_password)

        ### Get User Information ###
        LOG.info("Getting User Information...")
        membership = ad_query_user_membership(conn, username)
        # LOG.debug(f"User Membership: {membership}")

        ### Sync Environments ###

        LOG.info("Syncing Environments...")
        env_list = get_all_environment(False, session=session)

        for env in env_list:
            feature_params = env.feature_params or {}

            # Enable or disable the sync
            enable_ad_sync = feature_params.get("enable_ad_sync", False)

            # Comma-separated list of groups to sync to the environment
            access_control_groups = [
                group
                for group in feature_params.get("access_control_groups", "").split(",")
                if group
            ]

            if enable_ad_sync and access_control_groups:
                try:
                    LOG.info(f"Syncing Environment: {env.name} ({env.id})")
                    LOG.debug(f"Feature Params: {env.feature_params}")
                    LOG.info(f"Access control groups: {access_control_groups}")

                    # Test if any of the user's groups are in the access control groups
                    # Add/remove accordingly
                    if any(map(lambda x: x in access_control_groups, membership)):
                        LOG.debug(f"Adding {username} to {env.name} ({env.id})")
                        add_user_to_environment(
                            user.id, env.id, commit=False, session=session
                        )
                    else:
                        LOG.debug(f"Removing {username} from {env.name} ({env.id})")
                        remove_user_to_environment(
                            user.id, env.id, commit=False, session=session
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

            # Comma-separated list of groups to sync to the query engine
            access_control_groups = [
                group
                for group in feature_params.get("access_control_groups", "").split(",")
                if group
            ]

            if enable_ad_sync and access_control_groups:
                try:
                    LOG.info(
                        f"Syncing Query Engine: {query_engine.name} ({query_engine.id})"
                    )
                    LOG.debug(f"Feature Params: {query_engine.feature_params}")
                    LOG.info(f"Access control groups: {access_control_groups}")

                    # Test if any of the user's groups are in the access control groups
                    # Add/remove accordingly
                    if any(map(lambda x: x in access_control_groups, membership)):
                        LOG.debug(
                            f"Adding {username} to {query_engine.name} ({query_engine.id})"
                        )
                        add_user_to_query_engine(
                            user.id, query_engine.id, commit=False, session=session
                        )
                    else:
                        LOG.debug(
                            f"Removing {username} from {query_engine.name} ({query_engine.id})"
                        )
                        remove_user_to_query_engine(
                            user.id, query_engine.id, commit=False, session=session
                        )
                except Exception as e:
                    LOG.error(e, exc_info=True)
                    raise e

            else:
                LOG.info(
                    f"Skipping Query Engine: {query_engine.name} ({query_engine.id})"
                )

        session.commit()
