import urllib.request
import shutil
from pathlib import Path
import zipfile
import sys
import glob
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def main():
    print("Setting up real benchmark datasets...")
    
    # --- Land Cover Dataset Setup ---
    lc_dir = PROJECT_ROOT / "data" / "benchmark" / "land_cover"
    img_dir = lc_dir / "imagery"
    lbl_dir = lc_dir / "labels"
    
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Download ESA WorldCover Tile for Hyderabad
    worldcover_url = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_N15E078_Map.tif"
    worldcover_path = lbl_dir / "ESA_WorldCover_10m_2020_v100_N15E078_Map.tif"
    
    if not worldcover_path.exists():
        print(f"Downloading ESA WorldCover tile for Hyderabad (N15E078)...")
        urllib.request.urlretrieve(worldcover_url, worldcover_path)
        print("Downloaded ESA WorldCover successfully.")
    else:
        print("ESA WorldCover tile already exists.")
        
    # 2. Copy/Symlink Sentinel-2 scenes covering Hyderabad
    print("Linking Sentinel-2 scenes...")
    s2_downloads = PROJECT_ROOT / "data" / "raw" / "downloads"
    hyderabad_scenes = list(s2_downloads.glob("*T44QKE*")) + list(s2_downloads.glob("*T43QHV*"))
    
    if not hyderabad_scenes:
        print("Warning: No Hyderabad scenes found in data/raw/downloads!")
    
    # We just copy the .jp2 bands we need so TorchGeo can load them directly
    for scene_dir in hyderabad_scenes[:5]:  # Take 5 scenes to keep it manageable
        if not scene_dir.is_dir():
            continue
            
        print(f"Processing scene: {scene_dir.name}")
        for band in ["B02", "B03", "B04", "B08", "B11", "SCL"]:
            band_file = list(scene_dir.glob(f"*{band}*.jp2"))
            if band_file:
                target_path = img_dir / f"{scene_dir.name}_{band}.jp2"
                if not target_path.exists():
                    shutil.copy2(band_file[0], target_path)

    print("Land Cover dataset setup complete.")

if __name__ == "__main__":
    main()
