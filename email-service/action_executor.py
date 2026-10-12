"""No-op executor until real OAuth, HITL and audit persistence are implemented.

Never pass this function directly to an LLM as an unrestricted tool.
"""


def execute_approved_action(*args, **kwargs) -> dict:
    raise RuntimeError(
        "Gmail write actions are disabled in this scaffold. "
        "Implement approval binding, fresh policy checks, audit logging and tests first."
    )
