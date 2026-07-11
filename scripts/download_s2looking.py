"""
GeoSentinel AI - Download S2Looking
Downloads the S2Looking dataset via HuggingFace Datasets.
"""

import os
from pathlib import Path
from datasets import load_dataset

def main():
    print("Starting S2Looking Dataset Download from HuggingFace...")
    out_dir = Path("data/benchmark/s2looking")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading to {out_dir.absolute()}...")
    
    try:
        # Load dataset from HuggingFace
        # EVER-Z/torchange_s2looking is a port of the S2Looking dataset
        dataset = load_dataset("EVER-Z/torchange_s2looking")
        print("S2Looking Download Complete!")
        print(dataset)
        
        # Optionally, we can save it locally if we need to access it outside of HF cache
        dataset.save_to_disk(str(out_dir))
        print(f"Dataset successfully saved to {out_dir}")
        
    except Exception as e:
        print(f"Failed to download S2Looking: {e}")

if __name__ == "__main__":
    main()
