import asyncio

from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.scan_result import PredictResponse
from app.services.history_service import HistoryService
from app.services.inference_service import InferenceService

router = APIRouter(tags=["Inferencia"])
inference_svc = InferenceService()
history_svc = HistoryService()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: Request,
    file: UploadFile = File(...),
    authorization: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
) -> PredictResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Formato de imagen no soportado")

    model = request.app.state.model
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")

    image_bytes = await file.read()

    result = await asyncio.to_thread(inference_svc.run, image_bytes, model)

    if result is None:
        return PredictResponse(success=False, error="No se detectó ninguna fruta soportada")

    user_token = authorization.removeprefix("Bearer ").strip() or "anonymous"
    await history_svc.save(result, user_token, db)

    return PredictResponse(success=True, data=result)
