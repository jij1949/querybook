import os
import httpx

from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant


from lib.logger import get_logger

LOG = get_logger(__file__)

REQUESTS_CA_BUNDLE = os.environ.get("REQUESTS_CA_BUNDLE")


class EgOpenAIAssistant(OpenAIAssistant):
    """Wrapper"""

    @property
    def name(self) -> str:
        return "eg_openai"

    def _get_default_llm_config(self):
        # Cache the default config on first call
        if not hasattr(self, "_default_config"):
            self._default_config = super()._get_default_llm_config()
            self._default_config["http_client"] = httpx.Client(
                verify=REQUESTS_CA_BUNDLE
            )

        return self._default_config
