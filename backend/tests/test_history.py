from unittest.mock import patch

from httpx import AsyncClient

from app.schemas.scan_result import ScanResult
from tests.conftest import make_jpeg_bytes

MOCK_SCAN = ScanResult(
    fruit_type="platano",
    maturity_label="INMADURO",
    confidence=0.78,
    bbox=[5.0, 10.0, 200.0, 300.0],
    recommendation="Madurar en bolsa de papel 2-3 días",
    color_code="green",
)


async def test_history_empty(client: AsyncClient):
    r = await client.get("/v1/history", headers={"Authorization": "Bearer no_scans_token"})
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 50
    assert data["offset"] == 0


async def test_history_after_predict(client: AsyncClient):
    token = "Bearer history_test_token"

    with patch("app.routers.predict.inference_svc.run", return_value=MOCK_SCAN):
        await client.post(
            "/v1/predict",
            files={"file": ("banana.jpg", make_jpeg_bytes((200, 230, 100)), "image/jpeg")},
            headers={"Authorization": token},
        )

    r = await client.get("/v1/history", headers={"Authorization": token})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    item = data["items"][0]
    assert item["fruit_type"] == "platano"
    assert item["maturity_label"] == "INMADURO"


async def test_history_pagination(client: AsyncClient):
    r = await client.get("/v1/history?limit=5&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert len(data["items"]) <= 5


async def test_history_limit_validation(client: AsyncClient):
    r = await client.get("/v1/history?limit=200")
    assert r.status_code == 422
