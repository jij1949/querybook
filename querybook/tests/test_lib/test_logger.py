import io
import logging
from unittest import TestCase
from unittest.mock import patch

from lib.logger import CeleryTaskContextFilter, get_logger


class FakeRequest:
    def __init__(self, id):
        self.id = id


class FakeTask:
    def __init__(self, name, task_id):
        self.name = name
        self.request = FakeRequest(task_id)


def make_record():
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )


class CeleryTaskContextFilterTestCase(TestCase):
    def test_inside_task_sets_segment(self):
        record = make_record()
        with patch(
            "lib.logger.current_task",
            FakeTask("update_metastore_15", "1df32a54-8d88"),
        ):
            CeleryTaskContextFilter().filter(record)
        self.assertEqual(
            record.celery_task_context,
            "[task=update_metastore_15 task_id=1df32a54-8d88] ",
        )

    def test_no_task_is_empty(self):
        record = make_record()
        with patch("lib.logger.current_task", None):
            CeleryTaskContextFilter().filter(record)
        self.assertEqual(record.celery_task_context, "")

    def test_task_without_request_id_is_empty(self):
        # current_task exists but there is no active request id (not executing)
        record = make_record()
        with patch("lib.logger.current_task", FakeTask("some_task", None)):
            CeleryTaskContextFilter().filter(record)
        self.assertEqual(record.celery_task_context, "")

    def test_raising_proxy_is_safe(self):
        # A proxy that raises on any access (e.g. an unbound LocalProxy) must
        # not break logging; the filter falls back to empty context.
        class RaisingProxy:
            def __bool__(self):
                raise RuntimeError("no object bound")

            def __getattr__(self, name):
                raise RuntimeError("no object bound")

        record = make_record()
        with patch("lib.logger.current_task", RaisingProxy()):
            self.assertTrue(CeleryTaskContextFilter().filter(record))
        self.assertEqual(record.celery_task_context, "")


class GetLoggerTestCase(TestCase):
    def test_disables_propagation(self):
        log = get_logger("test_lib.test_logger.propagation")
        self.assertFalse(log.propagate)

    def test_no_duplicate_handlers_on_repeat_calls(self):
        name = "test_lib.test_logger.dedupe"
        first = get_logger(name)
        handler_count = len(first.handlers)
        second = get_logger(name)
        self.assertIs(first, second)
        self.assertEqual(len(second.handlers), handler_count)


class GetLoggerFormatTestCase(TestCase):
    def _capture(self, logger):
        # Mirror how get_logger builds a handler: same formatter AND the
        # task-context filter, since the filter now lives on the handler.
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logger.handlers[0].formatter)
        handler.addFilter(CeleryTaskContextFilter())
        logger.addHandler(handler)
        return stream, handler

    def test_segment_rendered_inside_task(self):
        log = get_logger("test_lib.test_logger.format_task")
        stream, handler = self._capture(log)
        try:
            with patch(
                "lib.logger.current_task",
                FakeTask("update_metastore_15", "abc-123"),
            ):
                log.info("Found 469 schemas")
        finally:
            log.removeHandler(handler)
        self.assertIn("[task=update_metastore_15 task_id=abc-123]", stream.getvalue())

    def test_segment_omitted_outside_task(self):
        log = get_logger("test_lib.test_logger.format_no_task")
        stream, handler = self._capture(log)
        try:
            with patch("lib.logger.current_task", None):
                log.info("web request served")
        finally:
            log.removeHandler(handler)
        output = stream.getvalue()
        self.assertNotIn("task=", output)
        self.assertIn("web request served", output)

    def test_record_propagated_from_descendant_does_not_raise(self):
        # A record originating at a descendant logger (no handler of its own)
        # propagates up to the get_logger handler. The filter lives on the
        # handler, so the attribute is set and the formatter must not KeyError.
        parent = get_logger("test_lib.test_logger.parent")
        stream, handler = self._capture(parent)
        child = logging.getLogger("test_lib.test_logger.parent.child")
        child.propagate = True
        child.setLevel(logging.INFO)
        try:
            with patch("lib.logger.current_task", None):
                child.info("from a descendant logger")
        finally:
            parent.removeHandler(handler)
        self.assertIn("from a descendant logger", stream.getvalue())
