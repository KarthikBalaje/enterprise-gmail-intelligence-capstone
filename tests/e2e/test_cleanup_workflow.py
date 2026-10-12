"""TODO: End-to-end test using synthetic emails and a mock Gmail adapter."""
import pytest


@pytest.mark.skip(reason="E2E flow needs full service test harness")
def test_cleanup_plan_is_dry_run_and_never_executes_actions():
    assert False
