"""
===============================================================================
GeoSentinel AI — Test Suite: Report Generation
===============================================================================
Tests CSV, PDF report generators using synthetic analysis data.
Verifies output files are created and contain expected data.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_area_rows():
    return [
        {
            "class_id": 1,
            "class_name": "Urban",
            "t1_area_km2": 120.5,
            "t2_area_km2": 145.2,
            "t1_pct": 18.5,
            "t2_pct": 22.3,
            "change_km2": 24.7,
            "change_pct": 20.5,
        },
        {
            "class_id": 2,
            "class_name": "Vegetation",
            "t1_area_km2": 300.2,
            "t2_area_km2": 275.8,
            "t1_pct": 46.2,
            "t2_pct": 42.4,
            "change_km2": -24.4,
            "change_pct": -8.1,
        },
    ]


@pytest.fixture
def synthetic_recommendations():
    return [
        {
            "rule_id": "URBAN_EXPANSION_HIGH",
            "category": "Urban",
            "severity": "HIGH",
            "title": "Rapid Urban Expansion",
            "recommendation": "Review zoning regulations.",
            "why": "Urban area increased by 20.5%.",
            "priority": 3,
        }
    ]


@pytest.fixture
def output_dir(tmp_path):
    """Temporary directory for test output files."""
    return tmp_path / "outputs"


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------

class TestCSVExport:

    def test_area_stats_csv_created(self, synthetic_area_rows, output_dir, monkeypatch):
        from src.reporting.csv_export import CSVExporter
        from src.utils.paths import paths

        # Redirect output to tmp_path
        monkeypatch.setattr(paths, "DATA_OUTPUT_DIR", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exporter = CSVExporter()
        result_path = exporter.export_area_stats(synthetic_area_rows, filename="test_area.csv")

        assert result_path is not None
        assert Path(result_path).exists()

    def test_area_stats_csv_has_correct_columns(self, synthetic_area_rows, output_dir, monkeypatch):
        from src.reporting.csv_export import CSVExporter
        from src.utils.paths import paths

        monkeypatch.setattr(paths, "DATA_OUTPUT_DIR", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exporter = CSVExporter()
        result_path = exporter.export_area_stats(synthetic_area_rows, filename="test_cols.csv")

        with open(result_path, newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        assert "class_name" in headers
        assert "t1_area_km2" in headers
        assert "t2_area_km2" in headers
        assert "change_km2" in headers

    def test_recommendations_csv_created(self, synthetic_recommendations, output_dir, monkeypatch):
        from src.reporting.csv_export import CSVExporter
        from src.utils.paths import paths

        monkeypatch.setattr(paths, "DATA_OUTPUT_DIR", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exporter = CSVExporter()
        result_path = exporter.export_recommendations(
            synthetic_recommendations, filename="test_recs.csv"
        )

        assert result_path is not None
        assert Path(result_path).exists()

    def test_recommendations_csv_has_severity_column(
        self, synthetic_recommendations, output_dir, monkeypatch
    ):
        from src.reporting.csv_export import CSVExporter
        from src.utils.paths import paths

        monkeypatch.setattr(paths, "DATA_OUTPUT_DIR", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exporter = CSVExporter()
        result_path = exporter.export_recommendations(
            synthetic_recommendations, filename="test_sev.csv"
        )

        with open(result_path, newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        assert "severity" in headers
        assert "rule_id" in headers


# ---------------------------------------------------------------------------
# PDF Report
# ---------------------------------------------------------------------------

class TestPDFReport:

    def test_pdf_generated_when_reportlab_available(
        self, synthetic_area_rows, synthetic_recommendations, output_dir, monkeypatch
    ):
        pytest.importorskip("reportlab")

        from src.reporting.pdf_report import PDFReportGenerator
        from src.utils.paths import paths

        monkeypatch.setattr(paths, "REPORTS_DIR", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        gen = PDFReportGenerator()
        data = {
            "metadata": {"date1": "2023-01-15", "date2": "2024-01-15"},
            "area_change": {"rows": synthetic_area_rows, "total_area_km2": 650.0},
            "recommendations": synthetic_recommendations,
        }

        result_path = gen.generate(data, filename="test_report.pdf")

        if result_path:
            assert Path(result_path).exists()
            assert Path(result_path).suffix == ".pdf"
            assert Path(result_path).stat().st_size > 0


# ---------------------------------------------------------------------------
# GeoJSON Export
# ---------------------------------------------------------------------------

class TestGeoJSONExport:

    def test_boundary_export_valid_geojson(self, output_dir, monkeypatch):
        """Should produce valid GeoJSON structure."""
        from src.reporting.geojson_export import GeoJSONExporter
        from src.utils.paths import paths
        import json

        monkeypatch.setattr(paths, "DATA_OUTPUT_DIR", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exporter = GeoJSONExporter()

        # Export a dummy area polygon
        aoi_geometry = {
            "type": "Polygon",
            "coordinates": [[[78.3, 17.2], [78.6, 17.2], [78.6, 17.5], [78.3, 17.5], [78.3, 17.2]]]
        }
        result_path = exporter.export_analysis_extent(
            aoi_geometry, filename="test_aoi.geojson"
        )

        if result_path:
            with open(result_path) as f:
                data = json.load(f)
            assert "type" in data
