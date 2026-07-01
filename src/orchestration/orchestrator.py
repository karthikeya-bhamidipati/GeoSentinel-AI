"""
===============================================================================
GeoSentinel AI

Module:
    orchestrator.py

Description:
    Pipeline orchestrator — the single entry point for a complete
    GeoSentinel AI analysis.

    Execution order:
    1. Validate AOI against HMR boundary
    2. Search + download Sentinel-2 scenes (T1, T2)
    3. Preprocess each scene
    4. Compute spectral features
    5. Run segmentation inference
    6. Temporal analysis (NDVI, NDBI, segmentation change)
    7. Area calculations
    8. Spatial statistics
    9. Generate recommendations
    10. Export reports (PDF, CSV, GeoJSON, GeoTIFF)
    11. Return structured result

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Optional

import numpy as np

from src.eo.aoi.geometry import AOI
from src.eo.aoi.validator import AOIValidator
from src.eo.cache import CacheManager
from src.eo.providers.stac import CDSEProvider
from src.eo.models.scene import SentinelScene
from src.eo.exceptions import (
    GeoSentinelError,
    AOIError,
    SceneNotFoundError,
)

from src.preprocessing.pipeline import PreprocessingPipeline
from src.feature_engineering.pipeline import FeatureEngineeringPipeline
from src.inference.predictor import ScenePredictor
from src.inference.visualization import SegmentationVisualizer

from src.temporal.ndvi_change import NDVIChangeAnalyzer
from src.temporal.ndbi_change import NDBIChangeAnalyzer
from src.temporal.segmentation_change import SegmentationChangeAnalyzer

from src.analytics.area import AreaCalculator
from src.analytics.statistics import SpatialStatisticsCalculator

from src.recommendation.engine import RecommendationEngine

from src.reporting.pdf_report import PDFReportGenerator
from src.reporting.csv_export import CSVExporter
from src.reporting.geojson_export import GeoJSONExporter
from src.reporting.geotiff_export import GeoTIFFExporter

from src.utils.helpers import parse_date
from src.utils.logger import logger
from src.utils.paths import paths


# =============================================================================
# Analysis Result
# =============================================================================


@dataclass
class AnalysisResult:
    """
    Complete output of a GeoSentinel AI analysis.

    Attributes
    ----------
    job_id : str
        Unique identifier for this analysis job.
    aoi : dict
        GeoJSON geometry of the analysis area.
    date1 : str
        T1 date (ISO 8601).
    date2 : str
        T2 date (ISO 8601).
    scene_t1_id : str
    scene_t2_id : str
    area_change : dict
        Area statistics by land cover class.
    temporal_stats : dict
        NDVI, NDBI, and segmentation change summaries.
    statistics : dict
        Spatial statistics and trend summary.
    recommendations : list[dict]
        Prioritized recommendations with WHY explanations.
    outputs : dict[str, str]
        Paths to generated output files.
    metadata : dict
        Job metadata (runtime, cloud cover, etc.).
    success : bool
    error : str | None
    """

    job_id: str
    aoi: dict
    date1: str
    date2: str
    scene_t1_id: str = ""
    scene_t2_id: str = ""
    area_change: dict = field(default_factory=dict)
    temporal_stats: dict = field(default_factory=dict)
    statistics: dict = field(default_factory=dict)
    recommendations: list[dict] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict:

        return {
            "job_id": self.job_id,
            "aoi": self.aoi,
            "date1": self.date1,
            "date2": self.date2,
            "scene_t1_id": self.scene_t1_id,
            "scene_t2_id": self.scene_t2_id,
            "area_change": self.area_change,
            "temporal_stats": self.temporal_stats,
            "statistics": self.statistics,
            "recommendations": self.recommendations,
            "outputs": self.outputs,
            "metadata": self.metadata,
            "success": self.success,
            "error": self.error,
        }


# =============================================================================
# Orchestrator
# =============================================================================


class Orchestrator:
    """
    Full GeoSentinel AI analysis pipeline.

    Coordinates all modules from data acquisition to report generation.
    This is the single public API for triggering an analysis.

    Parameters
    ----------
    model_checkpoint : Path | None
        Path to a trained model checkpoint. If None, inference
        returns random predictions (for development/testing).
    device : str
        'cuda' or 'cpu'.
    max_cloud_cover : float
        Maximum cloud cover % for scene selection.
    """

    def __init__(
        self,
        model_checkpoint: Optional[Path] = None,
        device: str = "cpu",
        max_cloud_cover: float = 10.0,
    ) -> None:

        self._model_checkpoint = model_checkpoint
        self._device = device
        self._max_cloud_cover = max_cloud_cover

        # Initialize all components
        self._validator = AOIValidator()
        self._cache = CacheManager()
        self._provider = CDSEProvider(max_cloud_cover=max_cloud_cover)
        self._preprocessing = PreprocessingPipeline()
        self._feature_engineering = FeatureEngineeringPipeline()
        self._ndvi_change = NDVIChangeAnalyzer()
        self._ndbi_change = NDBIChangeAnalyzer()
        self._seg_change = SegmentationChangeAnalyzer()
        self._area_calc = AreaCalculator()
        self._stats_calc = SpatialStatisticsCalculator()
        self._rec_engine = RecommendationEngine()
        self._visualizer = SegmentationVisualizer()

        # Reporting
        self._pdf_gen = PDFReportGenerator()
        self._csv_exp = CSVExporter()
        self._geojson_exp = GeoJSONExporter()
        self._geotiff_exp = GeoTIFFExporter()

        # Lazy model loading
        self._predictor: Optional[ScenePredictor] = None

        logger.info("Orchestrator initialized.")

    # ------------------------------------------------------------------
    # Main Entry Point
    # ------------------------------------------------------------------

    def run(
        self,
        job_id: str,
        aoi_geojson: dict,
        date1: str | date,
        date2: str | date,
    ) -> AnalysisResult:
        """
        Run a complete analysis pipeline.

        Parameters
        ----------
        job_id : str
            Unique identifier for this job.
        aoi_geojson : dict
            GeoJSON geometry (Point, Polygon, or FeatureCollection).
        date1 : str | date
            T1 (earlier) date.
        date2 : str | date
            T2 (later) date.

        Returns
        -------
        AnalysisResult
        """

        start_time = time.time()

        date1 = parse_date(date1)
        date2 = parse_date(date2)

        result = AnalysisResult(
            job_id=job_id,
            aoi=aoi_geojson,
            date1=str(date1),
            date2=str(date2),
        )

        try:
            # ----------------------------------------------------------
            # Step 1: Validate AOI
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 1: Validating AOI ...")

            aoi = AOI.from_geojson(aoi_geojson)
            self._validator.validate(aoi)

            # ----------------------------------------------------------
            # Step 2: Download T1 and T2 scenes
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 2: Downloading scenes ...")

            self._provider.connect()

            t1_features = self._provider.search(
                aoi=aoi.geometry,
                start_date=date1,
                end_date=date1,
                max_results=3,
            )

            t2_features = self._provider.search(
                aoi=aoi.geometry,
                start_date=date2,
                end_date=date2,
                max_results=3,
            )

            scene_t1 = self._provider.load(
                source=t1_features[0],
                aoi=aoi.geometry,
            )

            scene_t2 = self._provider.load(
                source=t2_features[0],
                aoi=aoi.geometry,
            )

            result.scene_t1_id = scene_t1.product_name
            result.scene_t2_id = scene_t2.product_name

            self._provider.close()

            # ----------------------------------------------------------
            # Step 3: Preprocess
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 3: Preprocessing ...")

            t1_preprocessed = self._preprocessing.run(scene_t1)
            t2_preprocessed = self._preprocessing.run(
                scene_t2,
                reference_scene=t1_preprocessed.scene,
            )

            # ----------------------------------------------------------
            # Step 4: Feature Engineering
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 4: Feature engineering ...")

            fe_t1 = self._feature_engineering.run(
                t1_preprocessed.scene
            )

            fe_t2 = self._feature_engineering.run(
                t2_preprocessed.scene
            )

            # ----------------------------------------------------------
            # Step 5: AI Inference
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 5: Segmentation inference ...")

            predictor = self._get_predictor()

            pred_t1 = predictor.predict(fe_t1.stack)
            pred_t2 = predictor.predict(fe_t2.stack)

            mask_t1 = pred_t1.mask
            mask_t2 = pred_t2.mask

            # ----------------------------------------------------------
            # Step 6: Temporal Analysis
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 6: Temporal analysis ...")

            ndvi_t1 = fe_t1.indices.get("NDVI")
            ndvi_t2 = fe_t2.indices.get("NDVI")
            ndbi_t1 = fe_t1.indices.get("NDBI")
            ndbi_t2 = fe_t2.indices.get("NDBI")

            ndvi_result = None
            ndbi_result = None

            if ndvi_t1 is not None and ndvi_t2 is not None:
                ndvi_result = self._ndvi_change.analyze(ndvi_t1, ndvi_t2)

            if ndbi_t1 is not None and ndbi_t2 is not None:
                ndbi_result = self._ndbi_change.analyze(ndbi_t1, ndbi_t2)

            seg_result = self._seg_change.analyze(mask_t1, mask_t2)

            result.temporal_stats = {
                "ndvi_change": ndvi_result.summary() if ndvi_result else {},
                "ndbi_change": ndbi_result.summary() if ndbi_result else {},
                "segmentation_change": seg_result.summary(),
            }

            # ----------------------------------------------------------
            # Step 7: Area Calculations
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 7: Area calculations ...")

            area_change = self._area_calc.compute_change(mask_t1, mask_t2)

            result.area_change = {
                "rows": area_change.to_rows(),
                "total_area_km2": round(area_change.total_area_km2, 4),
            }

            # ----------------------------------------------------------
            # Step 8: Spatial Statistics
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 8: Spatial statistics ...")

            stats = self._stats_calc.compute_full(
                indices_t1=fe_t1.indices,
                indices_t2=fe_t2.indices,
                mask_t1=mask_t1,
                mask_t2=mask_t2,
            )

            result.statistics = stats.trend_summary

            # ----------------------------------------------------------
            # Step 9: Recommendations
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 9: Generating recommendations ...")

            rec_result = self._rec_engine.evaluate(
                ndvi_change=ndvi_result,
                ndbi_change=ndbi_result,
                seg_change=seg_result,
                area_change=area_change,
                date1=str(date1),
                date2=str(date2),
            )

            result.recommendations = [
                r.to_dict() for r in rec_result.recommendations
            ]

            # ----------------------------------------------------------
            # Step 10: Export Reports
            # ----------------------------------------------------------

            logger.info(f"[{job_id}] Step 10: Exporting reports ...")

            output_files = {}

            # CSV export
            csv_path = self._csv_exp.export_area_stats(
                area_change.to_rows(),
                filename=f"{job_id}_area_stats.csv",
            )
            output_files["csv"] = str(csv_path)

            rec_csv = self._csv_exp.export_recommendations(
                result.recommendations,
                filename=f"{job_id}_recommendations.csv",
            )
            output_files["recommendations_csv"] = str(rec_csv)

            # Visualizations
            vis_t2_path = paths.FIGURES_DIR / f"{job_id}_mask_t2.png"
            self._visualizer.save_mask_png(
                mask_t2,
                vis_t2_path,
                title=f"Land Cover — {date2}",
            )
            output_files["mask_png"] = str(vis_t2_path)

            if ndvi_result is not None:
                ndvi_delta_path = paths.FIGURES_DIR / f"{job_id}_ndvi_delta.png"
                self._visualizer.save_change_map_png(
                    ndvi_result.delta,
                    ndvi_delta_path,
                    title=f"NDVI Change ({date1} → {date2})",
                )
                output_files["ndvi_delta_png"] = str(ndvi_delta_path)

            # PDF report
            analysis_data_for_pdf = {
                "metadata": {
                    "date1": str(date1),
                    "date2": str(date2),
                },
                "area_change": result.area_change,
                "recommendations": result.recommendations,
            }

            pdf_path = self._pdf_gen.generate(
                analysis_data_for_pdf,
                filename=f"{job_id}_report.pdf",
            )

            if pdf_path:
                output_files["pdf"] = str(pdf_path)

            result.outputs = output_files

            # ----------------------------------------------------------
            # Metadata
            # ----------------------------------------------------------

            elapsed = time.time() - start_time

            result.metadata = {
                "elapsed_seconds": round(elapsed, 1),
                "cloud_cover_t1": t1_features[0].get(
                    "properties", {}
                ).get("eo:cloud_cover", None),
                "cloud_cover_t2": t2_features[0].get(
                    "properties", {}
                ).get("eo:cloud_cover", None),
                "scene_t1_id": result.scene_t1_id,
                "scene_t2_id": result.scene_t2_id,
            }

            logger.info(
                f"[{job_id}] Analysis complete in "
                f"{elapsed:.1f}s."
            )

        except (AOIError, SceneNotFoundError, GeoSentinelError) as exc:
            logger.error(f"[{job_id}] Analysis failed: {exc}")
            result.success = False
            result.error = str(exc)

        except Exception as exc:
            logger.exception(
                f"[{job_id}] Unexpected error: {exc}"
            )
            result.success = False
            result.error = str(exc)

        return result

    # ------------------------------------------------------------------

    def _get_predictor(self) -> ScenePredictor:
        """
        Lazy-load the model predictor.
        """

        if self._predictor is not None:
            return self._predictor

        from src.models.model_factory import ModelFactory
        from src.models.unet import DEFAULT_IN_CHANNELS, NUM_CLASSES

        factory = ModelFactory()
        model = factory.create_model(
            model_type="unet",
            in_channels=DEFAULT_IN_CHANNELS,
            num_classes=NUM_CLASSES,
            encoder_weights=None,  # No pretrained weights for inference
        )

        if self._model_checkpoint and Path(self._model_checkpoint).exists():
            self._predictor = ScenePredictor.from_checkpoint(
                checkpoint_path=Path(self._model_checkpoint),
                model=model,
                device=self._device,
            )
        else:
            logger.warning(
                "No model checkpoint provided. "
                "Using uninitialized model weights."
            )
            self._predictor = ScenePredictor(
                model=model,
                device=self._device,
            )

        return self._predictor

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"Orchestrator("
            f"device={self._device}, "
            f"max_cloud={self._max_cloud_cover}%)"
        )
