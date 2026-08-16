from fastapi import FastAPI

from app.core.exceptions import register_exception_handlers
from app.judgment.router import router as judgment_router

app = FastAPI(title="Dr-Judge AI Service", version="v1")

register_exception_handlers(app)
app.include_router(judgment_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "UP"}
