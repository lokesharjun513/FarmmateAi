import pytest
from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4
from app.modules.identity.jwt import create_access_token

client = TestClient(app)

# Helper to create auth headers
def get_auth_headers(user_id: str):
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}

def test_crop_recommendation_requires_auth():
    # Test that /api/v1/crop-recommendation requires authentication
    response = client.post("/api/v1/crop-recommendation", json={"farm_id": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 401

def test_crop_season_creation_requires_auth():
    # Test that creating a crop season requires authentication
    response = client.post("/api/v1/crop-seasons", json={
        "farm_id": "00000000-0000-0000-0000-000000000000",
        "crop_name": "Wheat",
        "crop_variety": "Hybrid",
        "season": "Rabi",
        "year": 2026,
        "sowing_date": "2026-11-01",
        "expected_harvest_date": "2027-03-01",
        "land_area": 1.0,
        "land_unit": "hectares"
    })
    assert response.status_code == 401
