import tiktoken

from lib.logger import get_logger
from ai_assistant_plugin.eg_openai_assistant import EgOpenAIAssistant

LOG = get_logger(__file__)


AZURE_OPENAI_MODEL_CONTEXT_WINDOW_SIZE = {
    "gpt-35-turbo": 4097,
    "gpt-35-turbo-16k": 16385,
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
}
DEFAULT_MODEL_NAME = "gpt-35-turbo"

# Mapping from Azure model names to OpenAI model names
# If the model name is not in this mapping, it's assumed to be the same between the two
# See below
AZURE_MODEL_TO_OPENAI_MODEL = {
    "gpt-35-turbo": "gpt-3.5-turbo",
    "gpt-35-turbo-16k": "gpt-3.5-turbo-16k",
}


class AzureOpenAIAssistant(EgOpenAIAssistant):
    """
    EG-specific variation that works with the GenAI Proxy's Azure OpenAI API. This
    is only needed due to an issue with the version of tiktoken that Langchain uses.
    See below for more details.

    The GenAI Proxy has a different URL path but otherwise the same API as OpenAI, so
    we don't need to use AzureOpenAI from the Langchain SDK.
    (https://python.langchain.com/docs/integrations/llms/azure_openai)

    To use it, please set the following environment variables:
        OPENAI_API_KEY: OpenAI API key
        OPENAI_API_BASE: https://generative-ai-proxy-preprod.rcp.us-east-1.data.test.exp-aws.net/v1/proxy/azure-openai
    """

    @property
    def name(self) -> str:
        return "azure_openai"

    def _get_context_length_by_model(self, model_name: str) -> int:
        return (
            AZURE_OPENAI_MODEL_CONTEXT_WINDOW_SIZE.get(model_name)
            or AZURE_OPENAI_MODEL_CONTEXT_WINDOW_SIZE[DEFAULT_MODEL_NAME]
        )

    def _get_token_count(self, ai_command: str, prompt: str) -> int:
        azure_model_name = self._get_llm_config(ai_command)["model_name"]

        # Hack: The version of Langchain has an old version of tiktoken that
        # doesn't recognize the new Azure models. We can't upgrade Langchain without
        # larger changes to the codebase, so we're stuck with this for now.
        #
        # Here we just convert Azure model names to OpenAI model names.
        # This is a hack and should be removed when Langchain is upgraded.
        #
        # Note: the underline models are the same, so it's just a mapping issue.
        model_name = (
            AZURE_MODEL_TO_OPENAI_MODEL.get(azure_model_name) or azure_model_name
        )
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(prompt))
