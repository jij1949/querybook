from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant
from ai_assistant_plugin.azure_openai_assistant import AzureOpenAIAssistant
from ai_assistant_plugin.ollama_assistant import OllamaAIAssistant

ALL_PLUGIN_AI_ASSISTANTS = [
    OpenAIAssistant(),
    AzureOpenAIAssistant(),
    OllamaAIAssistant(),
]

# Example to add openai assistant
#
# from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant
#
# ALL_PLUGIN_AI_ASSISTANTS = [OpenAIAssistant()]
