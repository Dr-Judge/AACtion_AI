# AACtion_AI — 닥터저지 판정 AI 서비스

Dr-Judge(Spring) 백엔드가 호출하는 판정 AI 서비스. RAG 검색 + OpenAI 추론을 담당한다.
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
├── llm/        # 공용 연결 팩토리 (OpenAI 클라이언트, 키/타임아웃만)
└── judgment/   # 판정 도메인 — 프롬프트, RAG 오케스트레이션
    └── rag/    # 벡터스토어, 검색, 인제스트
```

## 현재 상태

`app/judgment/service.py`가 실제 RAG 검색 + OpenAI 구조화 출력으로 판정을 수행한다.
아카이브 검색 결과가 없으면 LLM 호출 없이 바로 NO_EVIDENCE를 반환한다.

## 아카이브 인제스트

관리자가 Dr-Judge MySQL의 `archive_items`를 직접 추가/수정한 뒤 수동 실행:

```bash
python -m app.judgment.rag.ingest
```
