from ai_assistant_plugin.eg_openai_assistant import EgOpenAIAssistant
from ai_assistant_plugin.azure_openai_assistant import AzureOpenAIAssistant
from ai_assistant_plugin.ollama_assistant import OllamaAIAssistant
from ai_assistant_plugin.eg_bedrock_assistant import EgBedrockAIAssistant

ALL_PLUGIN_AI_ASSISTANTS = [
    EgOpenAIAssistant(),
    AzureOpenAIAssistant(),
    OllamaAIAssistant(),
    EgBedrockAIAssistant(),
]

# Example to add openai assistant
#
# from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant
#
# ALL_PLUGIN_AI_ASSISTANTS = [OpenAIAssistant()]
