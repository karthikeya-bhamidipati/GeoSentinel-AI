"""
===============================================================================
GeoSentinel AI

Module:
    pdf_report.py

Description:
    PDF report generator using ReportLab.

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

from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.logger import logger

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        HRFlowable,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from src.utils.paths import paths


# Severity to color mapping for PDF
SEVERITY_COLORS = {
    "CRITICAL": "#DC143C",
    "HIGH": "#FF6347",
    "MEDIUM": "#FFA500",
    "LOW": "#228B22",
}


class PDFReportGenerator:
    """
    Generates professional PDF analysis reports.

    Uses ReportLab's Platypus framework for structured, printable reports.

    Parameters
    ----------
    output_dir : Path | None
        Directory to save PDF files.
    """

    def __init__(
        self,
        output_dir: Path | None = None,
    ) -> None:

        self.output_dir = output_dir or paths.REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not REPORTLAB_AVAILABLE:
            logger.warning(
                "ReportLab not installed. "
                "PDF reports will not be generated. "
                "Install with: pip install reportlab"
            )

    # ------------------------------------------------------------------

    def generate(
        self,
        analysis_data: dict[str, Any],
        filename: str | None = None,
    ) -> Path | None:
        """
        Generate a PDF report from analysis data.

        Parameters
        ----------
        analysis_data : dict
            Analysis results dict (from orchestrator output).
        filename : str | None
            Output filename. Auto-generated if None.

        Returns
        -------
        Path | None
            Path to the generated PDF, or None if ReportLab unavailable.
        """

        if not REPORTLAB_AVAILABLE:
            logger.warning("Skipping PDF: ReportLab not available.")
            return None

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"geosentinel_report_{timestamp}.pdf"

        output_path = self.output_dir / filename

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()

        story = []

        # ----------------------------------------------------------
        # Title
        # ----------------------------------------------------------

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=20,
            textColor=colors.HexColor("#1A237E"),
            spaceAfter=6,
        )

        story.append(
            Paragraph("GeoSentinel AI — Analysis Report", title_style)
        )

        story.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
                styles["Normal"],
            )
        )

        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1A237E")))
        story.append(Spacer(1, 0.3 * cm))

        # ----------------------------------------------------------
        # Analysis Period
        # ----------------------------------------------------------

        story.append(Paragraph("Analysis Period", styles["Heading2"]))

        meta = analysis_data.get("metadata", {})
        period_data = [
            ["Field", "Value"],
            ["Date 1 (T1)", meta.get("date1", "—")],
            ["Date 2 (T2)", meta.get("date2", "—")],
            ["T1 Scene ID", meta.get("scene_t1_id", "—")],
            ["T2 Scene ID", meta.get("scene_t2_id", "—")],
            ["T1 Acquisition", meta.get("acquisition_date_t1", "—")],
            ["T2 Acquisition", meta.get("acquisition_date_t2", "—")],
            ["T1 Cloud Cover", f"{meta.get('cloud_cover_t1', '—')}%"
             if meta.get("cloud_cover_t1") is not None else "—"],
            ["T2 Cloud Cover", f"{meta.get('cloud_cover_t2', '—')}%"
             if meta.get("cloud_cover_t2") is not None else "—"],
            ["Satellite", "Sentinel-2 L2A"],
            ["Resolution", "10 metres"],
            ["Processing Time", f"{meta.get('elapsed_seconds', '—')} s"],
        ]

        bbox = meta.get("bbox")
        if bbox and len(bbox) == 4:
            period_data.append(["AOI Bounding Box", f"[{bbox[0]:.4f}, {bbox[1]:.4f}, {bbox[2]:.4f}, {bbox[3]:.4f}]"])

        area_rows = analysis_data.get("area_change", {}).get("rows", [])
        if area_rows:
            total_area = sum(row.get("t1_area_km2", 0) for row in area_rows)
            period_data.append(["Total AOI Area", f"{total_area:.3f} km²"])

        story.append(
            self._build_table(period_data)
        )
        story.append(Spacer(1, 0.4 * cm))

        # ----------------------------------------------------------
        # Area Statistics
        # ----------------------------------------------------------

        area_rows = analysis_data.get("area_change", {}).get("rows", [])

        if area_rows:
            story.append(Paragraph("Land Cover Area Change", styles["Heading2"]))

            table_data = [
                ["Class", "T1 Area (km²)", "T2 Area (km²)", "Change (km²)", "Change (%)"]
            ]

            for row in area_rows:
                table_data.append([
                    row.get("class_name", "—"),
                    f"{row.get('t1_area_km2', 0.0):.3f}",
                    f"{row.get('t2_area_km2', 0.0):.3f}",
                    f"{row.get('change_km2', 0.0):+.3f}",
                    f"{row.get('change_pct', 0.0):+.1f}%",
                ])

            story.append(self._build_table(table_data))
            story.append(Spacer(1, 0.4 * cm))

        # ----------------------------------------------------------
        # Recommendations
        # ----------------------------------------------------------

        recs = analysis_data.get("recommendations", [])

        if recs:
            story.append(Paragraph("Recommendations", styles["Heading2"]))
            story.append(Spacer(1, 0.2 * cm))

            for i, rec in enumerate(recs, 1):
                severity = rec.get("severity", "LOW")
                color_hex = SEVERITY_COLORS.get(severity, "#228B22")

                sev_style = ParagraphStyle(
                    f"Sev_{i}",
                    parent=styles["Normal"],
                    textColor=colors.HexColor(color_hex),
                    fontName="Helvetica-Bold",
                    fontSize=11,
                )

                story.append(
                    Paragraph(
                        f"[{severity}] {rec.get('title', '')}",
                        sev_style,
                    )
                )

                story.append(
                    Paragraph(
                        f"<i>Why:</i> {rec.get('why', '')}",
                        styles["Normal"],
                    )
                )

                story.append(
                    Paragraph(
                        f"<b>Action:</b> {rec.get('recommendation', '')}",
                        styles["Normal"],
                    )
                )

                story.append(Spacer(1, 0.3 * cm))

                story.append(Spacer(1, 0.3 * cm))

        # ----------------------------------------------------------
        # Visualisations
        # ----------------------------------------------------------
        outputs = analysis_data.get("outputs", {})
        
        image_keys = [
            ("image_t1_png", "Time 1 (T1) True Colour Composite"),
            ("image_t2_png", "Time 2 (T2) True Colour Composite"),
            ("mask_t1_png", "Time 1 (T1) AI Land Cover Classification"),
            ("mask_t2_png", "Time 2 (T2) AI Land Cover Classification"),
            ("ndvi_delta_png", "NDVI Vegetation Change Map"),
        ]
        
        has_images = any(k in outputs for k, _ in image_keys)
        
        if has_images:
            from reportlab.platypus import Image, PageBreak
            
            story.append(PageBreak())
            story.append(Paragraph("Analysis Visualisations", styles["Heading2"]))
            story.append(Spacer(1, 0.4 * cm))
            
            for key, caption in image_keys:
                img_path = outputs.get(key)
                if img_path and Path(img_path).exists():
                    story.append(Paragraph(caption, styles["Heading3"]))
                    story.append(Spacer(1, 0.2 * cm))
                    
                    try:
                        img = Image(img_path)
                        # Scale image to fit A4 width nicely (approx 16cm width max)
                        max_width = 15.0 * cm
                        if img.drawWidth > max_width:
                            ratio = max_width / img.drawWidth
                            img.drawWidth = max_width
                            img.drawHeight = img.drawHeight * ratio
                            
                        story.append(img)
                        story.append(Spacer(1, 0.8 * cm))
                    except Exception as e:
                        logger.warning(f"Failed to embed image {img_path} in PDF: {e}")

        # ----------------------------------------------------------
        # Build
        # ----------------------------------------------------------

        doc.build(story)

        logger.info(f"PDF report generated: {output_path.name}")

        return output_path

    # ------------------------------------------------------------------

    def _build_table(
        self,
        data: list[list],
    ) -> "Table":

        table = Table(data, hAlign="LEFT")

        style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A237E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ])

        table.setStyle(style)

        return table
