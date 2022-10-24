import flask_login

from app.auth.utils import AuthenticationError, abort_unauthorized, AuthUser
from app.auth.oauth_auth import OAUTH_CALLBACK_PATH
from app.auth.okta_auth import OktaLoginManager
from app.db import DBSession
from env import QuerybookSettings
from flask import request, session as flask_session, redirect
from lib.logger import get_logger
from lib.utils.decorators import in_mem_memoized

LOG = get_logger(__file__)

#
# Expedia-customized version of the OktaLoginManager
#
class EgOktaLoginManager(OktaLoginManager):

    @property
    @in_mem_memoized()
    def oauth_config(self):
        authorization_url, token_url, profile_url = self.get_okta_urls()

        return {
            "callback_url": "{}{}".format(
                QuerybookSettings.PUBLIC_URL, OAUTH_CALLBACK_PATH
            ),
            "client_id": QuerybookSettings.OAUTH_CLIENT_ID,
            "client_secret": QuerybookSettings.OAUTH_CLIENT_SECRET,
            "authorization_url": authorization_url,
            "token_url": token_url,
            "profile_url": profile_url,
            "scope": ["openid", "email", "profile"],
            "cookies": {"secure": True, "samesite": "None"},
        }

    # Override this method to customize the behavior of the login process
    def oauth_callback(self):
        LOG.debug("Handling Oauth callback...")

        if request.args.get("error"):
            error_message = request.args.get("error")

            # If the user doesn't have Okta access, redirect to a page that
            # explains how to get access
            if error_message == "access_denied":
                return redirect(f"/access_denied?error={error_message}")
            else:
                return f"<h1>Error: {request.args.get('error')}</h1>"

        code = request.args.get("code")
        try:
            access_token = self._fetch_access_token(code)
            username, email, fullname = self._get_user_profile(access_token)
            with DBSession() as session:
                flask_login.login_user(
                    AuthUser(
                        self.login_user(username, email, fullname, session=session)
                    )
                )
        except AuthenticationError as e:
            LOG.error("Failed authenticate oauth user", e)
            abort_unauthorized()

        next_url = QuerybookSettings.PUBLIC_URL
        if "next" in flask_session:
            next_url = flask_session["next"]
            del flask_session["next"]

        return redirect(next_url)

    def _parse_user_profile(self, resp):
        user = resp.json()
        return user["preferred_username"], user["email"], user["name"]


login_manager = EgOktaLoginManager()

ignore_paths = [OAUTH_CALLBACK_PATH, "/access_denied"]


def init_app(app):
    login_manager.init_app(app)


def login(request):
    return login_manager.login(request)


# Required for local development
def oauth_authorization_url():
    oauth_config = login_manager.oauth_config
    return f"{oauth_config['authorization_url']}?response_type=code&client_id={oauth_config['client_id']}&redirect_uri={oauth_config['callback_url']}&scope={' '.join(oauth_config['scope'])}&state=test"
