"""
GeoSentinel AI - Download OSCD
Downloads the Onera Satellite Change Detection dataset via TorchGeo.
"""

import sys
from pathlib import Path
import torch
from torchgeo.datasets import OSCD

def main():
    print("Starting OSCD Dataset Download...")
    out_dir = Path("data/benchmark/oscd")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading to {out_dir.absolute()}...")
    
    try:
        # Download the dataset (Train Split)
        dataset_train = OSCD(
            root=str(out_dir),
            split="train",
            download=True,
            checksum=False
        )
        print(f"OSCD Train downloaded: {len(dataset_train)} scenes.")
        
        # Download the dataset (Test Split)
        dataset_test = OSCD(
            root=str(out_dir),
            split="test",
            download=True,
            checksum=False
        )
        print(f"OSCD Test downloaded: {len(dataset_test)} scenes.")
        print("\nOSCD Download Complete!")
    except Exception as e:
        print(f"Failed to download OSCD: {e}")

if __name__ == "__main__":
    main()
