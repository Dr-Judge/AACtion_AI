"""이해상충(상업적 의도) 키워드 탐지 — 공동구매/구매 링크/협찬 고지 등."""
import pytest

from app.judgment.service import _detect_conflict_by_keyword


@pytest.mark.parametrize(
    "text, expected_type",
    [
        ("오늘만 공동구매 50% 할인, 프로필 링크 클릭", "COMMERCIAL"),
        ("설명란 구매 링크에서 최저가로 만나보세요", "COMMERCIAL"),
        ("공구 오픈했어요! 마감되기 전에 신청하세요", "COMMERCIAL"),
        ("이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 받습니다", "SPONSORSHIP_DISCLOSURE"),
        ("업체로부터 제품을 제공받아 작성한 후기입니다 (협찬)", "SPONSORSHIP_DISCLOSURE"),
        ("오늘만 이 가격! 선착순 100명 한정수량", "COMMERCIAL"),  # 약한 신호 2개 이상
    ],
)
def test_detects_commercial_intent(text, expected_type):
    result = _detect_conflict_by_keyword(text)
    assert result.detected is True
    assert result.type == expected_type
    assert result.description


@pytest.mark.parametrize(
    "text",
    [
        "오메가3를 먹으면 중성지방이 내려간다고 하던데 맞나요?",
        "가르시니아가 살 빼는 데 도움이 될까요?",
        "오늘만 일찍 자려고 해요. 멜라토닌 먹어도 되나요?",  # 약한 신호 1개는 탐지하지 않음
        "공구함에서 드라이버를 꺼내 썼다",  # '공구'(도구)는 공동구매가 아님
    ],
)
def test_does_not_flag_plain_questions(text):
    result = _detect_conflict_by_keyword(text)
    assert result.detected is False
    assert result.type is None and result.description is None
