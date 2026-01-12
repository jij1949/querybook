import requests
from env import QuerybookSettings
from lib.notify.base_notifier import BaseNotifier
from lib.logger import get_logger

LOG = get_logger(__file__)


class SlackNotifier(BaseNotifier):
    def __init__(self, token=None):
        self.token = (
            token if token is not None else QuerybookSettings.QUERYBOOK_SLACK_TOKEN
        )

    @property
    def notifier_name(self):
        return "slack"

    @property
    def notifier_help(self) -> str:
        return "Recipient could be a Querybook user or a Slack user(starts with @) or channel(starts with #)"

    @property
    def notifier_format(self):
        return "plaintext"

    def notify_recipients(self, recipients, message):
        """Send message to a list of slack users or channels.

        Args:
            recipients (list[str]): list of Slack user(starts with @) or channel(starts with #) names
            message (str): messge to be sent
        """
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": "Bearer {}".format(self.token)}
        for recipient in recipients:
            data = {"text": message, "channel": recipient}
            try:
                response = requests.post(url, json=data, headers=headers, timeout=30)
                response_json = response.json()
                
                if response.status_code == 200 and response_json.get("ok"):
                    LOG.debug(f"Slack notification sent successfully to {recipient}")
                else:
                    error_msg = response_json.get("error", "Unknown error")
                    LOG.error(f"Slack API error sending to {recipient}: {error_msg} (HTTP {response.status_code})")
                    raise Exception(f"Slack API error: {error_msg}")
            except Exception as e:
                LOG.error(f"Error sending Slack notification to {recipient}: {str(e)}")
                raise

    def notify(self, user, message):
        self.notify_recipients(recipients=[f"@{user.username}"], message=message)
