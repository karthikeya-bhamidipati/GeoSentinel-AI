"""
===============================================================================
GeoSentinel AI

Module:
    geojson_export.py

Description:
    GeoJSON export for segmentation masks and hotspot locations.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from shapely.geometry import mapping

from src.utils.io import write_geojson
from src.utils.paths import paths
from src.utils.logger import logger


class GeoJSONExporter:
    """
    Exports spatial analysis results to GeoJSON format.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or paths.REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_hotspots(
        self,
        hotspots: list[dict],
        transform,
        crs_epsg: int = 32644,
        filename: str | None = None,
    ) -> Path:
        """
        Export change hotspots as GeoJSON point features.

        Parameters
        ----------
        hotspots : list[dict]
            List of hotspot dicts (from SegmentationChangeResult).
        transform : Affine
            Rasterio affine transform for pixel→coordinate conversion.
        crs_epsg : int
            CRS EPSG code of the raster.
        filename : str | None

        Returns
        -------
        Path
        """

        from pyproj import Transformer

        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hotspots_{ts}.geojson"

        output_path = self.output_dir / filename

        features = []
        transformer = Transformer.from_crs(
            crs_epsg, 4326, always_xy=True
        )

        for i, hotspot in enumerate(hotspots):
            row = hotspot.get("center_row", 0)
            col = hotspot.get("center_col", 0)

            # Pixel → projected coordinate
            x = transform.c + col * transform.a
            y = transform.f + row * transform.e

            # Projected → WGS84
            lon, lat = transformer.transform(x, y)

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "id": i + 1,
                    "area_pixels": hotspot.get("area_pixels", 0),
                    "from_class": hotspot.get("from_class", ""),
                    "to_class": hotspot.get("to_class", ""),
                },
            })

        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }

        write_geojson(output_path, geojson)

        logger.info(
            f"Hotspots GeoJSON: {output_path.name} "
            f"({len(features)} features)"
        )

        return output_path

    def export_analysis_extent(
        self,
        aoi_geometry: dict,
        filename: str | None = None,
    ) -> Path:
        """
        Export AOI geometry as GeoJSON.
        """

        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aoi_{ts}.geojson"

        output_path = self.output_dir / filename

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": aoi_geometry,
                    "properties": {"name": "Analysis Extent"},
                }
            ],
        }

        write_geojson(output_path, geojson)

        logger.info(f"AOI GeoJSON: {output_path.name}")

        return output_path
