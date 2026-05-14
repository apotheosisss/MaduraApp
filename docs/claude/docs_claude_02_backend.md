# 02 — Backend: FastAPI + YOLO26n

## Código implementado hasta ahora

### `backend/app/main.py`
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import predict, history
from app.core.config import settings
from app.core.yolo_wrapper import YOLO26Wrapper

model: YOLO26Wrapper = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model = YOLO26Wrapper(settings.YOLO_MODEL_PATH)
    model.load_model()
    yield
    del model

app = FastAPI(
    title="MaduraApp API",
    version="1.0.0",
    description="Backend de análisis de madurez agrícola con YOLO26n",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(predict.router, prefix="/v1")
app.include_router(history.router, prefix="/v1")

@app.get("/v1/health")
async def health():
    return {"status": "ok", "model": "yolo26n", "version": "1.0.0"}
```

### `backend/app/core/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_PORT: int = 8000
    YOLO_MODEL_PATH: str = "weights/yolo26n_maduraapp.pt"
    CONFIDENCE_THRESHOLD: float = 0.65
    DB_URL: str = "sqlite+aiosqlite:///./maduraapp_dev.db"
    AUTH_SECRET_KEY: str = "dev_secret_key"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

### `backend/app/core/yolo_wrapper.py`
```python
from ultralytics import YOLO

class YOLO26Wrapper:
    def __init__(self, model_path: str, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self.model: YOLO = None

    def load_model(self):
        self.model = YOLO(self.model_path)
        self.warmup()

    def warmup(self):
        import numpy as np
        dummy = np.zeros((1, 3, 640, 640), dtype=np.uint8)
        self.model.predict(dummy, verbose=False)

    def predict(self, image) -> list:
        return self.model.predict(image, imgsz=640, verbose=False)
```

### `backend/app/schemas/scan_result.py`
```python
from pydantic import BaseModel
from typing import Optional

class ScanResult(BaseModel):
    fruit_type: str
    maturity_label: str        # INMADURO | OPTIMO | SOBRE_MADURO
    confidence: float
    bbox: list[float]
    recommendation: str
    color_code: str            # green | yellow | red

    def to_json(self) -> dict:
        return self.model_dump()

class PredictResponse(BaseModel):
    success: bool
    data: Optional[ScanResult] = None
    error: Optional[str] = None
```

### `backend/app/routers/predict.py` (esqueleto)
```python
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
```

---

## Código PENDIENTE de implementar

### `backend/app/services/inference_service.py` — IMPLEMENTAR
```python
# PENDIENTE — Implementar lógica completa:
# - preprocess(image_bytes) → PIL Image → ndarray 640×640
# - run_inference(ndarray) → YOLO26n Results
# - postprocess(Results) → ScanResult
# - validate_image(bytes) → bool (blur, darkness, size checks)
# - Mapeo class_id → FruitClass + MaturityLabel
# - Mapeo MaturityLabel → color_code (green/yellow/red)
# - Mapeo FruitClass + MaturityLabel → recommendation text
```

**Clases del modelo YOLO26n (class_id → etiqueta):**
```python
CLASS_MAP = {
    0: ("aguacate_hass", "INMADURO"),
    1: ("aguacate_hass", "OPTIMO"),
    2: ("aguacate_hass", "SOBRE_MADURO"),
    3: ("platano", "INMADURO"),
    4: ("platano", "OPTIMO"),
    5: ("platano", "SOBRE_MADURO"),
    6: ("tomate_usda", "INMADURO"),
    7: ("tomate_usda", "OPTIMO"),
    8: ("tomate_usda", "SOBRE_MADURO"),
    9: ("mango", "INMADURO"),
    10: ("mango", "OPTIMO"),
    11: ("mango", "SOBRE_MADURO"),
}

COLOR_MAP = {
    "INMADURO": "green",
    "OPTIMO": "yellow",
    "SOBRE_MADURO": "red",
}

RECOMMENDATION_MAP = {
    ("aguacate_hass", "INMADURO"): "Dejar madurar a temperatura ambiente 3-5 días",
    ("aguacate_hass", "OPTIMO"): "Consumir hoy o refrigerar hasta 2 días",
    ("aguacate_hass", "SOBRE_MADURO"): "Consumir inmediatamente o usar en guacamole",
    ("platano", "INMADURO"): "Madurar en bolsa de papel 2-3 días",
    ("platano", "OPTIMO"): "Punto ideal de consumo",
    ("platano", "SOBRE_MADURO"): "Usar para batidos o pan de plátano",
    ("tomate_usda", "INMADURO"): "Esperar 5-7 días a temperatura ambiente",
    ("tomate_usda", "OPTIMO"): "Consumir en los próximos 2 días",
    ("tomate_usda", "SOBRE_MADURO"): "Usar inmediatamente para salsas o cocinar",
    ("mango", "INMADURO"): "Madurar a temperatura ambiente 3-6 días",
    ("mango", "OPTIMO"): "Consumir hoy, refrigerar si no lo consumes",
    ("mango", "SOBRE_MADURO"): "Usar para jugos o batidos inmediatamente",
}
```

### `backend/app/models/scan_entity.py` — IMPLEMENTAR
```python
# PENDIENTE — SQLAlchemy ORM async
# Tablas: ScanEntity, FrutaEntity, MaturityEntity, RecomendacionEntity
# Usar: declarative_base, mapped_column, Mapped, UUID, ForeignKey
```

### `backend/app/services/history_service.py` — IMPLEMENTAR
```python
# PENDIENTE
# - save(scan: ScanResult, user_token: str) → ScanEntity
# - get_all(user_token: str, limit: int = 50) → list[ScanResult]
# - Usar AsyncSession de SQLAlchemy
```

### `backend/app/routers/history.py` — IMPLEMENTAR
```python
# PENDIENTE
# GET /v1/history — devuelve historial del usuario autenticado
# Parámetros: limit (default 50), offset (default 0)
```

---

## API Reference completa

### `POST /v1/predict`
```
Content-Type: multipart/form-data
Authorization: Bearer <token>

Body:
  file: <image> (jpeg | png | webp, max 10MB)

Response 200:
{
  "success": true,
  "data": {
    "fruit_type": "aguacate_hass",
    "maturity_label": "OPTIMO",
    "confidence": 0.913,
    "bbox": [120.5, 80.3, 340.2, 290.1],
    "recommendation": "Consumir hoy o refrigerar hasta 2 días",
    "color_code": "yellow"
  }
}

Response 200 (no detectado):
{
  "success": false,
  "error": "No se detectó ninguna fruta soportada"
}

Response 400: Formato de imagen no soportado
Response 401: Token inválido o expirado
```

### `GET /v1/history`
```
Authorization: Bearer <token>
Query params: limit=50&offset=0

Response 200:
{
  "items": [ScanResult, ...],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

### `GET /v1/health`
```
Response 200:
{
  "status": "ok",
  "model": "yolo26n",
  "version": "1.0.0"
}
```

---

## Requirements

```
fastapi==0.135.1
uvicorn[standard]==0.30.0
python-multipart==0.0.9
pydantic==2.7.0
pydantic-settings==2.3.0
ultralytics>=8.3.0
Pillow==10.3.0
numpy==1.26.4
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
aiosqlite==0.20.0
python-jose[cryptography]==3.3.0
pytest==8.2.0
pytest-asyncio==0.23.0
httpx==0.27.0
```

---

## CI/CD — GitHub Actions

Archivo: `.github/workflows/backend_ci.yml`

- **Trigger:** push a `main` o `develop`, PR a `main`
- **Runner:** ubuntu-latest, Python 3.12
- **Pasos:** checkout → setup Python → install requirements → pytest
- **Estado actual:** Verde ✅ (test placeholder `assert True`)
- **Próximo paso:** Reemplazar placeholder con tests reales en Sprint 2

---

## Variables de entorno

```bash
# .env (nunca subir a Git)
API_PORT=8000
YOLO_MODEL_PATH=weights/yolo26n_maduraapp.pt
CONFIDENCE_THRESHOLD=0.65
DB_URL=postgresql+asyncpg://user:password@localhost:5432/maduraapp
AUTH_SECRET_KEY=CAMBIA_ESTO_EN_PRODUCCION
ENVIRONMENT=development
```
