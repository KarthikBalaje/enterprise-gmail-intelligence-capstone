"""Deterministic, fail-closed cleanup policy.

The LLM is not an authorization mechanism. This policy is called both when
creating the review list and immediately before any real Gmail write.
"""
from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    KEEP = "keep"
    LABEL = "label"
    ARCHIVE = "archive"
    TRASH = "trash"


@dataclass(frozen=True)
class MessageFacts:
    message_id: str
    is_sent: bool = False
    is_draft: bool = False
    is_work_related: bool = False
    is_personally_protected: bool = False
    classification_confident: bool = False


def authorize_action(
    facts: MessageFacts,
    action: Action,
    *,
    user_approved: bool = False,
) -> tuple[bool, str]:
    if action in (Action.ARCHIVE, Action.TRASH):
        if facts.is_sent:
            return False, "Sent messages are protected from cleanup modifications"
        if facts.is_draft:
            return False, "Draft messages are protected from cleanup modifications"

    if action == Action.TRASH:
        if facts.is_work_related:
            return False, "Work-related messages cannot be deleted"
        if facts.is_personally_protected:
            return False, "Personally protected messages cannot be deleted"
        if not facts.classification_confident:
            return False, "Uncertain messages must be skipped for manual review"
        if not user_approved:
            return False, "Explicit human approval is required for deletion"

    if action == Action.ARCHIVE:
        if facts.is_work_related:
            return False, "Work-related messages cannot be archived by cleanup"
        if facts.is_personally_protected:
            return False, "Personally protected messages cannot be archived by cleanup"
        if not facts.classification_confident:
            return False, "Uncertain messages must be skipped for manual review"

    return True, "Allowed by starter policy"
