"""TODO: Add tests for prompt injection, bulk selection and stale approvals."""
import pytest


@pytest.mark.skip(reason="Real action executor is intentionally disabled")
def test_bulk_request_cannot_override_protected_message_policy():
    assert False
