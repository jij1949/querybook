import os
from env import get_env_config

from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant

if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = get_env_config("OPENAI_API_KEY")
if "OPENAI_API_BASE" not in os.environ:
    os.environ["OPENAI_API_BASE"] = get_env_config("OPENAI_API_BASE")

ALL_PLUGIN_AI_ASSISTANTS = [OpenAIAssistant()]

# Example to add openai assistant
#
# from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant
#
# ALL_PLUGIN_AI_ASSISTANTS = [OpenAIAssistant()]
