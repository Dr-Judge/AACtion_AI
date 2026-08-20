from fastapi.testclient import TestClient

from app.core.settings import settings
from main import app

client = TestClient(app)


def test_인증_통과하면_판정_계약대로_응답한다(monkeypatch):
    # 아카이브 검색 결과가 없을 때의 경로(NO_EVIDENCE)만 오프라인으로 검증한다.
    # trust_level 등을 판단하는 본체 LLM 호출은 이 경로에서 애초에 안 타지만, title은
    # 이 경로에서도 별도로 LLM을 호출하므로(_generate_title) 같이 모킹한다 — CI에
    # OPENAI_API_KEY가 없어서 실제 호출하면 테스트가 깨진다.
    monkeypatch.setattr("app.judgment.service.search_archive", lambda *args, **kwargs: [])

    async def _fake_generate_title(claim):
        return "테스트 제목?"

    monkeypatch.setattr("app.judgment.service._generate_title", _fake_generate_title)

    response = client.post(
        "/internal/api/v1/judgments",
        json={"text": "테스트 주장", "category_id": 1},
        headers={"X-Internal-Api-Key": settings.internal_api_key},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["title"] == "테스트 제목?"
    assert body["trust_level"] in {
        "CLINICAL_EVIDENCE",
        "EXPERT_OPINION",
        "PENDING",
        "COUNTER_EVIDENCE",
        "NO_EVIDENCE",
    }
    assert "conflict_of_interest" in body
    assert "sources" in body
    assert "guide_card" in body


def test_인증_헤더_없으면_401():
    response = client.post("/internal/api/v1/judgments", json={"text": "테스트 주장"})
    assert response.status_code == 401


def test_인증_헤더_틀리면_401():
    response = client.post(
        "/internal/api/v1/judgments",
        json={"text": "테스트 주장"},
        headers={"X-Internal-Api-Key": "wrong-key"},
    )
    assert response.status_code == 401
