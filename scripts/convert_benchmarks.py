import os
import shutil
import numpy as np
import rasterio
from rasterio.transform import Affine
from pathlib import Path
from datasets import load_from_disk
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = PROJECT_ROOT / "data" / "benchmark"
OUT_DIR = PROJECT_ROOT / "data" / "benchmark_geotiffs"

def create_geotiff(out_path: Path, array: np.ndarray, is_mask: bool = False, x_offset: float = 0.0, y_offset: float = 0.0):
    # array shape: (C, H, W) or (H, W)
    if array.ndim == 2:
        array = np.expand_dims(array, axis=0)
    
    C, H, W = array.shape
    dtype = rasterio.uint8 if is_mask else rasterio.float32
    
    if not is_mask and array.dtype != np.float32:
        array = array.astype(np.float32)
        if array.max() > 1.0:
            array = array / 255.0
            
    # Dummy Affine Transform (10m resolution)
    # We add an offset so different cities/samples don't overlap exactly if we don't want them to, 
    # but TorchGeo's index will handle them. To be safe, we tile them spatially.
    transform = Affine(10.0, 0.0, x_offset, 0.0, -10.0, y_offset)
    
    with rasterio.open(
        out_path,
        'w',
        driver='GTiff',
        height=H,
        width=W,
        count=C,
        dtype=dtype,
        crs='+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs',
        transform=transform,
    ) as dst:
        dst.write(array)

def convert_s2looking():
    s2_dir = BENCHMARK_DIR / "s2looking"
    if not s2_dir.exists():
        print("S2Looking not found, skipping.")
        return
        
    ds = load_from_disk(str(s2_dir))
    
    out_t1 = OUT_DIR / "s2looking" / "t1"
    out_t2 = OUT_DIR / "s2looking" / "t2"
    out_mask = OUT_DIR / "s2looking" / "mask"
    
    for d in [out_t1, out_t2, out_mask]:
        d.mkdir(parents=True, exist_ok=True)
        
    idx = 0
    for split in ["train", "val"]:
        if split not in ds: continue
        for item in ds[split]:
            t1 = np.array(item["t1_image"]).transpose(2, 0, 1) # (3, H, W)
            t2 = np.array(item["t2_image"]).transpose(2, 0, 1) # (3, H, W)
            mask = np.array(item["change_mask"]) # (H, W)
            
            # Binary mask
            mask = (mask > 127).astype(np.uint8)
            
            # Space them out by 10,000 meters
            x = idx * 10000.0
            y = idx * 10000.0
            
            name = f"s2looking_{idx:05d}.tif"
            create_geotiff(out_t1 / name, t1, False, x, y)
            create_geotiff(out_t2 / name, t2, False, x, y)
            create_geotiff(out_mask / name, mask, True, x, y)
            
            idx += 1
            if idx % 500 == 0:
                print(f"S2Looking converted: {idx}")
                
    print(f"Total S2Looking: {idx}")

def convert_oscd():
    oscd_dir = BENCHMARK_DIR / "oscd" / "Onera Satellite Change Detection dataset - Images"
    if not oscd_dir.exists():
        print("OSCD not found, skipping.")
        return
        
    out_t1 = OUT_DIR / "oscd" / "t1"
    out_t2 = OUT_DIR / "oscd" / "t2"
    out_mask = OUT_DIR / "oscd" / "mask"
    
    for d in [out_t1, out_t2, out_mask]:
        d.mkdir(parents=True, exist_ok=True)
        
    cities = [d.name for d in oscd_dir.iterdir() if d.is_dir() and "Label" not in d.name]
    
    bands = ["B02", "B03", "B04", "B08", "B11", "B12"] # Example 6 bands
    
    x_offset = 0.0
    
    for city in cities:
        try:
            t1_stack = []
            t2_stack = []
            shape = None
            
            for band in bands:
                b_path1 = oscd_dir / city / "imgs_1_rect" / f"{band}.tif"
                b_path2 = oscd_dir / city / "imgs_2_rect" / f"{band}.tif"
                
                with rasterio.open(b_path1) as src:
                    arr = src.read(1).astype(np.float32)
                    if shape is None: shape = arr.shape
                    if arr.shape != shape: arr = cv2.resize(arr, (shape[1], shape[0]), interpolation=cv2.INTER_LINEAR)
                    t1_stack.append(arr)
                    
                with rasterio.open(b_path2) as src:
                    arr = src.read(1).astype(np.float32)
                    if arr.shape != shape: arr = cv2.resize(arr, (shape[1], shape[0]), interpolation=cv2.INTER_LINEAR)
                    t2_stack.append(arr)
                    
            t1 = np.stack(t1_stack) / 10000.0 # Standard Sentinel-2 scaling
            t2 = np.stack(t2_stack) / 10000.0
            
            t1 = np.clip(t1, 0, 1)
            t2 = np.clip(t2, 0, 1)
            
            # Find mask
            mask_path = None
            train_labels = BENCHMARK_DIR / "oscd" / "Onera Satellite Change Detection dataset - Train Labels" / city / "cm" / f"{city}-cm.tif"
            test_labels = BENCHMARK_DIR / "oscd" / "Onera Satellite Change Detection dataset - Test Labels" / city / "cm" / f"{city}-cm.tif"
            
            if train_labels.exists(): mask_path = train_labels
            elif test_labels.exists(): mask_path = test_labels
            
            if mask_path is None:
                print(f"No mask for OSCD city {city}, skipping.")
                continue
                
            with rasterio.open(mask_path) as src:
                mask = src.read(1)
                mask = (mask > 0).astype(np.uint8) # 0 is no change, 1 is change, 2 is ignore -> map to 1 for change
                if mask.shape != shape: mask = cv2.resize(mask, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
                
            name = f"oscd_{city}.tif"
            create_geotiff(out_t1 / name, t1, False, x_offset, 0.0)
            create_geotiff(out_t2 / name, t2, False, x_offset, 0.0)
            create_geotiff(out_mask / name, mask, True, x_offset, 0.0)
            
            x_offset += 20000.0 # Next city
            print(f"OSCD converted: {city}")
            
        except Exception as e:
            print(f"Failed OSCD city {city}: {e}")

if __name__ == "__main__":
    print("Converting benchmarks to GeoTIFFs...")
    convert_s2looking()
    convert_oscd()
    print("Done!")
