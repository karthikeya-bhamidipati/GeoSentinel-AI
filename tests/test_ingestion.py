"""
===============================================================================
GeoSentinel AI — Test Suite: AOI Geometry and Ingestion
===============================================================================
Tests AOI parsing, geometry validation, and boundary checking.
Mocks the BoundaryManager so these tests run without the GeoJSON file.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from shapely.geometry import Polygon, shape


# ---------------------------------------------------------------------------
# AOI Geometry tests
# ---------------------------------------------------------------------------

class TestAOIGeometry:

    def test_aoi_from_valid_geojson(self):
        """Should parse a valid Polygon GeoJSON without error."""
        from src.eo.aoi.geometry import AOI

        geojson = {
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

        aoi = AOI.from_geojson(geojson)
        assert aoi is not None
        assert not aoi.geometry.is_empty
        assert aoi.geometry.is_valid

    def test_aoi_area_positive(self):
        """A valid polygon must have positive area."""
        from src.eo.aoi.geometry import AOI

        geojson = {
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

        aoi = AOI.from_geojson(geojson)
        assert aoi.area_sqkm > 0.0

    def test_aoi_bounds_are_correct(self):
        """AOI bounds should match the input coordinates."""
        from src.eo.aoi.geometry import AOI

        geojson = {
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

        aoi = AOI.from_geojson(geojson)
        minx, miny, maxx, maxy = aoi.geometry.bounds
        assert abs(minx - 78.3) < 0.001
        assert abs(miny - 17.2) < 0.001
        assert abs(maxx - 78.6) < 0.001
        assert abs(maxy - 17.5) < 0.001


# ---------------------------------------------------------------------------
# AOI Validator tests
# ---------------------------------------------------------------------------

class TestAOIValidator:

    def _make_aoi(self, coords=None):
        from src.eo.aoi.geometry import AOI
        coords = coords or [
            [78.3, 17.2], [78.6, 17.2], [78.6, 17.5],
            [78.3, 17.5], [78.3, 17.2],
        ]
        return AOI.from_geojson({"type": "Polygon", "coordinates": [coords]})

    def test_validate_geometry_valid(self):
        from src.eo.aoi.validator import AOIValidator
        validator = AOIValidator()
        aoi = self._make_aoi()
        # Should not raise
        validator.validate_geometry(aoi)

    def test_validate_boundary_inside_hmr(self):
        """AOI inside HMR — boundary check should pass."""
        from src.eo.aoi.validator import AOIValidator

        mock_boundary = MagicMock()
        mock_boundary.contains.return_value = True

        with patch("src.eo.aoi.validator.get_boundary", return_value=mock_boundary):
            validator = AOIValidator()
            aoi = self._make_aoi()
            validator.validate_boundary(aoi)  # Should not raise

        mock_boundary.contains.assert_called_once_with(aoi.geometry)

    def test_validate_boundary_outside_hmr_raises(self):
        """AOI outside HMR — should raise AOIOutsideBoundaryError."""
        from src.eo.aoi.validator import AOIValidator
        from src.eo.exceptions import AOIOutsideBoundaryError

        mock_boundary = MagicMock()
        mock_boundary.contains.return_value = False

        with patch("src.eo.aoi.validator.get_boundary", return_value=mock_boundary):
            validator = AOIValidator()
            aoi = self._make_aoi()

            with pytest.raises(AOIOutsideBoundaryError):
                validator.validate_boundary(aoi)

    def test_validate_area_within_limit(self):
        from src.eo.aoi.validator import AOIValidator
        validator = AOIValidator(max_area_sqkm=5000.0)
        aoi = self._make_aoi()
        # A small AOI should not raise
        validator.validate_area(aoi)

    def test_validate_area_too_large_raises(self):
        """Large AOI should raise AOITooLargeError."""
        from src.eo.aoi.validator import AOIValidator
        from src.eo.exceptions import AOITooLargeError

        validator = AOIValidator(max_area_sqkm=0.001)  # Tiny limit
        aoi = self._make_aoi()

        with pytest.raises(AOITooLargeError):
            validator.validate_area(aoi)


# ---------------------------------------------------------------------------
# BoundaryManager lazy init
# ---------------------------------------------------------------------------

class TestBoundaryLazyInit:

    def test_boundary_module_imports_without_file(self):
        """Importing boundary.py should NOT raise even if boundary file is absent."""
        # The module has already been imported; just verify get_boundary can be imported
        from src.eo.aoi.boundary import get_boundary
        assert callable(get_boundary)

    def test_get_boundary_is_callable(self):
        from src.eo.aoi.boundary import get_boundary
        # Should be importable without error
        assert get_boundary is not None
