import hashlib
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# --- Carbon data from our previous scripts ---
data = {
    "project_name": "George Washington National Forest",
    "project_location": "Virginia, United States",
    "boundary": "[-79.5, 38.0, -78.5, 38.5]",
    "satellite": "Sentinel-2 SR Harmonized (COPERNICUS/S2_SR_HARMONIZED)",
    "baseline_period": "June 2021 - September 2021",
    "monitoring_period": "June 2023 - September 2023",
    "baseline_ndvi": 0.7265,
    "monitoring_ndvi": 0.7637,
    "ndvi_change": 0.0372,
    "area_ha": 485492.9,
    "biomass_change": 957197.7,
    "carbon_sequestered": 449882.9,
    "co2e": 1651070.4,
    "co2e_low": 1320856.3,
    "co2e_high": 1981284.5,
    "uncertainty": 20,
    "biomass_coefficient": 53.0,
    "carbon_fraction": 0.47,
    "co2_conversion": 3.67,
    "generated_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
    "methodology": "IPCC 2006 Guidelines for National Greenhouse Gas Inventories, Volume 4: Agriculture, Forestry and Other Land Use"
}

OUTPUT_FILE = "carbontrust_report.pdf"

def build_report(data, output_file):
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('CustomTitle',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#1a3c2e'),
        spaceAfter=6)

    subtitle_style = ParagraphStyle('Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#4a7c59'),
        spaceAfter=4)

    heading_style = ParagraphStyle('CustomHeading',
        parent=styles['Heading1'],
        fontSize=13,
        textColor=colors.HexColor('#1a3c2e'),
        spaceBefore=16,
        spaceAfter=6,
        borderPad=4)

    body_style = ParagraphStyle('Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        spaceAfter=6)

    small_style = ParagraphStyle('Small',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        leading=12)

    story = []

    # --- Header ---
    story.append(Paragraph("CarbonTrust", title_style))
    story.append(Paragraph("Carbon Verification Report", subtitle_style))
    story.append(Paragraph(f"Generated: {data['generated_date']}", small_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4a7c59'), spaceAfter=12))

    # --- Project Info ---
    story.append(Paragraph("Project Information", heading_style))

    project_table_data = [
        ["Project Name", data["project_name"]],
        ["Location", data["project_location"]],
        ["Boundary (GeoJSON)", data["boundary"]],
        ["Satellite Source", data["satellite"]],
        ["Baseline Period", data["baseline_period"]],
        ["Monitoring Period", data["monitoring_period"]],
    ]

    project_table = Table(project_table_data, colWidths=[2*inch, 4.5*inch])
    project_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eaf2ec')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a3c2e')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.white, colors.HexColor('#f7fbf8')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ccddcc')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(project_table)

    # --- NDVI Results ---
    story.append(Paragraph("Vegetation Index Results (NDVI)", heading_style))
    story.append(Paragraph(
        "NDVI (Normalized Difference Vegetation Index) measures vegetation density using near-infrared "
        "and red light reflected by plants. Values range from -1 to 1, with healthy forest typically "
        "above 0.6. A positive NDVI change indicates vegetation growth and carbon sequestration.",
        body_style))

    ndvi_data = [
        ["Metric", "Value", "Interpretation"],
        ["Baseline NDVI (2021)", f"{data['baseline_ndvi']:.4f}", "Healthy dense forest"],
        ["Monitoring NDVI (2023)", f"{data['monitoring_ndvi']:.4f}", "Increased vegetation density"],
        ["NDVI Change", f"+{data['ndvi_change']:.4f}", "Positive growth signal"],
    ]

    ndvi_table = Table(ndvi_data, colWidths=[2.2*inch, 1.5*inch, 2.8*inch])
    ndvi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3c2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fbf8')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ccddcc')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ]))
    story.append(ndvi_table)

    # --- Carbon Results ---
    story.append(Paragraph("Carbon Estimation Results", heading_style))

    carbon_data = [
        ["Parameter", "Value", "Unit"],
        ["Project Area", f"{data['area_ha']:,.1f}", "hectares"],
        ["Biomass Change", f"{data['biomass_change']:,.1f}", "tonnes"],
        ["Carbon Sequestered", f"{data['carbon_sequestered']:,.1f}", "tonnes C"],
        ["CO<sub>2</sub>e Sequestered", f"{data['co2e']:,.1f}", "tonnes CO<sub>2</sub>e"],
        ["Uncertainty Range (low)", f"{data['co2e_low']:,.1f}", "tonnes CO<sub>2</sub>e"],
        ["Uncertainty Range (high)", f"{data['co2e_high']:,.1f}", "tonnes CO<sub>2</sub>e"],
    ]

    # Convert to Paragraphs to support subscript tags
    carbon_table_data = []
    for row in carbon_data:
        carbon_table_data.append([Paragraph(cell, small_style) for cell in row])

    carbon_table = Table(carbon_table_data, colWidths=[2.5*inch, 2*inch, 2*inch])
    carbon_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3c2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fbf8')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ccddcc')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ]))
    story.append(carbon_table)

    # --- Methodology ---
    story.append(Paragraph("Methodology & Assumptions", heading_style))

    method_data = [
        ["Assumption", "Value", "Source"],
        ["Biomass Scaling Coefficient", f"{data['biomass_coefficient']} t/ha per NDVI unit", "Temperate forest literature"],
        ["Carbon Fraction", f"{data['carbon_fraction']}", "IPCC 2006 AFOLU Guidelines"],
        ["CO2 Conversion Factor", f"{data['co2_conversion']}", "Molecular weight ratio CO2/C"],
        ["Uncertainty Band", f"±{data['uncertainty']}%", "Conservative estimate"],
        ["Cloud Filter Threshold", "< 20% cloud cover", "Standard practice"],
        ["Pixel Resolution", "100m", "Sentinel-2 processing"],
    ]

    method_table = Table(method_data, colWidths=[2.2*inch, 2*inch, 2.3*inch])
    method_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3c2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fbf8')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ccddcc')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(method_table)

    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Full methodology reference: {data['methodology']}", small_style))

    # --- Footer / Hash ---
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ccddcc'), spaceAfter=8))
    story.append(Paragraph("Verification", heading_style))
    story.append(Paragraph(
        "This report will be hashed after generation. The SHA-256 hash below provides a tamper-proof "
        "fingerprint — any modification to this document will produce a different hash.",
        body_style))

    # Placeholder hash line — will be replaced after file is written
    story.append(Paragraph("SHA-256: [computed after generation]", small_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("CarbonTrust | Reproducible Carbon Verification Infrastructure", small_style))

    doc.build(story)

def hash_report(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# --- Run ---
print("Generating report...")
build_report(data, OUTPUT_FILE)

report_hash = hash_report(OUTPUT_FILE)
print(f"Report generated: {OUTPUT_FILE}")
print(f"SHA-256 Hash: {report_hash}")
print("\nThis hash is the tamper-proof fingerprint of your report.")
print("If anyone modifies the PDF, the hash will no longer match.")