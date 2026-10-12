
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.graph import build_cleanup_plan

app = FastAPI(title="Gmail Cleanup Agent Service", version="0.1.0")


from app.telemetry import configure_tracing

configure_tracing(app, "agent-service")



class GmailCandidate(BaseModel):
    message_id: str = Field(min_length=1, max_length=500)
    sender: str = Field(default="", max_length=1000)
    recipient: str = Field(default="", max_length=1000)
    subject: str = Field(default="", max_length=2000)
    date: str = Field(default="", max_length=200)
    snippet: str = Field(default="", max_length=5000)
    label_ids: list[str] = Field(default_factory=list, max_length=100)

    # Explicit classification and policy fields
    category: str = Field(default="uncertain", max_length=100)
    is_sent: bool = False
    is_draft: bool = False
    is_work_related: bool = False
    is_personally_protected: bool = False
    classification_confident: bool = False
    proposed_action: str = Field(default="keep", max_length=50)



class PlanRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=100)
    request: str = Field(min_length=3, max_length=2000)
    max_candidates: int = Field(default=20, ge=1, le=100)
    candidates: list[GmailCandidate] | None = Field(default=None, max_length=100)


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent-service"}


@app.post("/plan")
def plan(body: PlanRequest):
    candidates = (
        [item.model_dump() for item in body.candidates]
        if body.candidates is not None
        else None
    )

    return build_cleanup_plan(
        request_id=body.request_id,
        user_request=body.request,
        max_candidates=body.max_candidates,
        candidates=candidates,
    )
