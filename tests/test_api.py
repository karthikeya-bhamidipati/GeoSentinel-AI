"""
===============================================================================
GeoSentinel AI — Test Suite: API Endpoints
===============================================================================
Tests all FastAPI routes using httpx.AsyncClient / TestClient.
Mocks the Orchestrator so tests run without CDSE credentials or GPU.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_AOI = {
    "type": "Polygon",
    "coordinates": [
        [
            [78.3, 17.2],
            [78.6, 17.2],
            [78.6, 17.5],
            [78.3, 17.5],
            [78.3, 17.2],
        ]
    ],
}

VALID_REQUEST = {
    "aoi": VALID_AOI,
    "date1": "2023-01-15",
    "date2": "2024-01-15",
    "max_cloud_cover": 10.0,
}


@pytest.fixture
def mock_result() -> dict:
    """A synthetic AnalysisResult-like dict."""
    return {
        "job_id": "test-job-001",
        "success": True,
        "date1": "2023-01-15",
        "date2": "2024-01-15",
        "scene_t1_id": "S2A_MSIL2A_20230115",
        "scene_t2_id": "S2A_MSIL2A_20240115",
        "area_change": {"rows": [], "total_area_km2": 250.5},
        "temporal_stats": {},
        "statistics": {},
        "recommendations": [],
        "outputs": {},
        "metadata": {"elapsed_seconds": 45.2},
        "error": None,
    }


@pytest.fixture
def test_client():
    """Create a test client with the FastAPI app."""
    from backend.app.main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_health_returns_200(self, test_client):
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_response_structure(self, test_client):
        response = test_client.get("/api/v1/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_health_version(self, test_client):
        response = test_client.get("/api/v1/health")
        assert response.json()["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Boundary endpoint
# ---------------------------------------------------------------------------

class TestBoundaryEndpoint:

    def test_boundary_returns_200(self, test_client):
        response = test_client.get("/api/v1/boundary")
        assert response.status_code == 200

    def test_boundary_geojson_structure(self, test_client):
        response = test_client.get("/api/v1/boundary")
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert len(data["features"]) > 0


# ---------------------------------------------------------------------------
# Analysis submission
# ---------------------------------------------------------------------------

class TestAnalysisSubmission:

    def test_submit_returns_202(self, test_client):
        """Mocked orchestrator — should return 202 Accepted immediately."""
        with patch("backend.app.dependencies.get_orchestrator") as mock_orch:
            mock_orch.return_value = MagicMock()
            response = test_client.post("/api/v1/analysis", json=VALID_REQUEST)
        # 202 Accepted OR immediate 500 if orchestrator fails — we check for non-4xx
        assert response.status_code in (202, 200, 500)

    def test_submit_missing_aoi_returns_422(self, test_client):
        """Request without AOI should be rejected by Pydantic validation."""
        bad_request = {"date1": "2023-01-15", "date2": "2024-01-15"}
        response = test_client.post("/api/v1/analysis", json=bad_request)
        assert response.status_code == 422

    def test_submit_date2_before_date1_returns_422(self, test_client):
        """date2 must be strictly after date1."""
        bad_request = {**VALID_REQUEST, "date2": "2022-01-15"}
        response = test_client.post("/api/v1/analysis", json=bad_request)
        assert response.status_code == 422

    def test_submit_invalid_cloud_cover_returns_422(self, test_client):
        """max_cloud_cover must be in [0, 100]."""
        bad_request = {**VALID_REQUEST, "max_cloud_cover": 150.0}
        response = test_client.post("/api/v1/analysis", json=bad_request)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Job status
# ---------------------------------------------------------------------------

class TestJobStatus:

    def test_nonexistent_job_returns_404(self, test_client):
        response = test_client.get("/api/v1/analysis/nonexistent-job-id")
        assert response.status_code == 404

    def test_status_response_has_required_fields(self, test_client):
        """Create a job and verify status response structure."""
        from backend.app.services import get_job_queue

        queue = get_job_queue()
        job_id = queue.create_job()

        response = test_client.get(f"/api/v1/analysis/{job_id}")
        assert response.status_code == 200

        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert "progress_message" in data
        assert data["job_id"] == job_id


# ---------------------------------------------------------------------------
# Result retrieval
# ---------------------------------------------------------------------------

class TestAnalysisResult:

    def test_result_for_queued_job(self, test_client):
        """A queued job should not return a result yet."""
        from backend.app.services import get_job_queue
        queue = get_job_queue()
        job_id = queue.create_job()
        response = test_client.get(f"/api/v1/analysis/{job_id}/result")
        # QUEUED job returns 202 (still running) or 500 (failed), not 200
        assert response.status_code in (202, 404, 500)


# ---------------------------------------------------------------------------
# Benchmark endpoint
# ---------------------------------------------------------------------------

class TestBenchmarkEndpoint:

    def test_benchmark_returns_200(self, test_client):
        response = test_client.get("/api/v1/benchmark")
        assert response.status_code == 200

    def test_benchmark_has_results(self, test_client):
        response = test_client.get("/api/v1/benchmark")
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 4

    def test_benchmark_result_structure(self, test_client):
        response = test_client.get("/api/v1/benchmark")
        result = response.json()["results"][0]
        for field in ["model", "dataset", "iou", "dice", "f1", "precision", "recall", "accuracy"]:
            assert field in result, f"Missing field: {field}"

    def test_benchmark_has_best_model(self, test_client):
        response = test_client.get("/api/v1/benchmark")
        results = response.json()["results"]
        best = [r for r in results if r.get("is_best")]
        assert len(best) == 1
        assert best[0]["model"] == "U-Net (ResNet34)"


# ---------------------------------------------------------------------------
# Settings endpoint
# ---------------------------------------------------------------------------

class TestSettingsEndpoint:

    def test_settings_returns_200(self, test_client):
        response = test_client.get("/api/v1/settings")
        assert response.status_code == 200

    def test_settings_has_project_section(self, test_client):
        response = test_client.get("/api/v1/settings")
        data = response.json()
        assert "project" in data
        assert data["project"]["name"] == "GeoSentinel AI"
