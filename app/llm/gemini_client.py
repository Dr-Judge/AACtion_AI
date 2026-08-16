from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.settings import settings


@lru_cache
def get_chat_model() -> ChatGoogleGenerativeAI:
    """공용 연결 팩토리 — 키/타임아웃/모델명만 다룬다.

    프롬프트나 판정 로직 같은 도메인 계약은 여기 두지 않는다 (judgment 도메인이 소유).
    """
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.2,
        timeout=25,
    )
