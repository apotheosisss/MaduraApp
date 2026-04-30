import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScanEntity(Base):
    __tablename__ = "scans"

    scan_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_token: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    fruit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    maturity_label: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox: Mapped[list] = mapped_column(JSON, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(255), nullable=False)
    color_code: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
