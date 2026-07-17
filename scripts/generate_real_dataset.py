"""
GeoSentinel AI - Generate Real Dataset (Hyderabad)
Downloads real Sentinel-2 imagery via STAC, chunks it, and uses ESA WorldCover
as the ground-truth mask for DeepLabV3+ Semantic Segmentation training.
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from datetime import date
from shapely.geometry import shape
from dotenv import load_dotenv
import pystac_client

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.eo.providers.stac import CDSEProvider
from src.feature_engineering.pipeline import FeatureEngineeringPipeline

EXPECTED_CHANNELS = [
    "B02", "B03", "B04", "B08", "B11",
    "NDVI", "NDBI", "NDWI", "SAVI", "EVI", "MNDWI", "BSI"
]

# ESA WorldCover to GeoSentinel Class Mapping
# GeoSentinel: 0=Background, 1=Urban, 2=Vegetation, 3=Water, 4=Barren, 5=Agriculture
ESA_MAPPING = {
    0: 0,    # No data -> Background
    10: 2,   # Trees -> Vegetation
    20: 2,   # Shrubland -> Vegetation
    30: 2,   # Grassland -> Vegetation
    40: 5,   # Cropland -> Agriculture
    50: 1,   # Built-up -> Urban
    60: 4,   # Bare -> Barren
    70: 4,   # Snow/Ice -> Barren
    80: 3,   # Water -> Water
    90: 3,   # Wetland -> Water
    95: 2,   # Mangroves -> Vegetation
    100: 2,  # Moss -> Vegetation
}

# Vectorized mapping function
def map_esa_to_geosentinel(esa_mask: np.ndarray) -> np.ndarray:
    out_mask = np.zeros_like(esa_mask, dtype=np.int64)
    for esa_val, geo_val in ESA_MAPPING.items():
        out_mask[esa_mask == esa_val] = geo_val
    return out_mask

def get_hyderabad_aoi():
    return {
        "type": "Polygon",
        "coordinates": [[
            [78.3, 17.3],
            [78.6, 17.3],
            [78.6, 17.5],
            [78.3, 17.5],
            [78.3, 17.3]
        ]]
    }

def fetch_esa_worldcover(aoi_geom, target_shape, src_transform, src_crs):
    """Fetch the ESA WorldCover 2021 map for the given AOI via Planetary Computer STAC."""
    print("    [ESA] Querying Planetary Computer for ESA WorldCover mask...")
    import planetary_computer
    pc_catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace
    )
    search = pc_catalog.search(
        collections=["esa-worldcover"],
        intersects=aoi_geom
    )
    items = list(search.items())
    if not items:
        raise ValueError("No ESA WorldCover data found for this AOI!")
    
    item = items[0]
    map_href = item.assets["map"].href
    
    dest_array = np.zeros(target_shape, dtype=np.uint8)
    
    print(f"    [ESA] Streaming and reprojecting ESA mask from: {map_href}")
    with rasterio.open(map_href) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=dest_array,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=src_transform,
            dst_crs=src_crs,
            resampling=Resampling.nearest
        )
        
    return dest_array

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print statistics without saving patches.")
    args = parser.parse_args()

    print("Starting real dataset generation using ESA WorldCover for Hyderabad...")
    
    provider = CDSEProvider(max_cloud_cover=5.0)
    provider.connect()
    
    aoi_geojson = get_hyderabad_aoi()
    aoi_geom = shape(aoi_geojson)
    
    search_windows = [
        (date(2023, 1, 1), date(2023, 5, 1)),
        (date(2023, 10, 1), date(2023, 12, 31)),
        (date(2024, 1, 1), date(2024, 5, 1)),
    ]

    all_scenes = []
    print("Searching for cloud-free scenes over Hyderabad...")
    for start_d, end_d in search_windows:
        scenes = provider.search(
            aoi=aoi_geom,
            start_date=start_d,
            end_date=end_d,
            max_cloud_cover=5.0
        )
        if scenes:
            all_scenes.extend(scenes[:2]) # Take top 2 from each window
    
    if not all_scenes:
        print("No scenes found!")
        return
        
    out_dir_train = Path("data/benchmark/real/train")
    out_dir_val = Path("data/benchmark/real/val")
    if not args.dry_run:
        out_dir_train.mkdir(parents=True, exist_ok=True)
        out_dir_val.mkdir(parents=True, exist_ok=True)
    
    num_scenes = len(all_scenes)
    print(f"Found {num_scenes} scenes for ESA Land Cover dataset...")
    
    patch_idx = 0
    train_patches = 0
    val_patches = 0

    for i in range(num_scenes):
        scene_dict = all_scenes[i]
        scene_id = scene_dict.get("id") or scene_dict.get("title", "unknown")
        print(f"\n[{i+1}/{num_scenes}] Processing Scene: {scene_id}")
        
        print("    [S2] Downloading/loading scene bands via provider.load()...")
        scene = provider.load(scene_dict, aoi_geom)
        
        from src.preprocessing.pipeline import PreprocessingPipeline
        print("    [S2] Running Preprocessing Pipeline (Cloud mask, Resample, Normalize)...")
        preprocessor = PreprocessingPipeline()
        scene = preprocessor.run(scene).scene
        
        from src.eo.models.bands import Band
        b04 = scene.raster(Band.RED)
        if b04 is None:
            continue
        
        try:
            esa_mask_raw = fetch_esa_worldcover(
                aoi_geom=aoi_geom,
                target_shape=b04.array.shape,
                src_transform=b04.transform,
                src_crs=b04.crs
            )
        except Exception as e:
            print(f"    [ESA] Failed to fetch ESA mask: {e}")
            continue
            
        print("    [ESA] Mapping classes to GeoSentinel standard...")
        esa_mask = map_esa_to_geosentinel(esa_mask_raw)
            
        print("    [S2] Running Feature Engineering...")
        engineer = FeatureEngineeringPipeline()
        result = engineer.run(scene)
        
        if result.stack.channel_names != EXPECTED_CHANNELS:
            print(f"    [ERR] Channel order mismatch! Expected: {EXPECTED_CHANNELS}, Got: {result.stack.channel_names}")
            continue

        stack = result.stack.array  # (12, H, W)
        print(f"    Full stack shape: {stack.shape}, ESA Mask shape: {esa_mask.shape}")
        
        _, H, W = stack.shape
        patch_size = 256
        stride = 128  # 50% overlap
        
        valid_patches = 0
        for y in range(0, H - patch_size + 1, stride):
            for x in range(0, W - patch_size + 1, stride):
                patch = stack[:, y:y+patch_size, x:x+patch_size]
                mask = esa_mask[y:y+patch_size, x:x+patch_size]
                
                if np.isnan(patch).any() or (mask == 0).all():
                    continue
                    
                is_val = np.random.rand() < 0.2
                out_dir = out_dir_val if is_val else out_dir_train
                
                if not args.dry_run:
                    np.save(out_dir / f"image_{patch_idx:04d}.npy", patch.astype(np.float32))
                    np.save(out_dir / f"mask_{patch_idx:04d}.npy", mask)
                    
                if is_val:
                    val_patches += 1
                else:
                    train_patches += 1

                patch_idx += 1
                valid_patches += 1
                
        print(f"    Generated {valid_patches} patches from this scene.")
                
    if args.dry_run:
        print(f"\n[DRY RUN] Would generate {train_patches} train patches and {val_patches} val patches.")
    else:
        print(f"\nSuccessfully generated {train_patches} train and {val_patches} val patches at data/benchmark/real/")

if __name__ == "__main__":
    main()
