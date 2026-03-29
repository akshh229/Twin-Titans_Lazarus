"""Integration tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "lazarus-backend"

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestPatientEndpoints:
    @patch("app.api.patients.get_db")
    def test_list_patients(self, mock_get_db, client):
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result._mapping = {
            "patient_id": "test-uuid",
            "patient_raw_id": "P00001",
            "parity_flag": "even",
            "name": "Test Patient",
            "age": 45,
            "ward": "ICU-1",
            "last_bpm": 72,
            "last_oxygen": 98,
            "last_vitals_timestamp": None,
            "quality_flag": "good",
            "prescription_count": 3,
            "has_active_alert": False,
        }
        mock_db.execute.return_value = [mock_result]
        mock_get_db.return_value = mock_db

        response = client.get("/api/patients")
        assert response.status_code == 200


class TestAlertEndpoints:
    @patch("app.api.alerts.get_db")
    def test_list_alerts(self, mock_get_db, client):
        mock_db = MagicMock()
        mock_db.execute.return_value = []
        mock_get_db.return_value = mock_db

        response = client.get("/api/alerts")
        assert response.status_code == 200
        assert response.json() == []
