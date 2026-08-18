from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.settings import settings


@lru_cache
def get_chat_model() -> ChatOpenAI:
    """공용 연결 팩토리 — 키/타임아웃/모델명만 다룬다.

    프롬프트나 판정 로직 같은 도메인 계약은 여기 두지 않는다 (judgment 도메인이 소유).
    """
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
        timeout=25,
    )
