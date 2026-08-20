import asyncio
import json

from pydantic import BaseModel, ValidationError

from app.judgment.prompt import (
    SYSTEM_PROMPT,
    TITLE_ONLY_SYSTEM_PROMPT,
    build_title_only_user_prompt,
    build_user_prompt,
)
from app.judgment.rag.retriever import search_archive
from app.judgment.schemas import ConflictOfInterest, GuideCard, JudgmentRequest, JudgmentResponse, Source
from app.llm.openai_client import get_chat_model

TRUST_LEVELS = ("CLINICAL_EVIDENCE", "EXPERT_OPINION", "PENDING", "NO_EVIDENCE", "COUNTER_EVIDENCE")

# 근거 문서 유무와 무관하게 입력 원문만으로 판단 가능한 협찬/제휴마케팅 고지 신호.
# LLM 호출 없이도(NO_EVIDENCE 경로 포함) 항상 검사해야 한다.
_SPONSORSHIP_KEYWORDS = ("쿠팡파트너스", "협찬", "제공받아 작성", "제공받은 원고", "유료광고", "체험단")


def _detect_conflict_by_keyword(text: str) -> ConflictOfInterest:
    for kw in _SPONSORSHIP_KEYWORDS:
        if kw in text:
            return ConflictOfInterest(
                detected=True,
                type="SPONSORSHIP_DISCLOSURE",
                description=f"입력 텍스트에 협찬/제휴마케팅 고지로 보이는 표현('{kw}')이 포함되어 있습니다.",
            )
    return ConflictOfInterest(detected=False, type=None, description=None)


# LLM 구조화 출력 전용 스키마. sources/guide_card.source_type 같은 "사실값"과
# 이해상충 판단(입력 원문만으로 결정론적으로 판단하는 게 정책)은 여기 포함하지 않는다 —
# 할루시네이션 방지 + 근거 유무에 따라 이해상충 결과가 달라지는 모순을 막기 위함.
class LlmJudgmentOutput(BaseModel):
    title: str
    trust_level: str
    evidence_summary: str
    primary_archive_item_id: int | None
    guide_card_title: str
    guide_card_tips: list[str]
    safety_notice: str | None


_TITLE_MAX_LEN = 40


class _TitleOnlyOutput(BaseModel):
    title: str


def _truncated_fallback_title(claim: str) -> str:
    # _generate_title 자체가 실패했을 때(OpenAI 호출 오류 등)의 최후 수단이라, 완벽한
    # 의문문 재구성은 아니지만 판정 이력에 빈 제목이 뜨는 것보단 낫다.
    text = claim.strip().splitlines()[0].strip() if claim.strip() else "이 주장"
    text = text.rstrip("?!.  ")
    if len(text) > _TITLE_MAX_LEN:
        text = text[:_TITLE_MAX_LEN].rstrip() + "..."
    return f"{text}?"


async def _generate_title(claim: str) -> str:
    # 근거 후보가 없어 본체 LLM 호출을 안 하는 경로(NO_EVIDENCE)에서도, title만은 별도의
    # 가벼운 LLM 호출로 제대로 생성한다 — 원문(특히 유튜브 스크립트처럼 길고 장황한 텍스트)을
    # 그냥 잘라 붙이면 지저분한 제목이 나와서, 판정 이력/공유 카드 품질이 들쭉날쭉해진다.
    try:
        model = get_chat_model().with_structured_output(_TitleOnlyOutput)
        result: _TitleOnlyOutput = await model.ainvoke(
            [
                ("system", TITLE_ONLY_SYSTEM_PROMPT),
                ("human", build_title_only_user_prompt(claim)),
            ]
        )
        title = result.title.strip()
        return title if title else _truncated_fallback_title(claim)
    except Exception:
        return _truncated_fallback_title(claim)


async def _no_evidence_response(claim: str, title: str | None = None) -> JudgmentResponse:
    return JudgmentResponse(
        title=title or await _generate_title(claim),
        trust_level="NO_EVIDENCE",
        evidence_summary="현재 아카이브에서 이 주장과 관련된 근거 문서를 찾지 못했습니다. "
        "근거가 없다는 뜻이 아니라, 아직 충분히 확인되지 않았다는 의미입니다.",
        conflict_of_interest=_detect_conflict_by_keyword(claim),
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
    if not isinstance(raw, list):
        return []

    sources = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("title"):
            continue
        try:
            sources.append(Source(**item))
        except ValidationError:
            continue
    return sources


async def judge(request: JudgmentRequest) -> JudgmentResponse:
    candidates = await asyncio.to_thread(search_archive, request.text, request.category_id, k=3)
    if not candidates:
        return await _no_evidence_response(request.text)

    model = get_chat_model().with_structured_output(LlmJudgmentOutput)
    result: LlmJudgmentOutput = await model.ainvoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", build_user_prompt(request.text, candidates)),
        ]
    )

    trust_level = result.trust_level if result.trust_level in TRUST_LEVELS else "NO_EVIDENCE"
    primary = _find_candidate(candidates, result.primary_archive_item_id)

    # LLM이 evidence 기반 등급을 주장하면서 실제 후보와 매칭이 안 되면(프롬프트 위반),
    # 근거 없이 높은 신뢰도만 표시되는 모순을 막기 위해 안전하게 NO_EVIDENCE로 대체한다.
    if trust_level != "NO_EVIDENCE" and primary is None:
        # title은 이미 LLM이 생성했으니(result.title) 그대로 재사용 — 굳이 별도
        # LLM 호출로 다시 만들 필요 없음.
        return await _no_evidence_response(request.text, title=result.title)

    sources = _parse_sources(primary["metadata"].get("sources_json", "[]")) if primary else []
    source_type = (primary["metadata"].get("evidence_source_type") or "일반 안내") if primary else "일반 안내"
    source_ref = (
        f"{primary['metadata'].get('target', '')} {primary['metadata'].get('effect', '')}".strip()
        if primary
        else ""
    )

    safety_notice = result.safety_notice if trust_level in ("PENDING", "NO_EVIDENCE") else None

    return JudgmentResponse(
        title=result.title,
        trust_level=trust_level,
        evidence_summary=result.evidence_summary,
        conflict_of_interest=_detect_conflict_by_keyword(request.text),
        safety_notice=safety_notice,
        sources=sources,
        guide_card=GuideCard(
            title=result.guide_card_title,
            source_type=source_type,
            source_ref=source_ref,
            tips=result.guide_card_tips,
        ),
    )
