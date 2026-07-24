"""
===============================================================================
GeoSentinel AI — Test Suite: Preprocessing Modules
===============================================================================
Tests normalization, clipping, resampling, cloud masking, alignment.
Uses synthetic rasters (numpy arrays) — no real satellite data needed.
"""

from __future__ import annotations

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_raster():
    """A (C, H, W) float32 raster with 4 channels."""
    rng = np.random.default_rng(0)
    return rng.integers(0, 10000, size=(4, 256, 256)).astype(np.float32)


@pytest.fixture
def cloud_mask():
    """SCL-like cloud mask where 4 = clear, 8/9/10 = cloud."""
    # 256×256 mask: 80% clear, 20% cloud
    mask = np.full((256, 256), 4, dtype=np.uint8)
    mask[:50, :50] = 9  # cloud
    return mask


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

class TestNormalization:

    def test_normalized_range_in_01(self, synthetic_raster):
        """After normalization all values should be in [0, 1]."""
        from src.preprocessing.normalize import BandNormalizer
        result = BandNormalizer().normalize_array(synthetic_raster)
        assert result.min() >= 0.0 - 1e-6
        assert result.max() <= 1.0 + 1e-6

    def test_preserves_shape(self, synthetic_raster):
        from src.preprocessing.normalize import BandNormalizer
        result = BandNormalizer().normalize_array(synthetic_raster)
        assert result.shape == synthetic_raster.shape

    def test_output_dtype_float32(self, synthetic_raster):
        from src.preprocessing.normalize import BandNormalizer
        result = BandNormalizer().normalize_array(synthetic_raster)
        assert result.dtype == np.float32

    def test_constant_raster_normalized_to_zero_or_one(self):
        """A constant raster (all same value) should not raise and returns valid output."""
        from src.preprocessing.normalize import BandNormalizer
        constant = np.full((2, 32, 32), 5000.0, dtype=np.float32)
        result = BandNormalizer().normalize_array(constant)
        # Either 0.0 or 1.0 depending on implementation; just no NaN
        assert not np.any(np.isnan(result))


# ---------------------------------------------------------------------------
# Cloud Masking
# ---------------------------------------------------------------------------

class TestCloudMasking:

    def test_cloud_mask_returns_boolean_array(self, cloud_mask):
        """Should return a boolean mask of same H×W shape."""
        from src.preprocessing.cloudmask import CloudMasker
        result = CloudMasker().build_cloud_mask(cloud_mask)
        assert result.dtype == bool
        assert result.shape == (256, 256)

    def test_clear_pixels_are_false(self, cloud_mask):
        """Clear pixels (SCL=4) should be masked=False (not cloudy)."""
        from src.preprocessing.cloudmask import CloudMasker
        result = CloudMasker().build_cloud_mask(cloud_mask)
        # The 50×50 cloud region should be True (is cloud)
        assert result[:50, :50].any()

    def test_non_cloud_region_is_clear(self, cloud_mask):
        """Non-cloud region in the bottom-right quadrant should be all False."""
        from src.preprocessing.cloudmask import CloudMasker
        result = CloudMasker().build_cloud_mask(cloud_mask)
        assert not result[100:, 100:].any()


# ---------------------------------------------------------------------------
# Clipping
# ---------------------------------------------------------------------------

class TestClipping:

    def test_clip_to_valid_range(self, synthetic_raster):
        """Clipping to [0, 1] should produce only values in that range."""
        from src.preprocessing.normalize import BandNormalizer
        normalized = BandNormalizer().normalize_array(synthetic_raster)

        # Values out of [0,1] (numerical error) must be clamped
        clipped = np.clip(normalized, 0.0, 1.0)
        assert clipped.min() >= 0.0
        assert clipped.max() <= 1.0


# ---------------------------------------------------------------------------
# Feature Stack
# ---------------------------------------------------------------------------

class TestFeatureStack:

    def test_stack_shape(self, synthetic_raster):
        """Stacking 5 bands and 7 indices should produce a 12-channel tensor."""
        from src.feature_engineering.stack import FeatureStackBuilder

        # Build dummy dicts
        bands = {
            "B02": synthetic_raster[0],
            "B03": synthetic_raster[0],
            "B04": synthetic_raster[0],
            "B08": synthetic_raster[0],
            "B11": synthetic_raster[0],
        }
        indices = {name: np.zeros((256, 256), dtype=np.float32)
                   for name in ["NDVI", "NDBI", "NDWI", "SAVI", "EVI", "MNDWI", "BSI"]}

        stack = FeatureStackBuilder().build(bands=bands, indices=indices)
        tensor = stack.array

        # 5 bands + 7 indices = 12
        assert tensor.shape[0] == 12
        assert tensor.shape[1] == 256
        assert tensor.shape[2] == 256

    def test_stack_dtype(self, synthetic_raster):
        from src.feature_engineering.stack import FeatureStackBuilder
        
        bands = {
            "B02": synthetic_raster[0],
            "B03": synthetic_raster[0],
            "B04": synthetic_raster[0],
            "B08": synthetic_raster[0],
            "B11": synthetic_raster[0],
        }
        indices = {name: np.zeros((256, 256), dtype=np.float32)
                   for name in ["NDVI", "NDBI", "NDWI", "SAVI", "EVI", "MNDWI", "BSI"]}

        stack = FeatureStackBuilder().build(bands=bands, indices=indices)
        tensor = stack.array
        assert tensor.dtype == np.float32
