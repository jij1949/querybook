from lib.ai_assistant.assistants.openai_assistant import OpenAIAssistant
from lib.ai_assistant.base_ai_assistant import BaseAIAssistant
from lib.logger import get_logger

from langchain.chat_models import ChatOpenAI
from langchain.callbacks.manager import CallbackManager
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessage,
    HumanMessagePromptTemplate,
)
import openai


LOG = get_logger(__file__)


class OpenAINoStreamAssistant(OpenAIAssistant):
    """To use it, please set the following environment variable:
    OPENAI_API_KEY: OpenAI API key
    """

    @property
    def name(self) -> str:
        return "openai_nostream"

    def _generate_title_from_query(
        self, query, stream=True, callback_handler=None, user_id=None
    ):
        """Generate title from SQL query using OpenAI's chat model."""
        messages = self.title_generation_prompt_template.format_prompt(
            query=query
        ).to_messages()
        chat = ChatOpenAI(
            **self._config,
            streaming=False,
        )
        ai_message = chat(messages)
        callback_handler.on_llm_new_token(ai_message.content)
        callback_handler.on_llm_end(None)
        return ai_message.content

    def _query_auto_fix(
        self,
        language,
        query,
        error,
        table_schemas,
        stream,
        callback_handler,
        user_id=None,
    ):
        """Query auto fix using OpenAI's chat model."""
        messages = self.query_auto_fix_prompt_template.format_prompt(
            dialect=language, query=query, error=error, table_schemas=table_schemas
        ).to_messages()
        chat = ChatOpenAI(
            **self._config,
            streaming=False,
        )
        ai_message = chat(messages)
        callback_handler.on_llm_new_token(ai_message.content)
        callback_handler.on_llm_end(None)
        return ai_message.content

    def _generate_sql_query(
        self,
        language: str,
        table_schemas: str,
        question: str,
        original_query: str,
        stream,
        callback_handler,
        user_id=None,
    ):
        """Generate SQL query using OpenAI's chat model."""
        messages = self.generate_sql_query_prompt_template.format_prompt(
            dialect=language,
            question=question,
            table_schemas=table_schemas,
            original_query=original_query,
        ).to_messages()
        chat = ChatOpenAI(**self._config, streaming=False)
        ai_message = chat(messages)
        callback_handler.on_llm_new_token(ai_message.content)
        callback_handler.on_llm_end(None)
        return ai_message.content
