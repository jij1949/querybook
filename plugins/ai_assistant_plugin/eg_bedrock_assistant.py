import os
from typing import Any, List, Optional

import httpx
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from lib.ai_assistant.base_ai_assistant import BaseAIAssistant
from lib.logger import get_logger

LOG = get_logger(__file__)

BEDROCK_ENDPOINT_URL = os.environ.get("BEDROCK_ENDPOINT_URL")
BEDROCK_API_KEY = os.environ.get("OPENAI_API_KEY")  # same GenAI proxy token
REQUESTS_CA_BUNDLE = os.environ.get("REQUESTS_CA_BUNDLE")

BEDROCK_MODEL_CONTEXT_WINDOW_SIZE = {
    "us.anthropic.claude-sonnet-4-6": 200000,
}
DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"

# Approximate tokens using character count (~4 chars per token)
_CHARS_PER_TOKEN = 4


def _langchain_messages_to_bedrock(messages: List[BaseMessage]):
    """Convert LangChain messages to Bedrock Anthropic Messages API format.

    Returns (system_prompt, messages_list) where system_prompt may be None.
    """
    system_prompt = None
    bedrock_messages = []

    for msg in messages:
        if msg.type == "system":
            system_prompt = msg.content
        elif msg.type == "human":
            bedrock_messages.append(
                {
                    "role": "user",
                    "content": [{"type": "text", "text": msg.content}]
                    if isinstance(msg.content, str)
                    else msg.content,
                }
            )
        elif msg.type == "ai":
            bedrock_messages.append(
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": msg.content}]
                    if isinstance(msg.content, str)
                    else msg.content,
                }
            )

    return system_prompt, bedrock_messages


class BedrockProxyChat(BaseChatModel):
    """Thin LangChain chat model that calls Bedrock via EG GenAI Proxy over httpx."""

    model_id: str = DEFAULT_MODEL_ID
    endpoint_url: str = ""
    api_key: str = ""
    temperature: float = 1.0
    max_tokens: int = 4096
    ca_bundle: Optional[str] = None

    @property
    def _llm_type(self) -> str:
        return "eg_bedrock_proxy"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        system_prompt, bedrock_messages = _langchain_messages_to_bedrock(messages)

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "messages": bedrock_messages,
            "temperature": self.temperature,
        }
        if system_prompt:
            body["system"] = system_prompt
        if stop:
            body["stop_sequences"] = stop

        url = f"{self.endpoint_url}/model/{self.model_id}/invoke"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "x-client-app": "querybook",
        }

        LOG.info(f"Bedrock proxy request: {url} model={self.model_id}")
        response = httpx.post(
            url,
            headers=headers,
            json=body,
            verify=self.ca_bundle or True,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()

        text = ""
        for block in result.get("content", []):
            if block.get("type") == "text":
                text += block["text"]

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content=text),
                )
            ],
            llm_output={
                "model": result.get("model"),
                "usage": result.get("usage"),
            },
        )


class EgBedrockAIAssistant(BaseAIAssistant):
    """AWS Bedrock AI assistant routed through the EG GenAI Proxy via httpx.

    Environment variables:
        BEDROCK_ENDPOINT_URL: GenAI proxy Bedrock endpoint base URL
        OPENAI_API_KEY: Bearer token for GenAI proxy auth (shared with OpenAI proxy)
        REQUESTS_CA_BUNDLE: Path to CA bundle for SSL verification

    Configuration options (set via model_args in AI_ASSISTANT_CONFIG):
        model_id (str): Bedrock model ID. Defaults to claude-sonnet-4-6.
        model_kwargs (dict): Model parameters (e.g. temperature).
        streaming (bool): Whether to stream responses (not yet supported).
    """

    @property
    def name(self) -> str:
        return "eg_bedrock"

    def _get_context_length_by_model(self, model_name: str) -> int:
        return BEDROCK_MODEL_CONTEXT_WINDOW_SIZE.get(
            model_name, BEDROCK_MODEL_CONTEXT_WINDOW_SIZE[DEFAULT_MODEL_ID]
        )

    def _get_default_llm_config(self):
        default_config = super()._get_default_llm_config()
        if not default_config.get("model_id"):
            default_config["model_id"] = DEFAULT_MODEL_ID
        return default_config

    def _get_usable_token_count(self, ai_command: str) -> int:
        """Override base class which hardcodes 'model_name' key — Bedrock uses 'model_id'."""
        ai_command_config = self._config.get(ai_command, {})
        default_config = self._config.get("default", {})
        model_id = self._get_llm_config(ai_command).get(
            "model_id", DEFAULT_MODEL_ID
        )
        max_context_length = self._get_context_length_by_model(model_id)
        reserved_tokens = ai_command_config.get(
            "reserved_tokens"
        ) or default_config.get("reserved_tokens", 0)
        return max_context_length - reserved_tokens

    def _get_token_count(self, ai_command: str, prompt: str) -> int:
        return max(1, len(prompt) // _CHARS_PER_TOKEN)

    def _get_llm(self, ai_command: str, prompt_length: int):
        config = self._get_llm_config(ai_command)
        model_id = config.get("model_id", DEFAULT_MODEL_ID)
        model_kwargs = config.get("model_kwargs", {})

        return BedrockProxyChat(
            model_id=model_id,
            endpoint_url=BEDROCK_ENDPOINT_URL,
            api_key=BEDROCK_API_KEY,
            temperature=model_kwargs.get("temperature", 1.0),
            max_tokens=model_kwargs.get("max_tokens", 4096),
            ca_bundle=REQUESTS_CA_BUNDLE,
        )
