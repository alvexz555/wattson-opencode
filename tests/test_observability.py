import json
import unittest

from wattson_core.observability import build_event, emit_event


class ObservabilityTests(unittest.TestCase):
    def test_event_has_required_fields_and_utc_timestamp(self):
        event = build_event("request.completed", "orchestrator")

        self.assertEqual(
            set(event),
            {
                "timestamp", "event_type", "component", "level",
                "status", "message", "correlation_id", "fields",
            },
        )
        self.assertTrue(event["timestamp"].endswith("+00:00"))
        self.assertTrue(event["correlation_id"])

    def test_correlation_id_can_be_shared(self):
        event = build_event(
            "tool.completed", "executor", correlation_id="request-123"
        )
        self.assertEqual(event["correlation_id"], "request-123")

    def test_sensitive_fields_and_text_are_redacted(self):
        event = build_event(
            "auth.check",
            "provider",
            message="authorization=secret-value",
            fields={
                "api_key": "secret-key",
                "nested": {"password": "secret-password"},
                "detail": "Bearer abc.def.ghi",
            },
        )

        serialized = json.dumps(event)
        for secret in (
            "secret-value", "secret-key", "secret-password",
            "abc.def.ghi",
        ):
            self.assertNotIn(secret, serialized)

        self.assertEqual(event["fields"]["api_key"], "[REDACTED]")
        self.assertEqual(
            event["fields"]["nested"]["password"], "[REDACTED]"
        )

    def test_circular_values_do_not_break_event(self):
        circular = {}
        circular["self"] = circular
        event = build_event("test", "tests", fields=circular)
        self.assertEqual(event["fields"]["self"], "[CIRCULAR]")
        json.dumps(event)

    def test_unknown_objects_do_not_expose_repr(self):
        class SecretObject:
            def __repr__(self):
                return "password=hidden-value"

        event = build_event(
            "test", "tests", fields={"object": SecretObject()}
        )
        self.assertEqual(
            event["fields"]["object"], "[UNSUPPORTED:SecretObject]"
        )
        self.assertNotIn("hidden-value", json.dumps(event))

    def test_sink_failure_does_not_propagate(self):
        def broken_sink(_event):
            raise RuntimeError("sink unavailable")

        event = emit_event(
            "test", "tests", sink=broken_sink
        )
        self.assertEqual(event["event_type"], "test")

    def test_sink_receives_the_event(self):
        received = []
        event = emit_event("test", "tests", sink=received.append)
        self.assertEqual(received, [event])


if __name__ == "__main__":
    unittest.main()
