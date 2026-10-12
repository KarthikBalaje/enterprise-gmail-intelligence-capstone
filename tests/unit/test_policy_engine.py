from policy_engine import Action, MessageFacts, authorize_action


def test_sent_message_cannot_be_trashed():
    facts = MessageFacts(message_id="sent-1", is_sent=True, classification_confident=True)
    allowed, reason = authorize_action(facts, Action.TRASH, user_approved=True)
    assert not allowed
    assert "Sent" in reason


def test_draft_cannot_be_trashed():
    facts = MessageFacts(message_id="draft-1", is_draft=True, classification_confident=True)
    allowed, _ = authorize_action(facts, Action.TRASH, user_approved=True)
    assert not allowed


def test_work_email_cannot_be_trashed():
    facts = MessageFacts(message_id="work-1", is_work_related=True, classification_confident=True)
    allowed, _ = authorize_action(facts, Action.TRASH, user_approved=True)
    assert not allowed


def test_personally_protected_email_cannot_be_trashed():
    facts = MessageFacts(message_id="personal-1", is_personally_protected=True, classification_confident=True)
    allowed, _ = authorize_action(facts, Action.TRASH, user_approved=True)
    assert not allowed


def test_unapproved_trash_is_rejected():
    facts = MessageFacts(message_id="promo-1", classification_confident=True)
    allowed, reason = authorize_action(facts, Action.TRASH, user_approved=False)
    assert not allowed
    assert "approval" in reason.lower()


def test_uncertain_email_is_not_trashed():
    facts = MessageFacts(message_id="unknown-1", classification_confident=False)
    allowed, _ = authorize_action(facts, Action.TRASH, user_approved=True)
    assert not allowed


def test_work_email_cannot_be_archived_by_cleanup():
    facts = MessageFacts(message_id="work-2", is_work_related=True, classification_confident=True)
    allowed, _ = authorize_action(facts, Action.ARCHIVE, user_approved=True)
    assert not allowed
