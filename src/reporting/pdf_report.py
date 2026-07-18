"""
===============================================================================
GeoSentinel AI

Module:
    pdf_report.py

Description:
    PDF report generator using Jinja2 and Playwright.

    Generates a structured analysis report containing:
    - Executive summary
    - Area change tables
    - Recommendations with WHY explanations
    - Analysis metadata

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from src.utils.logger import logger


def encode_image(path: str) -> str | None:
    if not path or not Path(path).exists():
        return None
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    except Exception as e:
        logger.warning(f"Failed to encode image {path}: {e}")
        return None


class PDFReportGenerator:
    """
    Generates PDF analysis reports using Playwright.
    """

    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir = Path(__file__).parent / "templates"

    def generate(self, analysis_data: dict[str, Any], filename: str = None) -> Path | None:
        """
        Generate a PDF report from analysis data.

        Parameters
        ----------
        analysis_data : dict
            Complete analysis result dictionary.
        filename : str
            Optional filename for the generated PDF.

        Returns
        -------
        Path | None
            Path to the generated PDF, or None if failed.
        """
        try:
            job_id = analysis_data.get("job_id", "unknown_job")
            if not filename:
                filename = f"{job_id}_report.pdf"
            output_path = self.output_dir / filename

            env = Environment(loader=FileSystemLoader(self.templates_dir))
            template = env.get_template("report_template.html")

            # Prepare data
            meta = analysis_data.get("metadata", {})
            area_rows = analysis_data.get("area_change", {}).get("rows", [])
            total_area = analysis_data.get("area_change", {}).get("total_area_km2", 0)
            if not total_area and area_rows:
                total_area = sum(row.get("t1_area_km2", 0) for row in area_rows)

            # Base64 encode images
            outputs = analysis_data.get("outputs", {})
            encoded_outputs = {
                k: encode_image(v) for k, v in outputs.items() if k.endswith("_png") and v
            }

            context = {
                "job_id": job_id,
                "generated_time": datetime.now().strftime('%d %B %Y, %H:%M'),
                "metadata": meta,
                "area_rows": area_rows,
                "total_area": total_area,
                "recommendations": analysis_data.get("recommendations", []),
                "outputs": encoded_outputs,
            }

            html_out = template.render(context)

            # Use playwright to print to PDF
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_content(html_out)
                # Wait for any network resources if needed
                page.wait_for_load_state("networkidle")
                
                page.pdf(
                    path=str(output_path),
                    format="A4",
                    print_background=True,
                    margin={"top": "20px", "right": "20px", "bottom": "40px", "left": "20px"}
                )
                browser.close()

            logger.info(f"Generated PDF report for job {job_id} at {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            return None
