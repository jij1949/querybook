from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant
from ai_assistant_plugin.openai_nostream_assistant.openai_nostream_assistant import (
    OpenAINoStreamAssistant,
)

ALL_PLUGIN_AI_ASSISTANTS = [OpenAIAssistant(), OpenAINoStreamAssistant()]

# Example to add openai assistant
#
# from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant
#
# ALL_PLUGIN_AI_ASSISTANTS = [OpenAIAssistant()]
