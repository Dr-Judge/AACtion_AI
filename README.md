# AACtion_AI — 닥터저지 판정 AI 서비스

Dr-Judge(Spring) 백엔드가 호출하는 판정 AI 서비스. RAG 검색 + Gemini 추론을 담당한다.
Spring↔Python 계약 상세는 [Dr-Judge/docs/AI_SERVICE_CONTRACT.md](https://github.com/Dr-Judge/AACtion_BE/blob/develop/docs/AI_SERVICE_CONTRACT.md) 참고.

## 로컬 실행

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env  # 값 채우기

uvicorn main:app --reload --port 8000
```

`http://localhost:8000/docs`에서 Swagger UI 확인 가능.

## 테스트

```bash
pytest -v
```

## 구조

```
app/
├── core/       # 설정, 인증, 예외 — 공용
├── llm/        # 공용 연결 팩토리 (Gemini 클라이언트, 키/타임아웃만)
└── judgment/   # 판정 도메인 — 프롬프트, RAG 오케스트레이션
    └── rag/    # 벡터스토어, 검색, 인제스트
```

## 현재 상태

`app/judgment/service.py`는 아직 스텁이다 — 계약 형태(응답 필드)만 맞춰서 반환하고
실제 RAG 검색/Gemini 추론은 하지 않는다. Spring 쪽 연동 테스트를 먼저 가능하게 하기 위함.
실제 구현은 별도 작업으로 이어감.

## 아카이브 인제스트

관리자가 Dr-Judge MySQL의 `archive_items`를 직접 추가/수정한 뒤 수동 실행:

```bash
python -m app.judgment.rag.ingest
```
