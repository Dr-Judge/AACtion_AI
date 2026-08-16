from fastapi.testclient import TestClient

from app.core.settings import settings
from main import app

client = TestClient(app)


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


def test_인증_통과하면_판정_계약대로_응답한다():
    response = client.post(
        "/internal/api/v1/judgments",
        json={"text": "테스트 주장", "category_id": 1},
        headers={"X-Internal-Api-Key": settings.internal_api_key},
    )
    assert response.status_code == 200

    body = response.json()
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
