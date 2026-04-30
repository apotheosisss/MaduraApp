from unittest.mock import patch

from httpx import AsyncClient

from app.schemas.scan_result import ScanResult
from tests.conftest import make_jpeg_bytes

MOCK_SCAN = ScanResult(
    fruit_type="mango",
    maturity_label="OPTIMO",
    confidence=0.92,
    bbox=[10.0, 20.0, 300.0, 400.0],
    recommendation="Consumir hoy, refrigerar si no lo consumes",
    color_code="yellow",
)


async def test_health(client: AsyncClient):
    r = await client.get("/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["model"] == "yolo26n"
    assert "model_loaded" in data


async def test_predict_unsupported_format(client: AsyncClient):
    r = await client.post(
        "/v1/predict",
        files={"file": ("img.gif", b"GIF89a", "image/gif")},
    )
    assert r.status_code == 400
    assert "no soportado" in r.json()["detail"]


async def test_predict_no_detection(client: AsyncClient):
    with patch("app.routers.predict.inference_svc.run", return_value=None):
        r = await client.post(
            "/v1/predict",
            files={"file": ("fruit.jpg", make_jpeg_bytes(), "image/jpeg")},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert "error" in data


async def test_predict_with_detection(client: AsyncClient):
    with patch("app.routers.predict.inference_svc.run", return_value=MOCK_SCAN):
        r = await client.post(
            "/v1/predict",
            files={"file": ("mango.jpg", make_jpeg_bytes((255, 200, 0)), "image/jpeg")},
            headers={"Authorization": "Bearer test_token"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    result = data["data"]
    assert result["fruit_type"] == "mango"
    assert result["maturity_label"] == "OPTIMO"
    assert result["color_code"] == "yellow"
    assert isinstance(result["confidence"], float)
    assert len(result["bbox"]) == 4


async def test_predict_png_accepted(client: AsyncClient):
    import io
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (50, 50), (0, 128, 0)).save(buf, format="PNG")
    with patch("app.routers.predict.inference_svc.run", return_value=MOCK_SCAN):
        r = await client.post(
            "/v1/predict",
            files={"file": ("img.png", buf.getvalue(), "image/png")},
        )
    assert r.status_code == 200
