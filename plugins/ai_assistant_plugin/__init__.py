from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant
from ai_assistant_plugin.azure_openai_assistant import AzureOpenAIAssistant

ALL_PLUGIN_AI_ASSISTANTS = [OpenAIAssistant(), AzureOpenAIAssistant()]

# Example to add openai assistant
#
# from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant
#
# ALL_PLUGIN_AI_ASSISTANTS = [OpenAIAssistant()]
