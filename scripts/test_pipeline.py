import json
import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

import sys
# Load env before imports
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.orchestration.orchestrator import Orchestrator
from backend.app.services import JobRecord

def test_pipeline():
    print("Testing backend pipeline end-to-end...")
    
    # Small sample AOI in Hyderabad
    aoi_geojson = {
        "type": "Polygon",
        "coordinates": [
            [
                [78.47, 17.37],
                [78.47, 17.39],
                [78.49, 17.39],
                [78.49, 17.37],
                [78.47, 17.37]
            ]
        ]
    }
    
    job_id = "test-job-999"
    orchestrator = Orchestrator()
    
    try:
        result = orchestrator.run(
            job_id=job_id,
            aoi_geojson=aoi_geojson,
            date1="2023-01-15",
            date2="2023-06-15",
            max_cloud_cover=20.0
        )
        print("Pipeline succeeded!")
        
        # Save to history manually so it appears in frontend
        job = JobRecord(job_id=job_id)
        job.status = "COMPLETED"
        job.progress_message = "Completed"
        job.completed_at = datetime.now(timezone.utc).isoformat()
        job.result = result.to_dict()
        
        job_dir = Path("data/jobs")
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / f"{job_id}.json").write_text(json.dumps(job.to_dict(), indent=2), "utf-8")
        print(f"Result saved at: data/jobs/{job_id}.json")
        
    except Exception as e:
        print("Pipeline failed!")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
