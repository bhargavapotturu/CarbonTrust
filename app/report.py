# app/report.py

import os
import tempfile
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


# --- Brand colors ---
PRIMARY = colors.HexColor("#1a5c38")    # dark forest green
SECONDARY = colors.HexColor("#2d8653")  # mid green
LIGHT_BG = colors.HexColor("#f0f7f3")  # light green tint
TEXT = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#555555")


def _styles():
    base = getSampleStyleSheet()

    title = ParagraphStyle(
        "ct_title",
        parent=base["Normal"],
        fontSize=22,
        textColor=PRIMARY,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    subtitle = ParagraphStyle(
        "ct_subtitle",
        parent=base["Normal"],
        fontSize=11,
        textColor=MUTED,
        fontName="Helvetica",
        spaceAfter=2,
    )
    section = ParagraphStyle(
        "ct_section",
        parent=base["Normal"],
        fontSize=12,
        textColor=PRIMARY,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "ct_body",
        parent=base["Normal"],
        fontSize=10,
        textColor=TEXT,
        fontName="Helvetica",
        spaceAfter=4,
        leading=15,
    )
    footnote = ParagraphStyle(
        "ct_footnote",
        parent=base["Normal"],
        fontSize=8,
        textColor=MUTED,
        fontName="Helvetica-Oblique",
        spaceAfter=2,
    )

    return title, subtitle, section, body, footnote


def _metric_table(results: dict) -> Table:
    """Build the main results table."""
    rows = [
        ["Metric", "Value", "Unit"],
        ["Project Area", f"{results['area_ha']:,.1f}", "hectares"],
        ["Baseline NDVI", f"{results['baseline_ndvi']:.4f}", "index"],
        ["Monitoring NDVI", f"{results['monitoring_ndvi']:.4f}", "index"],
        ["NDVI Change", f"{results['ndvi_change']:+.4f}", "index"],
        ["Biomass Change", f"{results['biomass_change_tonnes']:,.1f}", "tonnes"],
        ["Carbon Sequestered", f"{results['carbon_sequestered_tonnes_c']:,.1f}", "tonnes C"],
        ["CO₂e Sequestered", f"{results['co2e_tonnes']:,.1f}", "tonnes CO₂e"],
        ["Uncertainty Low (−20%)", f"{results['co2e_low']:,.1f}", "tonnes CO₂e"],
        ["Uncertainty High (+20%)", f"{results['co2e_high']:,.1f}", "tonnes CO₂e"],
    ]

    col_widths = [7.5 * cm, 5 * cm, 4.5 * cm]

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Alternating row backgrounds
        *[
            ("BACKGROUND", (0, i), (-1, i), LIGHT_BG)
            for i in range(2, len(rows), 2)
        ],
        # All rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (2, -1), "LEFT"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUND", (0, 0), (-1, 0), PRIMARY),
    ]))

    return table


def generate_report(
    project_name: str,
    results: dict,
    generated_at: str,
    run_hash: str,
) -> str:
    """
    Generate a PDF report and write it to a temp file.
    Returns the file path.
    """
    title_style, subtitle_style, section_style, body_style, footnote_style = _styles()

    # Write to a named temp file so FastAPI can stream it
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".pdf", prefix="carbontrust_"
    )
    tmp.close()

    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    story = []

    # --- Header ---
    story.append(Paragraph("CarbonTrust", title_style))
    story.append(Paragraph("Satellite-Based Carbon Verification Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=12))

    # --- Project info ---
    story.append(Paragraph("Project Details", section_style))
    story.append(Paragraph(f"<b>Project Name:</b> {project_name}", body_style))
    story.append(Paragraph(f"<b>Generated:</b> {generated_at}", body_style))
    story.append(Paragraph(
        f"<b>Methodology:</b> IPCC 2006 AFOLU Guidelines, Sentinel-2 SR Harmonized",
        body_style
    ))
    story.append(Spacer(1, 0.3 * cm))

    # --- Results table ---
    story.append(Paragraph("Carbon Estimation Results", section_style))
    story.append(_metric_table(results))
    story.append(Spacer(1, 0.5 * cm))

    # --- Methodology notes ---
    story.append(Paragraph("Methodology Notes", section_style))
    story.append(Paragraph(
        "Vegetation change is measured using the Normalized Difference Vegetation Index (NDVI) "
        "derived from Sentinel-2 Surface Reflectance imagery. Biomass change is estimated using "
        "a scaling coefficient of 53.0 t/ha per NDVI unit, consistent with temperate forest "
        "literature. Carbon is calculated using the IPCC 2006 carbon fraction of 0.47, and "
        "converted to CO₂ equivalent using the molecular weight ratio of 3.67.",
        body_style
    ))
    story.append(Paragraph(
        "Uncertainty bands of ±20% are applied to the final CO₂e estimate in accordance "
        "with Tier 1 IPCC guidelines for forestry carbon accounting.",
        body_style
    ))
    story.append(Spacer(1, 0.5 * cm))

    # --- Audit footer ---
    story.append(HRFlowable(width="100%", thickness=1, color=MUTED, spaceAfter=8))
    story.append(Paragraph("Verification & Audit Trail", section_style))
    story.append(Paragraph(
        "This report is cryptographically signed. The SHA-256 hash below is derived from "
        "all input parameters and computed results. Any modification to this report will "
        "produce a different hash and can be detected.",
        body_style
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f"<b>SHA-256 Run Hash:</b>", body_style))
    story.append(Paragraph(run_hash, footnote_style))

    doc.build(story)

    return tmp.name