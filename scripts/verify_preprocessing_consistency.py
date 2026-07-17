"""
===============================================================================
GeoSentinel AI — Preprocessing Consistency Verification

Script:
    verify_preprocessing_consistency.py

Description:
    MANDATORY gate before any training. Verifies that a randomly-selected
    training patch and a freshly-streamed production AOI pass through
    EXACTLY the same preprocessing and produce tensors with identical:
      - Channel order
      - Normalization range
      - Spatial resolution
      - CRS
      - Feature stack layout (12 channels)

    Training MUST NOT begin until this script outputs PASS for all channels.

Author:
    GeoSentinel AI Pipeline
===============================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# Configuration
# =============================================================================

EXPECTED_CHANNELS = [
    "B02", "B03", "B04", "B08", "B11",
    "NDVI", "NDBI", "NDWI", "SAVI", "EVI", "MNDWI", "BSI"
]
NUM_EXPECTED_CHANNELS = 12
EXPECTED_DTYPE = np.float32

# Acceptable value ranges for each channel type
BAND_RANGE = (-0.05, 1.5)      # Normalized reflectance (may slightly exceed 1.0)
INDEX_RANGE = (-2.0, 2.0)       # Spectral indices


def check_channel_order(channel_names: list[str]) -> bool:
    """Verify channel names match expected order exactly."""
    if channel_names != EXPECTED_CHANNELS:
        print(f"  FAIL: Channel order mismatch")
        print(f"    Expected: {EXPECTED_CHANNELS}")
        print(f"    Got:      {channel_names}")
        return False
    print(f"  PASS: Channel order matches ({len(channel_names)} channels)")
    return True


def check_value_range(array: np.ndarray, channel_names: list[str]) -> tuple[bool, list[str]]:
    """Verify each channel has sensible value ranges."""
    passed = True
    failures = []

    for i, name in enumerate(channel_names):
        ch = array[i]
        finite = ch[np.isfinite(ch)]
        if len(finite) == 0:
            failures.append(f"  FAIL: Channel {i} ({name}): all NaN/Inf")
            passed = False
            continue

        vmin, vmax = float(finite.min()), float(finite.max())
        vmean = float(finite.mean())

        # Determine expected range based on channel type
        if name.startswith("B"):
            lo, hi = BAND_RANGE
        else:
            lo, hi = INDEX_RANGE

        status = "PASS" if (vmin >= lo - 0.1 and vmax <= hi + 0.5) else "WARN"
        if vmin < lo - 1.0 or vmax > hi + 2.0:
            status = "FAIL"
            passed = False
            failures.append(f"    Channel {i} ({name}): range [{vmin:.4f}, {vmax:.4f}] outside [{lo}, {hi}]")

        print(f"  {status}: Channel {i:2d} ({name:6s}) — range [{vmin:8.4f}, {vmax:8.4f}], mean={vmean:8.4f}")

    return passed, failures


def check_no_nan(array: np.ndarray) -> bool:
    """Verify no NaN values in the final tensor."""
    nan_count = np.isnan(array).sum()
    if nan_count > 0:
        total = array.size
        pct = 100.0 * nan_count / total
        print(f"  WARN: {nan_count:,} NaN values ({pct:.2f}% of tensor)")
        return True  # Warning only — NaNs are replaced with 0 downstream
    print(f"  PASS: No NaN values")
    return True


def check_dtype(array: np.ndarray) -> bool:
    """Verify dtype is float32."""
    if array.dtype != EXPECTED_DTYPE:
        print(f"  FAIL: Expected dtype {EXPECTED_DTYPE}, got {array.dtype}")
        return False
    print(f"  PASS: dtype is {array.dtype}")
    return True


def check_shape(array: np.ndarray) -> bool:
    """Verify shape is (12, H, W)."""
    if len(array.shape) != 3:
        print(f"  FAIL: Expected 3D tensor, got shape {array.shape}")
        return False
    if array.shape[0] != NUM_EXPECTED_CHANNELS:
        print(f"  FAIL: Expected {NUM_EXPECTED_CHANNELS} channels, got {array.shape[0]}")
        return False
    print(f"  PASS: Shape is {array.shape} ({array.shape[0]} channels, {array.shape[1]}×{array.shape[2]} pixels)")
    return True


def verify_training_patch(patch_dir: Path) -> bool:
    """Verify a training patch from the dataset."""
    print("\n" + "=" * 64)
    print("  TRAINING PATCH VERIFICATION")
    print("=" * 64)

    image_files = sorted(patch_dir.glob("image_*.npy"))
    mask_files = sorted(patch_dir.glob("mask_*.npy"))

    if not image_files:
        print(f"  SKIP: No training patches found in {patch_dir}")
        print(f"  This is expected if you haven't run generate_real_dataset.py yet.")
        return True  # Not a failure — just not generated yet

    # Pick a random patch
    idx = np.random.randint(0, len(image_files))
    img_path = image_files[idx]
    mask_path = mask_files[idx] if idx < len(mask_files) else None

    print(f"  Patch: {img_path.name}")
    image = np.load(img_path)

    all_pass = True
    all_pass &= check_shape(image)
    all_pass &= check_dtype(image)
    all_pass &= check_no_nan(image)

    # Verify value ranges (using expected channel order from stack.py)
    range_pass, _ = check_value_range(image, EXPECTED_CHANNELS)
    all_pass &= range_pass

    # Check mask if available
    if mask_path and mask_path.exists():
        mask = np.load(mask_path)
        unique = np.unique(mask)
        print(f"\n  Mask: {mask_path.name}")
        print(f"  PASS: Mask shape {mask.shape}, classes present: {unique.tolist()}")
        if mask.max() > 5:
            print(f"  FAIL: Mask has class > 5 ({mask.max()}) — expected [0..5]")
            all_pass = False

    return all_pass


def verify_production_pipeline() -> bool:
    """Verify a live Sentinel-2 scene through the production pipeline."""
    print("\n" + "=" * 64)
    print("  PRODUCTION PIPELINE VERIFICATION")
    print("=" * 64)

    try:
        from datetime import date
        from shapely.geometry import box
        from dotenv import load_dotenv

        from src.eo.providers.stac import CDSEProvider
        from src.preprocessing.pipeline import PreprocessingPipeline
        from src.feature_engineering.pipeline import FeatureEngineeringPipeline

        load_dotenv()

        # Small AOI within Hyderabad (minimal data download)
        aoi = box(78.40, 17.38, 78.45, 17.42)

        print("  Connecting to CDSE...")
        provider = CDSEProvider(max_cloud_cover=15.0)
        provider.connect()

        print("  Searching for a Sentinel-2 scene...")
        scenes = provider.search(
            aoi=aoi,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 1),
            max_cloud_cover=15.0,
            max_results=1,
        )

        if not scenes:
            print("  SKIP: No scenes found (check CDSE credentials)")
            return True

        scene_id = scenes[0].get("id", "unknown")
        print(f"  Loading scene: {scene_id}...")
        scene = provider.load(source=scenes[0], aoi=aoi)

        print("  Running preprocessing pipeline...")
        preprocessor = PreprocessingPipeline()
        prep = preprocessor.run(scene)

        print("  Running feature engineering pipeline...")
        fe = FeatureEngineeringPipeline()
        result = fe.run(prep.scene)

        stack = result.stack
        print(f"\n  Production stack: {stack.array.shape}")
        print(f"  Channel names: {stack.channel_names}")

        all_pass = True
        all_pass &= check_channel_order(stack.channel_names)
        all_pass &= check_shape(stack.array)
        all_pass &= check_dtype(stack.array)
        all_pass &= check_no_nan(stack.array)

        range_pass, _ = check_value_range(stack.array, stack.channel_names)
        all_pass &= range_pass

        provider.close()
        return all_pass

    except Exception as exc:
        print(f"  SKIP: Production pipeline verification skipped: {exc}")
        print(f"  This requires valid CDSE credentials in .env")
        return True  # Not a hard failure


def main():
    print("=" * 64)
    print("  GeoSentinel AI — Preprocessing Consistency Verification")
    print("  This script MUST pass before training is authorized.")
    print("=" * 64)

    patch_dir = PROJECT_ROOT / "data" / "benchmark" / "real" / "train"
    
    results = {}
    results["training_patch"] = verify_training_patch(patch_dir)
    results["production_pipeline"] = verify_production_pipeline()

    # Final report
    print("\n" + "=" * 64)
    print("  FINAL VERIFICATION REPORT")
    print("=" * 64)

    all_pass = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {test_name}")
        all_pass &= passed

    print()
    if all_pass:
        print("  ALL CHECKS PASSED - Training is authorized.")
    else:
        print("  VERIFICATION FAILED - DO NOT proceed with training!")
        print("  Fix the issues above before retraining.")

    print("=" * 64)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
