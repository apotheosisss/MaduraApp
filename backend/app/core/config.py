from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    API_PORT: int = 8000
    YOLO_MODEL_PATH: str = "weights/yolo26n_maduraapp.pt"
    CONFIDENCE_THRESHOLD: float = 0.65
    DB_URL: str = "sqlite+aiosqlite:///./maduraapp_dev.db"
    AUTH_SECRET_KEY: str = "dev_secret_key"
    ENVIRONMENT: str = "development"


settings = Settings()