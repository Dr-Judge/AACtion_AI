from pydantic import BaseModel


class JudgmentRequest(BaseModel):
    text: str
    category_id: int | None = None


class ConflictOfInterest(BaseModel):
    detected: bool
    type: str | None = None
    description: str | None = None


class Source(BaseModel):
    title: str
    url: str
    publisher: str
    type: str


class GuideCard(BaseModel):
    title: str
    source_type: str
    source_ref: str
    tips: list[str]


class JudgmentResponse(BaseModel):
    trust_level: str
    evidence_summary: str
    conflict_of_interest: ConflictOfInterest
    safety_notice: str | None
    sources: list[Source]
    guide_card: GuideCard
