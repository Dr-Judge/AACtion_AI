from fastapi import Header, HTTPException, status

from app.core.settings import settings


async def verify_internal_api_key(x_internal_api_key: str | None = Header(default=None)) -> None:
    """Spring -> Python 호출 인증. 헤더 없거나 값이 다르면 401.

    (Dr-Judge의 X-Internal-Api-Key와 계약 동일 — docs/AI_SERVICE_CONTRACT.md 참고)
    """
    if x_internal_api_key is None or x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid internal api key")
