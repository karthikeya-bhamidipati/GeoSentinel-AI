import rasterio
from rasterio.crs import CRS
from pathlib import Path
import os
import glob

def main():
    print("Fixing missing CRS in JP2 files and converting to TIF...")
    img_dir = Path("data/benchmark/land_cover/imagery")
    jp2_files = list(img_dir.glob("*.jp2"))
    
    for jp2 in jp2_files:
        # Determine CRS from filename
        if "T44QKE" in jp2.name:
            crs = CRS.from_proj4("+proj=utm +zone=44 +datum=WGS84 +units=m +no_defs")
        elif "T43QHV" in jp2.name:
            crs = CRS.from_proj4("+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs")
        else:
            print(f"Unknown UTM zone for {jp2.name}, skipping.")
            continue
            
        tif_path = jp2.with_suffix('.tif')
        
        print(f"Converting {jp2.name} to {tif_path.name} with CRS {crs}...")
        
        with rasterio.open(jp2) as src:
            meta = src.meta.copy()
            meta.update({
                "driver": "GTiff",
                "crs": crs
            })
            
            with rasterio.open(tif_path, "w", **meta) as dst:
                dst.write(src.read())
                
        # Remove the original JP2 to avoid TorchGeo trying to load it
        os.remove(jp2)
        
    print("Done converting imagery!")

if __name__ == "__main__":
    main()
