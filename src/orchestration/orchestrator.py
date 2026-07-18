"""
===============================================================================
GeoSentinel AI

Module:
    orchestrator.py

Description:
    Pipeline orchestrator — the single entry point for a complete
    GeoSentinel AI analysis.

    Execution order:
    1.  Validate AOI against HMR boundary
    2.  Search CDSE STAC for best T1 and T2 scenes (nearest to dates,
        lowest cloud cover)
    3.  Stream and cache AOI-clipped bands via GDAL /vsicurl/ (never
        the full ~500 MB SAFE product)
    4.  Preprocess each scene:
        a. SCL cloud masking
        b. Resample all bands to 10 m
        c. Spatial alignment (T2 → T1 pixel grid)
        d. DN → surface reflectance normalisation
    5.  Compute all 7 spectral indices (NDVI, NDBI, NDWI, EVI, SAVI,
        MSAVI, BSI) and stack with 5 bands → 12-channel feature tensor
    6.  Run U-Net segmentation inference (T1, T2)
    7.  Temporal change analysis:
        - NDVI delta
        - NDBI delta
        - Pixel-level segmentation change matrix
    8.  Area calculations per land-cover class
    9.  Spatial statistics (per-class index means, trend summary)
    10. Rule-based recommendation engine (YAML rules, no LLM)
    11. Export outputs:
        - GeoTIFF  : segmentation masks (T1, T2) + NDVI/NDBI delta rasters
        - GeoJSON  : change hotspots, AOI extent
        - CSV      : area statistics, recommendations
        - PDF      : structured analysis report
    12. Return AnalysisResult with all metadata

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Optional, Tuple
import concurrent.futures

import numpy as np

from rasterio.crs import CRS
from rasterio.transform import Affine

from src.analytics.area import AreaCalculator
from src.analytics.statistics import SpatialStatisticsCalculator
from src.eo.aoi.geometry import AOI
from src.eo.aoi.validator import AOIValidator
from src.eo.exceptions import AOIError, GeoSentinelError, SceneNotFoundError
from src.eo.models.bands import Band
from src.eo.models.scene import SentinelScene
from src.eo.providers.stac import CDSEProvider
from src.feature_engineering.pipeline import FeatureEngineeringPipeline, FeatureEngineeringResult
from src.inference.predictor import ScenePredictor
from src.inference.visualization import SegmentationVisualizer
from src.preprocessing.pipeline import PreprocessingPipeline
from src.recommendation.engine import RecommendationEngine
from src.reporting.csv_export import CSVExporter
from src.reporting.geojson_export import GeoJSONExporter
from src.reporting.geotiff_export import GeoTIFFExporter
from src.reporting.pdf_report import PDFReportGenerator
from src.temporal.ndbi_change import NDBIChangeAnalyzer
from src.temporal.ndvi_change import NDVIChangeAnalyzer
from src.temporal.segmentation_change import SegmentationChangeAnalyzer
from src.utils.config import ProjectConfig
from src.utils.helpers import parse_date
from src.utils.logger import logger
from src.utils.paths import paths


ProgressCallback = Callable[[str, str], None]


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class AnalysisResult:
    """
    Complete output of a GeoSentinel AI analysis.

    This dataclass is the single return value of Orchestrator.run().
    It is serialised to JSON and returned via the REST API.
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
        """Serialise the result for API responses."""

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

    The orchestrator coordinates every stage from AOI validation to
    multi-format report generation.  It owns no data processing logic
    itself — each step is delegated to a dedicated service class.

    Parameters
    ----------
    model_checkpoint : Path | None
        Path to a trained U-Net checkpoint.  If None the model runs with
        uninitialised weights (useful for integration tests).
    device : str
        PyTorch device string — ``'cpu'`` or ``'cuda'``.
    max_cloud_cover : float
        Maximum scene cloud cover percentage to accept (default 10 %).
    """

    def __init__(
        self,
        model_checkpoint: Optional[Path] = None,
        change_model_checkpoint: Optional[Path] = None,
        device: str = "cpu",
        max_cloud_cover: float = 10.0,
    ) -> None:
        self._model_checkpoint = model_checkpoint
        self._change_model_checkpoint = change_model_checkpoint
        self._device = device
        self._max_cloud_cover = max_cloud_cover
        self._config = ProjectConfig()

        # --- Domain services -------------------------------------------
        self._validator = AOIValidator()
        self._preprocessing = PreprocessingPipeline()
        self._feature_engineering = FeatureEngineeringPipeline()

        # --- Temporal analysers ----------------------------------------
        self._ndvi_change = NDVIChangeAnalyzer()
        self._ndbi_change = NDBIChangeAnalyzer()
        self._seg_change = SegmentationChangeAnalyzer()

        # --- Analytics -------------------------------------------------
        self._area_calc = AreaCalculator()
        self._stats_calc = SpatialStatisticsCalculator()
        self._rec_engine = RecommendationEngine()

        # --- Visualisation & export ------------------------------------
        self._visualizer = SegmentationVisualizer()
        self._pdf_gen = PDFReportGenerator(output_dir=paths.REPORTS_DIR)
        self._csv_exp = CSVExporter()
        self._geojson_exp = GeoJSONExporter()
        self._geotiff_exp = GeoTIFFExporter()

        # --- Lazy-loaded model predictors --------------------------------
        self._lc_predictor: Optional[ScenePredictor] = None
        self._change_predictor: Optional[ScenePredictor] = None

        logger.info("Orchestrator initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        job_id: str,
        aoi_geojson: dict,
        date1: str | date,
        date2: str | date,
        max_cloud_cover: float | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> AnalysisResult:
        """
        Execute the full analysis pipeline.

        Parameters
        ----------
        job_id : str
            Unique job identifier (used for output filenames).
        aoi_geojson : dict
            GeoJSON geometry dict for the Area of Interest.
        date1 : str | date
            Reference date (T1).
        date2 : str | date
            Target date (T2).
        max_cloud_cover : float | None
            Override for cloud cover threshold.
        progress_callback : ProgressCallback | None
            Called at each pipeline step as ``(step_id, message)``.

        Returns
        -------
        AnalysisResult
        """

        start_time = time.time()
        parsed_date1 = parse_date(date1)
        parsed_date2 = parse_date(date2)

        result = AnalysisResult(
            job_id=job_id,
            aoi=aoi_geojson,
            date1=str(parsed_date1),
            date2=str(parsed_date2),
        )

        def mark(step_id: str, message: str) -> None:
            logger.info(f"[{job_id}] {message}")
            if progress_callback is not None:
                progress_callback(step_id, message)

        provider: Optional[CDSEProvider] = None

        try:
            # ----------------------------------------------------------
            # Step 1: AOI Validation
            # ----------------------------------------------------------

            mark("aoi", "Validating AOI …")
            aoi = AOI.from_geojson(aoi_geojson)
            self._validator.validate(aoi)

            # ----------------------------------------------------------
            # Step 2: Search and pick best T1 scene (local cloud check)
            # ----------------------------------------------------------

            provider = self._create_provider(max_cloud_cover)
            provider.connect()
            search_window = timedelta(days=30)

            mark(
                "search",
                f"Searching CDSE for T1 scene near {parsed_date1} …",
            )
            t1_features = provider.search(
                aoi=aoi.geometry,
                start_date=parsed_date1 - search_window,
                end_date=parsed_date1 + search_window,
                max_cloud_cover=max_cloud_cover,
                max_results=5,
            )
            
            # Pick best local cloud cover for T1
            best_t1_feature = t1_features[0]
            best_t1_cloud = 100.0
            for f in t1_features:
                local_cloud = provider.get_local_cloud_cover(f, aoi.geometry)
                if local_cloud < best_t1_cloud:
                    best_t1_cloud = local_cloud
                    best_t1_feature = f
            t1_features = [best_t1_feature]

            mark(
                "search",
                f"Searching CDSE for T2 scene near {parsed_date2} …",
            )
            t2_features = provider.search(
                aoi=aoi.geometry,
                start_date=parsed_date2 - search_window,
                end_date=parsed_date2 + search_window,
                max_cloud_cover=max_cloud_cover,
                max_results=5,
            )
            
            # Pick best local cloud cover for T2
            best_t2_feature = t2_features[0]
            best_t2_cloud = 100.0
            for f in t2_features:
                local_cloud = provider.get_local_cloud_cover(f, aoi.geometry)
                if local_cloud < best_t2_cloud:
                    best_t2_cloud = local_cloud
                    best_t2_feature = f
            t2_features = [best_t2_feature]

            # ----------------------------------------------------------
            # Step 3: Stream and cache AOI-clipped bands
            # ----------------------------------------------------------

            mark("download", "Streaming T1 and T2 bands concurrently (AOI window via /vsicurl/) …")

            provider_t1 = self._create_provider(max_cloud_cover)
            provider_t1.connect()
            provider_t2 = self._create_provider(max_cloud_cover)
            provider_t2.connect()

            def load_t1():
                return provider_t1.load(source=t1_features[0], aoi=aoi.geometry)

            def load_t2():
                return provider_t2.load(source=t2_features[0], aoi=aoi.geometry)

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_t1 = executor.submit(load_t1)
                future_t2 = executor.submit(load_t2)
                scene_t1 = future_t1.result()
                scene_t2 = future_t2.result()

            result.scene_t1_id = scene_t1.product_name
            result.scene_t2_id = scene_t2.product_name

            # ----------------------------------------------------------
            # Step 4: Preprocess scenes
            #   a. Cloud masking
            #   b. Resample to 10 m
            #   c. Spatial alignment (T2 → T1)
            #   d. Normalisation
            # ----------------------------------------------------------

            mark("preprocess", "Preprocessing T1 …")
            t1_prep = self._preprocessing.run(scene_t1)

            mark("preprocess", "Preprocessing T2 (align to T1) …")
            t2_prep = self._preprocessing.run(
                scene_t2,
                reference_scene=t1_prep.scene,
            )

            # ----------------------------------------------------------
            # Step 5: Compute spectral features
            # ----------------------------------------------------------

            mark("features", "Computing spectral features (T1) …")
            fe_t1 = self._feature_engineering.run(t1_prep.scene)

            mark("features", "Computing spectral features (T2) …")
            fe_t2 = self._feature_engineering.run(t2_prep.scene)

            # ----------------------------------------------------------
            # Step 6: AI segmentation inference
            # ----------------------------------------------------------

            import numpy as np
            from src.feature_engineering.stack import FeatureStack

            min_h_stack = min(fe_t1.stack.height, fe_t2.stack.height)
            min_w_stack = min(fe_t1.stack.width, fe_t2.stack.width)
            t1_arr = fe_t1.stack.array[:, :min_h_stack, :min_w_stack].copy()
            t2_arr = fe_t2.stack.array[:, :min_h_stack, :min_w_stack].copy()

            stack_t1 = FeatureStack(
                array=t1_arr,
                channel_names=fe_t1.stack.channel_names
            )
            stack_t2 = FeatureStack(
                array=t2_arr,
                channel_names=fe_t2.stack.channel_names
            )

            mark("ai", "Running DeepLabV3+ Land Cover (T1) …")
            lc_predictor = self._get_landcover_predictor()
            pred_t1 = lc_predictor.predict(stack_t1)

            mark("ai", "Running DeepLabV3+ Land Cover (T2) …")
            pred_t2 = lc_predictor.predict(stack_t2)

            mask_t1 = pred_t1.mask  # (H, W) int
            mask_t2 = pred_t2.mask  # (H, W) int

            # Fix for Cloud Masking Bug: If a pixel is completely masked (all 0s), 
            # the neural network convolutions produce random classes (often Water or Vegetation).
            # We explicitly override these nodata/cloud pixels to Background (0).
            nodata_t1 = (fe_t1.stack.array[:, :min_h_stack, :min_w_stack] == 0).all(axis=0)
            nodata_t2 = (fe_t2.stack.array[:, :min_h_stack, :min_w_stack] == 0).all(axis=0)
            
            mask_t1[nodata_t1] = 0
            mask_t2[nodata_t2] = 0

            mark("ai", "Running Siamese U-Net Change Detection …")
            change_predictor = self._get_change_predictor()
            pred_change = change_predictor.predict(stack_t1, stack_t2)
            ml_change_mask = pred_change.mask  # (H, W) int (0 or 1)

            # Resolve CRS and Affine transform from the T1 reference raster
            scene_crs, scene_transform = self._get_scene_georef(t1_prep.scene)

            # ----------------------------------------------------------
            # Step 7: Temporal change analysis
            # ----------------------------------------------------------

            mark("temporal", "Running NDVI / NDBI / segmentation change …")

            ndvi_t1 = fe_t1.indices.get("NDVI")
            ndvi_t2 = fe_t2.indices.get("NDVI")
            ndbi_t1 = fe_t1.indices.get("NDBI")
            ndbi_t2 = fe_t2.indices.get("NDBI")

            # Force exact shape alignment (crop to absolute min bounding box)
            shapes = [mask_t1.shape, mask_t2.shape]
            if ndvi_t1 is not None: shapes.append(ndvi_t1.shape)
            if ndvi_t2 is not None: shapes.append(ndvi_t2.shape)
            if ndbi_t1 is not None: shapes.append(ndbi_t1.shape)
            if ndbi_t2 is not None: shapes.append(ndbi_t2.shape)
            
            min_h = min(s[0] for s in shapes)
            min_w = min(s[1] for s in shapes)

            mask_t1 = mask_t1[:min_h, :min_w]
            mask_t2 = mask_t2[:min_h, :min_w]
            ml_change_mask = ml_change_mask[:min_h, :min_w]
            
            if ndvi_t1 is not None: ndvi_t1 = ndvi_t1[:min_h, :min_w]
            if ndvi_t2 is not None: ndvi_t2 = ndvi_t2[:min_h, :min_w]
            if ndbi_t1 is not None: ndbi_t1 = ndbi_t1[:min_h, :min_w]
            if ndbi_t2 is not None: ndbi_t2 = ndbi_t2[:min_h, :min_w]

            # Also crop the full indices dictionaries so spatial statistics don't crash
            for k in fe_t1.indices.keys():
                fe_t1.indices[k] = fe_t1.indices[k][:min_h, :min_w]
            for k in fe_t2.indices.keys():
                fe_t2.indices[k] = fe_t2.indices[k][:min_h, :min_w]

            # NOTE: Do NOT overwrite mask_t2 here. The segmentation_change.analyze()
            # method already handles false-positive suppression internally by
            # intersecting ml_change_mask with (mask_t1 != mask_t2).
            # Overwriting mask_t2 here would corrupt the ORIGINAL classification
            # results, making area statistics and change percentages inaccurate.

            ndvi_result = (
                self._ndvi_change.analyze(ndvi_t1, ndvi_t2)
                if ndvi_t1 is not None and ndvi_t2 is not None
                else None
            )
            ndbi_result = (
                self._ndbi_change.analyze(ndbi_t1, ndbi_t2)
                if ndbi_t1 is not None and ndbi_t2 is not None
                else None
            )
            # Extract bbox from AOI for spatial coordinate estimation
            try:
                # Assuming aoi_geojson is a dict with a bbox field, or calculate it
                coords = np.array(aoi_geojson.get("coordinates", [])[0])
                if coords.size > 0:
                    west, south = coords.min(axis=0)
                    east, north = coords.max(axis=0)
                    aoi_bbox = [float(west), float(south), float(east), float(north)]
                else:
                    aoi_bbox = None
            except Exception:
                aoi_bbox = None

            seg_result = self._seg_change.analyze(mask_t1, mask_t2, ml_change_mask, bbox=aoi_bbox)
            
            # Use exact Affine transform to compute accurate lat/lon for hotspots
            if seg_result.hotspots and scene_transform is not None and scene_crs is not None:
                try:
                    from rasterio.warp import transform as rp_transform
                    from rasterio.crs import CRS
                    
                    target_crs = CRS.from_epsg(4326)
                    for h in seg_result.hotspots:
                        # Convert pixel to UTM (or whatever scene_crs is)
                        x_crs, y_crs = scene_transform * (h.center_col, h.center_row)
                        # Project to Lat/Lon
                        lons, lats = rp_transform(scene_crs, target_crs, [x_crs], [y_crs])
                        h.center_lon = lons[0]
                        h.center_lat = lats[0]
                except Exception as exc:
                    logger.warning(f"Failed to project hotspot coordinates: {exc}")

            seg_summary = seg_result.summary()
            seg_summary["hotspots"] = [h.to_dict() for h in seg_result.hotspots]
            seg_summary["transition_matrix"] = seg_result.transition_dict()
            result.temporal_stats = {
                "ndvi_change": ndvi_result.summary() if ndvi_result else {},
                "ndbi_change": ndbi_result.summary() if ndbi_result else {},
                "segmentation_change": seg_summary,
            }

            # ----------------------------------------------------------
            # Step 8: Area calculations
            # ----------------------------------------------------------

            mark("area", "Computing land-cover area change …")
            area_change = self._area_calc.compute_change(mask_t1, mask_t2)
            result.area_change = {
                "rows": area_change.to_rows(),
                "total_area_km2": round(area_change.total_area_km2, 4),
            }

            # ----------------------------------------------------------
            # Step 9: Spatial statistics
            # ----------------------------------------------------------

            mark("stats", "Computing spatial statistics …")
            stats = self._stats_calc.compute_full(
                indices_t1=fe_t1.indices,
                indices_t2=fe_t2.indices,
                mask_t1=mask_t1,
                mask_t2=mask_t2,
            )
            result.statistics = stats.trend_summary

            # ----------------------------------------------------------
            # Step 10: Recommendations
            # ----------------------------------------------------------

            mark("recommendations", "Generating recommendations …")
            rec_result = self._rec_engine.evaluate(
                ndvi_change=ndvi_result,
                ndbi_change=ndbi_result,
                seg_change=seg_result,
                area_change=area_change,
                date1=str(parsed_date1),
                date2=str(parsed_date2),
            )
            result.recommendations = [
                r.to_dict() for r in rec_result.recommendations
            ]

            # ----------------------------------------------------------
            # Step 11: Metadata
            # ----------------------------------------------------------

            elapsed = time.time() - start_time

            result.metadata = {
                "elapsed_seconds": round(elapsed, 1),
                "date1": str(parsed_date1),
                "date2": str(parsed_date2),
                "seasonal_shift": (
                    abs(parsed_date1.month - parsed_date2.month) > 2
                    and abs(parsed_date1.month - parsed_date2.month) < 10
                ),
                "scene_t1_id": result.scene_t1_id,
                "scene_t2_id": result.scene_t2_id,
                "cloud_cover_t1": (
                    t1_features[0]
                    .get("properties", {})
                    .get("eo:cloud_cover")
                ) if t1_features else None,
                "cloud_cover_t2": (
                    t2_features[0]
                    .get("properties", {})
                    .get("eo:cloud_cover")
                ) if t2_features else None,
                "acquisition_date_t1": (
                    t1_features[0]
                    .get("properties", {})
                    .get("datetime", "")[:10]
                ) if t1_features else "",
                "acquisition_date_t2": (
                    t2_features[0]
                    .get("properties", {})
                    .get("datetime", "")[:10]
                ) if t2_features else "",
                "cloud_mask_t1_pct": round(t1_prep.cloud_coverage_pct, 2),
                "cloud_mask_t2_pct": round(t2_prep.cloud_coverage_pct, 2),
                "preprocessing_steps": t1_prep.steps_applied,
                "crs": str(scene_crs) if scene_crs else None,
                "pixel_resolution_m": 10.0,
                "bbox": list(aoi.bounds),
            }

            # ----------------------------------------------------------
            # Step 12: Export all output artefacts
            # ----------------------------------------------------------

            mark("report", "Exporting reports (GeoTIFF / GeoJSON / CSV / PDF) …")
            result.outputs = self._export_outputs(
                job_id=job_id,
                date1=parsed_date1,
                date2=parsed_date2,
                mask_t1=mask_t1,
                mask_t2=mask_t2,
                ml_change_mask=ml_change_mask,
                ndvi_result=ndvi_result,
                ndbi_result=ndbi_result,
                seg_result=seg_result,
                area_change=result.area_change,
                recommendations=result.recommendations,
                aoi_geojson=aoi_geojson,
                crs=scene_crs,
                transform=scene_transform,
                fe_t1=fe_t1,
                fe_t2=fe_t2,
                metadata=result.metadata,
            )

            logger.info(
                f"[{job_id}] Analysis complete in {elapsed:.1f} s."
            )

        except (AOIError, SceneNotFoundError, GeoSentinelError) as exc:
            logger.error(f"[{job_id}] Analysis failed: {exc}")
            result.success = False
            result.error = str(exc)
        except Exception as exc:
            logger.exception(f"[{job_id}] Unexpected error: {exc}")
            result.success = False
            result.error = str(exc)
        finally:
            if provider is not None:
                provider.close()

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_provider(
        self,
        max_cloud_cover: float | None,
    ) -> CDSEProvider:
        """Instantiate a CDSEProvider for one analysis run."""

        cloud_cover = (
            max_cloud_cover
            if max_cloud_cover is not None
            else self._max_cloud_cover
        )
        return CDSEProvider(max_cloud_cover=float(cloud_cover))

    # ------------------------------------------------------------------

    @staticmethod
    def _get_scene_georef(
        scene: SentinelScene,
    ) -> Tuple[Optional[CRS], Optional[Affine]]:
        """
        Extract CRS and Affine transform from the first available band.

        Used to georeference exported rasters and GeoJSON outputs.

        Parameters
        ----------
        scene : SentinelScene

        Returns
        -------
        (CRS | None, Affine | None)
        """

        for band in (Band.NIR, Band.RED, Band.GREEN, Band.BLUE, Band.SWIR_1):
            if scene.has_band(band):
                try:
                    raster = scene.raster(band)
                    return raster.crs, raster.transform
                except Exception:
                    continue

        return None, None

    # ------------------------------------------------------------------

    def _export_outputs(
        self,
        job_id: str,
        date1: date,
        date2: date,
        mask_t1,
        mask_t2,
        ml_change_mask,
        ndvi_result,
        ndbi_result,
        seg_result,
        area_change: dict,
        recommendations: list[dict],
        aoi_geojson: dict,
        crs: Optional[CRS],
        transform: Optional[Affine],
        fe_t1: Optional[FeatureEngineeringResult] = None,
        fe_t2: Optional[FeatureEngineeringResult] = None,
        metadata: Optional[dict] = None,
    ) -> dict[str, str]:
        """
        Persist all analysis artefacts and return a mapping of
        ``{output_key: absolute_path_str}``.

        Outputs produced
        ----------------
        GeoTIFF
          - ``mask_t1``        : T1 segmentation mask
          - ``mask_t2``        : T2 segmentation mask
          - ``ndvi_delta_tif`` : NDVI change raster (float32)
          - ``ndbi_delta_tif`` : NDBI change raster (float32)
        GeoJSON
          - ``hotspots_geojson`` : change hotspot point features
          - ``aoi_geojson``      : AOI extent polygon
        PNG visualisations
          - ``mask_t1_png``      : colourised T1 segmentation mask
          - ``mask_t2_png``      : colourised T2 segmentation mask
          - ``ndvi_delta_png``   : NDVI delta RdYlGn colour ramp
          - ``ndbi_delta_png``   : NDBI delta colour ramp
        CSV
          - ``csv``              : area change statistics
          - ``recommendations_csv`` : recommendations table
        PDF
          - ``pdf``              : structured analysis report
        """

        out: dict[str, str] = {}

        # ---- GeoTIFF exports ----------------------------------------

        if crs is not None and transform is not None:
            try:
                p = self._geotiff_exp.export_mask(
                    mask=mask_t1,
                    crs=crs,
                    transform=transform,
                    filename=f"{job_id}_mask_t1.tif",
                )
                out["mask_t1"] = str(p)
            except Exception as exc:
                logger.warning(f"GeoTIFF T1 mask export failed: {exc}")

            try:
                p = self._geotiff_exp.export_mask(
                    mask=mask_t2,
                    crs=crs,
                    transform=transform,
                    filename=f"{job_id}_mask_t2.tif",
                )
                out["mask_t2"] = str(p)
            except Exception as exc:
                logger.warning(f"GeoTIFF T2 mask export failed: {exc}")

            if ml_change_mask is not None:
                try:
                    p = self._geotiff_exp.export_mask(
                        mask=np.asarray(ml_change_mask).astype(np.int32),
                        crs=crs,
                        transform=transform,
                        filename=f"{job_id}_change_mask.tif",
                    )
                    out["change_mask_tif"] = str(p)
                except Exception as exc:
                    import traceback
                    logger.error(f"GeoTIFF Change mask export failed: {exc}\n{traceback.format_exc()}")

            if ndvi_result is not None:
                try:
                    p = self._geotiff_exp.export_change_raster(
                        change_array=ndvi_result.delta,
                        crs=crs,
                        transform=transform,
                        filename=f"{job_id}_ndvi_delta.tif",
                    )
                    out["ndvi_delta_tif"] = str(p)
                except Exception as exc:
                    logger.warning(f"NDVI delta GeoTIFF export failed: {exc}")

            if ndbi_result is not None:
                try:
                    p = self._geotiff_exp.export_change_raster(
                        change_array=ndbi_result.delta,
                        crs=crs,
                        transform=transform,
                        filename=f"{job_id}_ndbi_delta.tif",
                    )
                    out["ndbi_delta_tif"] = str(p)
                except Exception as exc:
                    logger.warning(f"NDBI delta GeoTIFF export failed: {exc}")
        else:
            logger.warning(
                "No CRS/transform available — skipping georeferenced exports."
            )

        # ---- GeoJSON exports ----------------------------------------

        try:
            p = self._geojson_exp.export_analysis_extent(
                aoi_geometry=aoi_geojson,
                filename=f"{job_id}_aoi.geojson",
            )
            out["aoi_geojson"] = str(p)
        except Exception as exc:
            logger.warning(f"AOI GeoJSON export failed: {exc}")

        if seg_result is not None and len(seg_result.hotspots) > 0:
            if transform is not None and crs is not None:
                try:
                    crs_epsg = crs.to_epsg() or 32644
                    hotspot_dicts = [
                        h.to_dict() if hasattr(h, "to_dict") else
                        (h.__dict__ if hasattr(h, "__dict__") else h)
                        for h in seg_result.hotspots
                    ]
                    p = self._geojson_exp.export_hotspots(
                        hotspots=hotspot_dicts,
                        transform=transform,
                        crs_epsg=crs_epsg,
                        filename=f"{job_id}_hotspots.geojson",
                    )
                    out["hotspots_geojson"] = str(p)
                except Exception as exc:
                    logger.warning(f"Hotspots GeoJSON export failed: {exc}")

        # ---- PNG visualisations -------------------------------------

        try:
            p = self._visualizer.save_mask_png(
                mask_t1,
                paths.FIGURES_DIR / f"{job_id}_mask_t1.png",
                title=f"Land Cover — {date1}",
            )
            out["mask_t1_png"] = str(p)
        except Exception as exc:
            logger.warning(f"T1 mask PNG failed: {exc}")

        try:
            p = self._visualizer.save_mask_png(
                mask_t2,
                paths.FIGURES_DIR / f"{job_id}_mask_t2.png",
                title=f"Land Cover — {date2}",
            )
            out["mask_t2_png"] = str(p)
        except Exception as exc:
            logger.warning(f"T2 mask PNG failed: {exc}")

        if ml_change_mask is not None:
            try:
                p = paths.FIGURES_DIR / f"{job_id}_change_mask.png"
                import PIL.Image
                import traceback
                
                # Ensure it's a 2D numpy array
                mask_2d = np.asarray(ml_change_mask).squeeze()
                if mask_2d.ndim != 2:
                    logger.error(f"Change mask has unexpected shape: {mask_2d.shape}")
                else:
                    logger.info(f"Change mask shape: {mask_2d.shape}, positive pixels: {int((mask_2d > 0).sum())}")
                    
                    # Create an RGBA image (transparent background)
                    rgba = np.zeros((mask_2d.shape[0], mask_2d.shape[1], 4), dtype=np.uint8)
                    
                    # Apply cyan color where mask is positive
                    rgba[mask_2d > 0] = [56, 189, 248, 200]
                    
                    img = PIL.Image.fromarray(rgba, mode="RGBA")
                    
                    # Only resize if reasonably small (avoids memory issues)
                    if img.width < 512 and img.height < 512:
                        if hasattr(PIL.Image, "Resampling"):
                            resample_filter = PIL.Image.Resampling.NEAREST
                        else:
                            resample_filter = PIL.Image.NEAREST
                        img = img.resize((img.width * 4, img.height * 4), resample=resample_filter)
                    
                    img.save(p)
                    out["change_mask_png"] = str(p)
                    logger.info(f"Change mask PNG saved: {p}")
            except Exception as exc:
                import traceback
                logger.error(f"Change mask PNG failed: {exc}\n{traceback.format_exc()}")

        if fe_t1 is not None:
            try:
                p = self._visualizer.save_rgb_png(
                    fe_t1.stack,
                    paths.FIGURES_DIR / f"{job_id}_image_t1.png",
                )
                out["image_t1_png"] = str(p)
            except Exception as exc:
                logger.warning(f"T1 RGB PNG failed: {exc}")

        if fe_t2 is not None:
            try:
                p = self._visualizer.save_rgb_png(
                    fe_t2.stack,
                    paths.FIGURES_DIR / f"{job_id}_image_t2.png",
                )
                out["image_t2_png"] = str(p)
            except Exception as exc:
                logger.warning(f"T2 RGB PNG failed: {exc}")

        if ndvi_result is not None:
            try:
                p = self._visualizer.save_change_map_png(
                    ndvi_result.delta,
                    paths.FIGURES_DIR / f"{job_id}_ndvi_delta.png",
                    title=f"NDVI Change ({date1} → {date2})",
                )
                out["ndvi_delta_png"] = str(p)
            except Exception as exc:
                logger.warning(f"NDVI delta PNG failed: {exc}")

        if ndbi_result is not None:
            try:
                p = self._visualizer.save_change_map_png(
                    ndbi_result.delta,
                    paths.FIGURES_DIR / f"{job_id}_ndbi_delta.png",
                    title=f"NDBI Change ({date1} → {date2})",
                    cmap="RdBu_r",
                )
                out["ndbi_delta_png"] = str(p)
            except Exception as exc:
                logger.warning(f"NDBI delta PNG failed: {exc}")

        # ---- CSV exports --------------------------------------------

        try:
            p = self._csv_exp.export_area_stats(
                area_change["rows"],
                filename=f"{job_id}_area_stats.csv",
            )
            out["csv"] = str(p)
        except Exception as exc:
            logger.warning(f"Area stats CSV failed: {exc}")

        try:
            p = self._csv_exp.export_recommendations(
                recommendations,
                filename=f"{job_id}_recommendations.csv",
            )
            out["recommendations_csv"] = str(p)
        except Exception as exc:
            logger.warning(f"Recommendations CSV failed: {exc}")

        # ---- PDF report ---------------------------------------------

        try:
            pdf_data = {
                "metadata": metadata or {
                    "date1": str(date1),
                    "date2": str(date2),
                },
                "area_change": area_change,
                "recommendations": recommendations,
                "outputs": out,
            }
            p = self._pdf_gen.generate(
                pdf_data,
                filename=f"{job_id}_report.pdf",
            )
            if p:
                out["pdf"] = str(p)
        except Exception as exc:
            logger.warning(f"PDF generation failed: {exc}")

        logger.info(
            f"[{job_id}] Exported {len(out)} output artefact(s): "
            f"{list(out.keys())}"
        )

        return out

    # ------------------------------------------------------------------

    def _get_landcover_predictor(self) -> ScenePredictor:
        """Lazy-load the DeepLabV3+ Land Cover Predictor (12 channels)."""

        if self._lc_predictor is not None:
            return self._lc_predictor

        from src.models.model_factory import ModelFactory
        from src.models.unet import NUM_CLASSES
        import torch

        factory = ModelFactory()
        
        encoder_name = self._config.get("model", "encoder", "backbone", default="resnet50")

        deeplab_model = factory.create_model(
            model_type="deeplabv3plus",
            in_channels=12,
            num_classes=NUM_CLASSES,
            encoder_name=encoder_name,
            encoder_weights=None,
        )
        deeplab_ckpt = paths.DATA_DIR / "weights" / "deeplabv3plus_best.pt"
        if deeplab_ckpt.exists():
            checkpoint = torch.load(deeplab_ckpt, map_location=self._device, weights_only=True)
            state_dict = checkpoint.get("model_state_dict", checkpoint)
            
            model_keys = list(deeplab_model.state_dict().keys())
            needs_model_prefix = any(k.startswith("model.") for k in model_keys)
            has_model_prefix = any(k.startswith("model.") for k in state_dict.keys())
            
            new_sd = {}
            for k, v in state_dict.items():
                if needs_model_prefix and not has_model_prefix:
                    new_sd[f"model.{k}"] = v
                elif not needs_model_prefix and has_model_prefix:
                    new_sd[k.replace("model.", "", 1)] = v
                else:
                    new_sd[k] = v
                    
            deeplab_model.load_state_dict(new_sd, strict=True)

        deeplab_model = deeplab_model.to(self._device)

        self._lc_predictor = ScenePredictor(
            model=deeplab_model,
            device=self._device,
            num_classes=NUM_CLASSES,
        )

        return self._lc_predictor

    def _get_change_predictor(self) -> SiameseScenePredictor:
        """Lazy-load the Siamese U-Net Change Detection Predictor (12 channels)."""

        if self._change_predictor is not None:
            return self._change_predictor

        import torch
        from src.models.siamese import GeoSentinelSiameseUNet
        from src.inference.predictor import SiameseScenePredictor

        deeplab_ckpt = paths.DATA_DIR / "weights" / "deeplabv3plus_best.pt"
        unet_model = GeoSentinelSiameseUNet(deeplab_ckpt_path=str(deeplab_ckpt), num_classes=2)
        
        unet_ckpt = self._change_model_checkpoint or (paths.DATA_DIR / "weights" / "change_unet_best.pt")
        if unet_ckpt.exists():
            checkpoint = torch.load(unet_ckpt, map_location=self._device, weights_only=True)
            state_dict = checkpoint.get("model_state_dict", checkpoint)
            new_sd = {}
            for k, v in state_dict.items():
                if k.startswith("model."):
                    new_sd[k[6:]] = v
                else:
                    new_sd[k] = v
            unet_model.load_state_dict(new_sd, strict=False)

        unet_model = unet_model.to(self._device)

        self._change_predictor = SiameseScenePredictor(
            model=unet_model,
            device=self._device,
            num_classes=2,
        )

        return self._change_predictor

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Orchestrator("
            f"device={self._device!r}, "
            f"max_cloud={self._max_cloud_cover}%)"
        )
