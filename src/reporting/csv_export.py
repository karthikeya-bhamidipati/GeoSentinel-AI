"""
===============================================================================
GeoSentinel AI

Module:
    csv_export.py

Description:
    CSV export for area statistics and recommendation data.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.io import write_csv
from src.utils.paths import paths
from src.utils.logger import logger


class CSVExporter:
    """
    Exports analysis results to CSV files.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or paths.REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_area_stats(
        self,
        rows: list[dict[str, Any]],
        filename: str | None = None,
    ) -> Path:
        """
        Export area change statistics to CSV.

        Parameters
        ----------
        rows : list[dict]
        filename : str | None

        Returns
        -------
        Path
        """

        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"area_stats_{ts}.csv"

        output_path = self.output_dir / filename
        write_csv(output_path, rows)

        logger.info(f"CSV exported: {output_path.name}")

        return output_path

    def export_recommendations(
        self,
        recommendations: list[dict[str, Any]],
        filename: str | None = None,
    ) -> Path:
        """
        Export recommendations to CSV.
        """

        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recommendations_{ts}.csv"

        output_path = self.output_dir / filename
        write_csv(output_path, recommendations)

        logger.info(f"Recommendations CSV: {output_path.name}")

        return output_path
