import importlib
import os
from unittest import mock


def test_langsmith_settings_read_from_env():
    """QuerybookSettings exposes the three LangSmith env vars."""
    import env as env_module

    with mock.patch.dict(
        os.environ,
        {
            "LANGSMITH_TRACING": "true",
            "LANGSMITH_API_KEY": "test-key",
            "LANGSMITH_PROJECT": "federated-querybook_test",
        },
    ):
        try:
            # Re-import to pick up patched env
            importlib.reload(env_module)
            settings = env_module.QuerybookSettings

            assert settings.LANGSMITH_TRACING is True
            assert settings.LANGSMITH_API_KEY == "test-key"
            assert settings.LANGSMITH_PROJECT == "federated-querybook_test"
        finally:
            # Restore module to the live environment so subsequent tests are not affected
            importlib.reload(env_module)


def test_langsmith_settings_default_to_none():
    """LangSmith settings are None/False when env vars are absent.

    NOTE: This test uses clear=True to strip the environment, which removes
    QUERYBOOK_WORK_PATH and other required vars.  The reload would normally
    raise MissingConfigException; it is suppressed because conftest.py sets
    sys._called_from_test = True via pytest_configure(), which env.py checks
    before raising.
    """
    import env as env_module

    env_without_langsmith = {
        k: v for k, v in os.environ.items()
        if not k.startswith("LANGSMITH_")
    }
    with mock.patch.dict(os.environ, env_without_langsmith, clear=True):
        try:
            importlib.reload(env_module)
            settings = env_module.QuerybookSettings

            assert settings.LANGSMITH_TRACING is False
            assert settings.LANGSMITH_API_KEY is None
            assert settings.LANGSMITH_PROJECT is None
        finally:
            # Restore module to the live environment so subsequent tests are not affected
            importlib.reload(env_module)


def test_public_methods_are_traceable():
    """All public AI command methods must be decorated with @traceable.

    Uses a spy/reload approach so the check is independent of langsmith version —
    langchain 0.3.x pins langsmith<0.4, so we cannot rely on version-specific
    dunder attributes that only exist in newer versions.
    """
    import sys
    import functools
    import langsmith

    traced_names = []
    original_traceable = langsmith.traceable

    def recording_traceable(*args, **kwargs):
        name = kwargs.get("name")
        if name:
            traced_names.append(name)

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*a, **kw):
                return func(*a, **kw)
            return wrapper

        # @traceable without args: args[0] is the function itself
        if args and callable(args[0]):
            return decorator(args[0])
        return decorator

    module_name = "lib.ai_assistant.base_ai_assistant"
    sys.modules.pop(module_name, None)
    langsmith.traceable = recording_traceable
    try:
        import lib.ai_assistant.base_ai_assistant  # class body runs with our spy
    finally:
        langsmith.traceable = original_traceable
        sys.modules.pop(module_name, None)

    expected_methods = [
        "generate_sql_query",
        "query_auto_fix",
        "summarize_table",
        "summarize_query",
        "find_tables",
        "get_sql_completion",
        "generate_title_from_query",
        "generate_data_doc_title_from_query",
    ]
    for method_name in expected_methods:
        assert method_name in traced_names, (
            f"{method_name} is missing @traceable decorator"
        )


def test_traceable_is_noop_when_tracing_disabled(monkeypatch):
    """@traceable must not raise and must return normally when LANGSMITH_TRACING is unset."""
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)

    from unittest.mock import MagicMock, patch
    from lib.ai_assistant.base_ai_assistant import BaseAIAssistant
    from langchain_core.language_models.base import BaseLanguageModel

    class _MinimalAssistant(BaseAIAssistant):
        @property
        def name(self):
            return "test"

        def _get_token_count(self, ai_command, prompt):
            return 10

        def _get_context_length_by_model(self, model_name):
            return 4096

        def _get_llm(self, ai_command, prompt_length):
            llm = MagicMock(spec=BaseLanguageModel)
            chain = MagicMock()
            chain.invoke.return_value = "summary"
            llm.__or__ = MagicMock(return_value=chain)
            return llm

    assistant = _MinimalAssistant()
    assistant.set_config({"default": {"model_args": {"model_name": "gpt-4o"}}})

    with patch("lib.ai_assistant.base_ai_assistant.get_table_schema_by_name", return_value="schema"), \
         patch("lib.ai_assistant.base_ai_assistant.get_sample_query_cells_by_table_name", return_value=[]), \
         patch("lib.ai_assistant.base_ai_assistant.get_table_schemas_by_names", return_value="schema"):
        result = assistant.summarize_table(
            metastore_id=1,
            table_name="my_schema.my_table",
        )
        assert result == "summary"
