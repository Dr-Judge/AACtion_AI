import json

from pydantic import BaseModel

from app.judgment.prompt import SYSTEM_PROMPT, build_user_prompt
from app.judgment.rag.retriever import search_archive
from app.judgment.schemas import ConflictOfInterest, GuideCard, JudgmentRequest, JudgmentResponse, Source
from app.llm.openai_client import get_chat_model

TRUST_LEVELS = ("CLINICAL_EVIDENCE", "EXPERT_OPINION", "PENDING", "NO_EVIDENCE", "COUNTER_EVIDENCE")


# LLM 구조화 출력 전용 스키마. sources/guide_card.source_type 같은 "사실값"은
# 여기 포함하지 않는다 — 할루시네이션 방지를 위해 검색된 근거의 DB 값을 그대로 쓴다.
class LlmJudgmentOutput(BaseModel):
    trust_level: str
    evidence_summary: str
    primary_archive_item_id: int | None
    guide_card_title: str
    guide_card_tips: list[str]
    conflict_detected: bool
    conflict_type: str | None
    conflict_description: str | None
    safety_notice: str | None


def _no_evidence_response() -> JudgmentResponse:
    return JudgmentResponse(
        trust_level="NO_EVIDENCE",
        evidence_summary="현재 아카이브에서 이 주장과 관련된 근거 문서를 찾지 못했습니다. "
        "근거가 없다는 뜻이 아니라, 아직 충분히 확인되지 않았다는 의미입니다.",
        conflict_of_interest=ConflictOfInterest(detected=False, type=None, description=None),
        safety_notice="관련 근거가 아직 확인되지 않았습니다. 정확한 판단을 위해 전문가와 상담하세요.",
        sources=[],
        guide_card=GuideCard(
            title="이 점을 참고하세요",
            source_type="일반 안내",
            source_ref="",
            tips=["관련 근거가 아직 부족하니, 과장된 효과를 내세우는 표현은 주의해서 받아들이세요."],
        ),
    )


def _find_candidate(candidates: list[dict], archive_item_id: int | None) -> dict | None:
    if archive_item_id is None:
        return None
    for c in candidates:
        if c["metadata"].get("archive_item_id") == archive_item_id:
            return c
    return None


def _parse_sources(sources_json: str) -> list[Source]:
    try:
        raw = json.loads(sources_json or "[]")
    except (json.JSONDecodeError, TypeError):
        return []
    return [Source(**s) for s in raw if s.get("title")]


async def judge(request: JudgmentRequest) -> JudgmentResponse:
    candidates = search_archive(request.text, request.category_id, k=3)
    if not candidates:
        return _no_evidence_response()

    model = get_chat_model().with_structured_output(LlmJudgmentOutput)
    result: LlmJudgmentOutput = await model.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", build_user_prompt(request.text, candidates)),
        ]
    )

    trust_level = result.trust_level if result.trust_level in TRUST_LEVELS else "NO_EVIDENCE"
    primary = _find_candidate(candidates, result.primary_archive_item_id)

    sources = _parse_sources(primary["metadata"]["sources_json"]) if primary else []
    source_type = (primary["metadata"].get("evidence_source_type") or "일반 안내") if primary else "일반 안내"
    source_ref = (
        f"{primary['metadata'].get('target', '')} {primary['metadata'].get('effect', '')}".strip()
        if primary
        else ""
    )

    safety_notice = result.safety_notice if trust_level in ("PENDING", "NO_EVIDENCE") else None

    return JudgmentResponse(
        trust_level=trust_level,
        evidence_summary=result.evidence_summary,
        conflict_of_interest=ConflictOfInterest(
            detected=result.conflict_detected,
            type=result.conflict_type if result.conflict_detected else None,
            description=result.conflict_description if result.conflict_detected else None,
        ),
        safety_notice=safety_notice,
        sources=sources,
        guide_card=GuideCard(
            title=result.guide_card_title,
            source_type=source_type,
            source_ref=source_ref,
            tips=result.guide_card_tips,
        ),
    )
