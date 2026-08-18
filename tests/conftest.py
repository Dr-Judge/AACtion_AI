import os

# app.core.settings가 임포트되기 전에 필수 환경변수를 채워둔다 (실제 키 필요 없음, 테스트 전용 값).
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
