from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.scan_result import PredictResponse
from app.services.inference_service import InferenceService

router = APIRouter(tags=["Inferencia"])
svc = InferenceService()

@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Formato de imagen no soportado")
    image_bytes = await file.read()
    result = svc.run(image_bytes)
    if result is None:
        return PredictResponse(success=False, error="No se detectó ninguna fruta soportada")
    return PredictResponse(success=True, data=result)