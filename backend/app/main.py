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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/v1")
app.include_router(history.router, prefix="/v1")

@app.get("/v1/health")
async def health():
    return {"status": "ok", "model": "yolo26n", "version": "1.0.0"}