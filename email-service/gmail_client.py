"""Gmail adapter boundary.

Implement OAuth and Gmail API calls here only after review. Begin with
read-only scopes. Do not persist tokens in source control. No write operation
is implemented in this starter file.
"""


class GmailClientNotConfigured(RuntimeError):
    pass


class GmailClient:
    def __init__(self, mode: str = "mock"):
        if mode not in {"mock", "readonly"}:
            raise ValueError("Only mock or readonly mode is allowed in this scaffold")
        self.mode = mode

    def list_messages(self, query: str = "", max_results: int = 20) -> list[dict]:
        if self.mode == "mock":
            return []
        raise GmailClientNotConfigured(
            "Read-only Gmail OAuth adapter is not implemented yet."
        )
