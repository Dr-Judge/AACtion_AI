from app.judgment.schemas import ConflictOfInterest, GuideCard, JudgmentRequest, JudgmentResponse

# TODO: 실제 RAG 검색(app.judgment.rag.retriever.search_archive) + Gemini 추론으로 대체.
# 지금은 Spring 쪽 연동 테스트가 실제 Gemini/Chroma 키 없이도 가능하도록,
# 계약 형태만 맞춘 임시 응답을 반환한다 (외부 호출 없음).


async def judge(request: JudgmentRequest) -> JudgmentResponse:
    return JudgmentResponse(
        trust_level="PENDING",
        evidence_summary="TODO: 실제 Gemini 추론 결과로 대체 예정",
        conflict_of_interest=ConflictOfInterest(detected=False, type=None, description=None),
        safety_notice="충분한 근거가 아직 확인되지 않았습니다. 전문가와 상담하세요.",
        sources=[],
        guide_card=GuideCard(title="TODO", source_type="TODO", source_ref="TODO", tips=[]),
    )
