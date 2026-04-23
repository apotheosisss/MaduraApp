from pydantic import BaseModel
from typing import Optional

class ScanResult(BaseModel):
    fruit_type: str
    maturity_label: str          # INMADURO | OPTIMO | SOBRE_MADURO
    confidence: float
    bbox: list[float]
    recommendation: str
    color_code: str              # green | yellow | red

    def to_json(self) -> dict:
        return self.model_dump()

class PredictResponse(BaseModel):
    success: bool
    data: Optional[ScanResult] = None
    error: Optional[str] = None