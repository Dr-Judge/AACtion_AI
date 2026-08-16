from fastapi import APIRouter, Depends

from app.core.security import verify_internal_api_key
from app.judgment.schemas import JudgmentRequest, JudgmentResponse
from app.judgment.service import judge

router = APIRouter(
    prefix="/internal/api/v1/judgments",
    tags=["judgment"],
    dependencies=[Depends(verify_internal_api_key)],
)


@router.post("", response_model=JudgmentResponse)
async def create_judgment(request: JudgmentRequest) -> JudgmentResponse:
    return await judge(request)
