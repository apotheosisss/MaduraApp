import io

import numpy as np
from PIL import Image

from app.core.config import settings
from app.schemas.scan_result import ScanResult

CLASS_MAP: dict[int, tuple[str, str]] = {
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

COLOR_MAP: dict[str, str] = {
    "INMADURO": "green",
    "OPTIMO": "yellow",
    "SOBRE_MADURO": "red",
}

RECOMMENDATION_MAP: dict[tuple[str, str], str] = {
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

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB


class InferenceService:
    def validate_image(self, image_bytes: bytes) -> bool:
        if len(image_bytes) > MAX_IMAGE_BYTES:
            return False
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
            return True
        except Exception:
            return False

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((640, 640), Image.LANCZOS)
        return np.array(img)

    def postprocess(self, results: list) -> ScanResult | None:
        best_box = None
        best_conf = settings.CONFIDENCE_THRESHOLD
        best_class_id = -1

        for result in results:
            if result.boxes is None or len(result.boxes) == 0:
                continue
            for box in result.boxes:
                conf = float(box.conf[0])
                class_id = int(box.cls[0])
                if conf >= best_conf and class_id in CLASS_MAP:
                    best_conf = conf
                    best_box = box
                    best_class_id = class_id

        if best_box is None:
            return None

        fruit_type, maturity_label = CLASS_MAP[best_class_id]
        bbox = [round(v, 2) for v in best_box.xyxy[0].tolist()]

        return ScanResult(
            fruit_type=fruit_type,
            maturity_label=maturity_label,
            confidence=round(best_conf, 4),
            bbox=bbox,
            recommendation=RECOMMENDATION_MAP[(fruit_type, maturity_label)],
            color_code=COLOR_MAP[maturity_label],
        )

    def run(self, image_bytes: bytes, model) -> ScanResult | None:
        image_array = self.preprocess(image_bytes)
        results = model.predict(image_array)
        return self.postprocess(results)
