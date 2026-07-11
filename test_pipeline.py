import asyncio
from dotenv import load_dotenv
load_dotenv()
from datetime import date
from src.orchestration.orchestrator import Orchestrator

def main():
    o = Orchestrator()
    bbox = {
        "type": "Polygon",
        "coordinates": [[
            [78.34, 17.32],
            [78.45, 17.32],
            [78.45, 17.38],
            [78.34, 17.38],
            [78.34, 17.32]
        ]]
    }
    
    try:
        # I'll use dates that have a known Sentinel-2 pass over Hyderabad
        # E.g., 2023-01-14 and 2024-01-14.
        res = o.run(
            job_id="test-123",
            aoi_geojson=bbox,
            date1="2023-01-14",
            date2="2024-01-14",
            max_cloud_cover=20.0,
            progress_callback=lambda s, m: print(f"[{s}] {m}")
        )
        print("Success:", res.success)
        if not res.success:
            print("Error:", res.error)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
