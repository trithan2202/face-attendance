import json
import logging
import unittest

from backend.app.core.logging import JsonFormatter, log_extra, request_id_context


class LoggingTests(unittest.TestCase):
    def test_json_log_contains_event_context_and_safe_fields(self):
        formatter = JsonFormatter()
        token = request_id_context.set("request-test-1")
        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname=__file__,
                lineno=1,
                msg="Business event",
                args=(),
                exc_info=None,
            )
            for key, value in log_extra(
                "test_event", session_id="session-1", password="secret"
            ).items():
                setattr(record, key, value)
            output = json.loads(formatter.format(record))
        finally:
            request_id_context.reset(token)

        self.assertEqual(output["event"], "test_event")
        self.assertEqual(output["request_id"], "request-test-1")
        self.assertEqual(output["session_id"], "session-1")
        self.assertEqual(output["password"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
