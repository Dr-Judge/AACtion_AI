from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class JudgmentProcessingError(Exception):
    """RAG 검색/LLM 호출 등 판정 처리 중 발생하는 복구 불가능한 오류.

    Spring 쪽에서는 5xx로 받아 1회 재시도 후 실패 처리한다 (AI_SERVICE_CONTRACT.md).
    """


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(JudgmentProcessingError)
    async def handle_judgment_processing_error(request: Request, exc: JudgmentProcessingError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})
