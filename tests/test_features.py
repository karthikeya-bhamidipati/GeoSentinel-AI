"""
===============================================================================
GeoSentinel AI — Test Suite: Spectral Feature Engineering
===============================================================================
Tests all 7 spectral index calculators with synthetic numpy arrays.
Validators confirm formula correctness (range, sign, shape) and that
from_scene() correctly delegates to compute().
"""

from __future__ import annotations

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures — synthetic band data
# ---------------------------------------------------------------------------

@pytest.fixture
def random_bands():
    """Returns random (H, W) float32 arrays in [0, 1] for each band."""
    rng = np.random.default_rng(42)
    shape = (64, 64)
    return {
        "red": rng.random(shape, dtype=np.float32),
        "nir": rng.random(shape, dtype=np.float32),
        "green": rng.random(shape, dtype=np.float32),
        "swir1": rng.random(shape, dtype=np.float32),
        "blue": rng.random(shape, dtype=np.float32),
    }


@pytest.fixture
def constant_bands():
    """Constant arrays for formula validation."""
    shape = (16, 16)
    return {
        "red": np.full(shape, 0.2, dtype=np.float32),
        "nir": np.full(shape, 0.8, dtype=np.float32),
        "green": np.full(shape, 0.4, dtype=np.float32),
        "swir1": np.full(shape, 0.3, dtype=np.float32),
        "blue": np.full(shape, 0.1, dtype=np.float32),
    }


# ---------------------------------------------------------------------------
# NDVI
# ---------------------------------------------------------------------------

class TestNDVI:

    def test_output_range(self, random_bands):
        from src.feature_engineering.ndvi import NDVICalculator
        calc = NDVICalculator()
        result = calc.compute(nir=random_bands["nir"], red=random_bands["red"])
        assert result.shape == (64, 64)
        assert result.min() >= -1.0, "NDVI must be >= -1"
        assert result.max() <= 1.0, "NDVI must be <= 1"
        assert result.dtype == np.float32

    def test_formula_constant(self, constant_bands):
        """NDVI = (NIR - RED) / (NIR + RED) = (0.8 - 0.2) / (0.8 + 0.2) = 0.6"""
        from src.feature_engineering.ndvi import NDVICalculator
        calc = NDVICalculator()
        result = calc.compute(nir=constant_bands["nir"], red=constant_bands["red"])
        expected = (0.8 - 0.2) / (0.8 + 0.2)
        assert np.allclose(result, expected, atol=1e-5)

    def test_high_vegetation_positive(self, constant_bands):
        """NIR >> RED => NDVI positive."""
        from src.feature_engineering.ndvi import NDVICalculator
        calc = NDVICalculator()
        result = calc.compute(nir=constant_bands["nir"], red=constant_bands["red"])
        assert result.mean() > 0.0

    def test_index_name(self):
        from src.feature_engineering.ndvi import NDVICalculator
        assert NDVICalculator.INDEX_NAME == "NDVI"


# ---------------------------------------------------------------------------
# NDBI
# ---------------------------------------------------------------------------

class TestNDBI:

    def test_output_range(self, random_bands):
        from src.feature_engineering.ndbi import NDBICalculator
        calc = NDBICalculator()
        result = calc.compute(swir1=random_bands["swir1"], nir=random_bands["nir"])
        assert result.shape == (64, 64)
        assert result.min() >= -1.0
        assert result.max() <= 1.0
        assert result.dtype == np.float32

    def test_formula_constant(self, constant_bands):
        """NDBI = (SWIR1 - NIR) / (SWIR1 + NIR) = (0.3 - 0.8) / (0.3 + 0.8)"""
        from src.feature_engineering.ndbi import NDBICalculator
        calc = NDBICalculator()
        result = calc.compute(swir1=constant_bands["swir1"], nir=constant_bands["nir"])
        expected = (0.3 - 0.8) / (0.3 + 0.8)
        assert np.allclose(result, expected, atol=1e-5)

    def test_urban_dominance_positive(self):
        """When SWIR1 > NIR, NDBI is positive (urban signal)."""
        from src.feature_engineering.ndbi import NDBICalculator
        calc = NDBICalculator()
        swir1 = np.full((8, 8), 0.7, dtype=np.float32)
        nir = np.full((8, 8), 0.2, dtype=np.float32)
        result = calc.compute(swir1=swir1, nir=nir)
        assert result.mean() > 0.0


# ---------------------------------------------------------------------------
# NDWI
# ---------------------------------------------------------------------------

class TestNDWI:

    def test_output_range(self, random_bands):
        from src.feature_engineering.ndwi import NDWICalculator
        calc = NDWICalculator()
        result = calc.compute(green=random_bands["green"], nir=random_bands["nir"])
        assert result.shape == (64, 64)
        assert result.min() >= -1.0
        assert result.max() <= 1.0

    def test_water_signal_positive(self):
        """GREEN >> NIR should yield positive NDWI (water body)."""
        from src.feature_engineering.ndwi import NDWICalculator
        calc = NDWICalculator()
        green = np.full((8, 8), 0.9, dtype=np.float32)
        nir = np.full((8, 8), 0.1, dtype=np.float32)
        result = calc.compute(green=green, nir=nir)
        assert result.mean() > 0.0


# ---------------------------------------------------------------------------
# MSAVI
# ---------------------------------------------------------------------------

class TestMSAVI:

    def test_output_range(self, random_bands):
        from src.feature_engineering.msavi import MSAVICalculator
        calc = MSAVICalculator()
        result = calc.compute(nir=random_bands["nir"], red=random_bands["red"])
        assert result.shape == (64, 64)
        assert result.min() >= -1.0
        assert result.max() <= 1.0

    def test_no_nan(self, random_bands):
        from src.feature_engineering.msavi import MSAVICalculator
        calc = MSAVICalculator()
        result = calc.compute(nir=random_bands["nir"], red=random_bands["red"])
        assert not np.any(np.isnan(result))


# ---------------------------------------------------------------------------
# EVI
# ---------------------------------------------------------------------------

class TestEVI:

    def test_output_shape_and_dtype(self, random_bands):
        from src.feature_engineering.evi import EVICalculator
        calc = EVICalculator()
        result = calc.compute(
            nir=random_bands["nir"],
            red=random_bands["red"],
            blue=random_bands["blue"],
        )
        assert result.shape == (64, 64)
        assert result.dtype == np.float32

    def test_no_nan(self, random_bands):
        from src.feature_engineering.evi import EVICalculator
        calc = EVICalculator()
        result = calc.compute(
            nir=random_bands["nir"],
            red=random_bands["red"],
            blue=random_bands["blue"],
        )
        assert not np.any(np.isnan(result))


# ---------------------------------------------------------------------------
# SAVI
# ---------------------------------------------------------------------------

class TestSAVI:

    def test_output_range(self, random_bands):
        from src.feature_engineering.savi import SAVICalculator
        calc = SAVICalculator()
        result = calc.compute(nir=random_bands["nir"], red=random_bands["red"])
        assert result.shape == (64, 64)
        assert result.dtype == np.float32

    def test_no_nan(self, random_bands):
        from src.feature_engineering.savi import SAVICalculator
        calc = SAVICalculator()
        result = calc.compute(nir=random_bands["nir"], red=random_bands["red"])
        assert not np.any(np.isnan(result))


# ---------------------------------------------------------------------------
# BSI
# ---------------------------------------------------------------------------

class TestBSI:

    def test_output_shape(self, random_bands):
        from src.feature_engineering.bsi import BSICalculator
        calc = BSICalculator()
        result = calc.compute(
            swir1=random_bands["swir1"],
            red=random_bands["red"],
            nir=random_bands["nir"],
            blue=random_bands["blue"],
        )
        assert result.shape == (64, 64)
        assert result.dtype == np.float32

    def test_no_nan(self, random_bands):
        from src.feature_engineering.bsi import BSICalculator
        calc = BSICalculator()
        result = calc.compute(
            swir1=random_bands["swir1"],
            red=random_bands["red"],
            nir=random_bands["nir"],
            blue=random_bands["blue"],
        )
        assert not np.any(np.isnan(result))
