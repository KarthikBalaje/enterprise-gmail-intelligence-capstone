
"""Create safe cleanup proposals; never execute Gmail actions."""


def make_plan(user_request: str, candidates: list[dict]) -> list[dict]:
    planned = []

    for candidate in candidates:
        item = {**candidate, "request_summary": user_request[:240]}

        protected = any((
            item.get("is_sent", False),
            item.get("is_draft", False),
            item.get("is_work_related", False),
            item.get("is_personally_protected", False),
        ))
        confident = item.get("classification_confident", False)

        if protected:
            item["proposed_action"] = "keep"
            item["review_status"] = "skipped_protected"
        elif not confident:
            item["proposed_action"] = "keep"
            item["review_status"] = "manual_review_required"
        elif item.get("category") == "promotion":
            item["proposed_action"] = "keep"
            item["review_status"] = "eligible_for_human_review"
        else:
            item["proposed_action"] = "keep"
            item["review_status"] = "manual_review_required"

        planned.append(item)

    return planned
