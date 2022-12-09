from lib.notify.notifier.email_notifier import EmailNotifier
from notifier_plugin.eg_slack.eg_slack_notifier import EGSlackNotifier


ALL_PLUGIN_NOTIFIERS = [EmailNotifier(), EGSlackNotifier()]
