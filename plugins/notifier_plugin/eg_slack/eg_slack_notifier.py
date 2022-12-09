import requests
from env import QuerybookSettings
from lib.notify.notifier.slack_notifier import SlackNotifier
from lib.logger import get_logger

LOG = get_logger(__file__)

#
# This is a Expedia-specific version of the SlackNotifier.
#
class EGSlackNotifier(SlackNotifier):
    def __init__(self, token=None):
        self.token = (
            token if token is not None else QuerybookSettings.QUERYBOOK_SLACK_TOKEN
        )

    def notify(self, user, message):
        # Vendor accounts don't have a 'v-' prefix in their username,
        # but they do in both their email and Slack username.
        #
        # Check for the 'v-' prefix in the email address, and if it's
        # there, use it in the Slack username.
        slackUsername = (
            f"@v-{user.username}"
            if user.email.startswith("v-")
            else f"@{user.username}"
        )

        self.notify_recipients(recipients=[slackUsername], message=message)
