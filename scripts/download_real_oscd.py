"""
Real OSCD (Onera Satellite Change Detection) Data Downloader
Using HuggingFace Datasets to fetch the oscd100 subset directly.
"""

import os
from pathlib import Path
from datasets import load_dataset
import numpy as np

def main():
    print("============================================================")
    print("  GeoSentinel AI - Real OSCD Data Downloader")
    print("============================================================")
    
    root_dir = Path("data/benchmark/real_oscd")
    root_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading OSCD100 dataset to {root_dir}...")
    
    try:
        # Load from HuggingFace
        dataset = load_dataset("hkristen/oscd100")
        
        # Save a summary
        print(f"\n[OK] Successfully downloaded real OSCD data!")
        print(dataset)
        
        # We will save the first few images to verify it works
        train_data = dataset['train']
        print(f"Total training scenes: {len(train_data)}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[ERROR] Failed to download OSCD: {e}")

if __name__ == "__main__":
    main()
