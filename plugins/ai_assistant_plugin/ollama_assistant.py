import os
import requests

from const.ai_assistant import AICommandType
from lib.ai_assistant.ai_socket import with_ai_socket
from lib.ai_assistant.base_ai_assistant import BaseAIAssistant
from lib.ai_assistant.prompts.sql_title_prompt import SQL_TITLE_PROMPT
from lib.ai_assistant.prompts.text_to_sql_prompt import TEXT_TO_SQL_PROMPT
from lib.ai_assistant.tools.table_schema import get_slimmed_table_schemas
from lib.logger import get_logger
import tiktoken

from langchain_community.llms import Ollama

from app.db import with_session


LOG = get_logger(__file__)


MODEL_CONTEXT_WINDOW_SIZE = {
    "tinydolphin:v2.8": 4097,
}

DEFAULT_MODEL_NAME = "tinydolphin:v2.8"


class OllamaAIAssistant(BaseAIAssistant):
    """
    Ollama AI Assistant

    To use it, please set the following environment variables:
        OLLAMA_BASE_URL: Ollama base url
    """

    @property
    def name(self) -> str:
        return "ollama"

    def _get_context_length_by_model(self, model_name: str) -> int:
        return 4097

    def _get_default_llm_config(self):
        default_config = super()._get_default_llm_config()
        if not default_config.get("model_name"):
            default_config["model_name"] = DEFAULT_MODEL_NAME

        return default_config

    def _get_token_count(self, ai_command: str, prompt: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(prompt))

    def _get_llm(self, ai_command: str, prompt_length: int, callback_handler=None):
        config = self._get_llm_config(ai_command)

        model = config.get("model_name")
        base_url = os.environ.get("OLLAMA_BASE_URL") or config.get("base_url")
        combined_config = {**config, "base_url": base_url, "model": model}
        combined_config.pop("streaming", None)
        combined_config.pop("model_name", None)

        LOG.debug(f"**** Using Ollama config: {combined_config}")
        ollama = Ollama(**combined_config)

        return ollama

    def _get_error_msg(self, error) -> str:
        LOG.debug(f"** Ollama error: {error}")
        # if error message contains model 'tinydolphin:v2.8' not found, try pulling it first"
        if "model" in str(error) and "not found" in str(error):
            # parse model name out of error message

            model_name = str(error).split("'")[1]
            base_url = os.environ.get("OLLAMA_BASE_URL")

            # Attempt to pull model via API
            # curl http://localhost:11434/api/pull -d '{
            #   "name": "<model_name>",
            # }'

            response = requests.post(
                f"{base_url}/api/pull",
                json={
                    "name": model_name,
                },
            )

            LOG.debug(f"** Ollama response: {response}")

            return "Model not found, try again later."

        else:
            return str(error.args[0])

    def _get_sql_title_prompt(self, query):
        prompt = SQL_TITLE_PROMPT.format(query=query)
        LOG.debug(f"PROMPT: {prompt}")
        return prompt

    def _get_text_to_sql_prompt(self, dialect, question, table_schemas, original_query):
        context_limit = self._get_usable_token_count(AICommandType.TEXT_TO_SQL.value)
        prompt = TEXT_TO_SQL_PROMPT.format(
            dialect=dialect,
            question=question,
            table_schemas=table_schemas,
            original_query=original_query,
        )
        token_count = self._get_token_count(AICommandType.TEXT_TO_SQL.value, prompt)

        if token_count > context_limit:
            LOG.debug(f"!! PROMPT LENGTH: {token_count} / {context_limit}")
            LOG.debug(f"PROMPT: {prompt}")
            LOG.debug("!! PROMPT TOO LONG, USING SLIMMED TABLE SCHEMAS")
            # if the prompt is too long, use slimmed table schemas
            prompt = TEXT_TO_SQL_PROMPT.format(
                dialect=dialect,
                question=question,
                table_schemas=get_slimmed_table_schemas(table_schemas),
                original_query=original_query,
            )
            token_count = self._get_token_count(AICommandType.TEXT_TO_SQL.value, prompt)

        LOG.debug(f"PROMPT: {prompt}")
        LOG.debug(f"!! PROMPT LENGTH: {token_count} / {context_limit}")

        # TODO: need a better way to handle it if the prompt is still too long
        return prompt

    @with_session
    @with_ai_socket(command_type=AICommandType.TEXT_TO_SQL)
    def generate_sql_query(
        self,
        query_engine_id: int,
        tables: list[str],
        question: str,
        original_query: str = None,
        socket=None,
        session=None,
    ):
        response = super().generate_sql_query(
            query_engine_id,
            tables,
            question,
            original_query=original_query,
            socket=socket,
            session=session,
        )
        LOG.debug("** Ollama response: {response}")
        return response
