from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.scan_result import HistoryResponse
from app.services.history_service import HistoryService

router = APIRouter(tags=["Historial"])
svc = HistoryService()


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    authorization: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    user_token = authorization.removeprefix("Bearer ").strip() or "anonymous"
    items, total = await svc.get_all(user_token, db, limit, offset)
    return HistoryResponse(items=items, total=total, limit=limit, offset=offset)
