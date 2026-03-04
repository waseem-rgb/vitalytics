"""Tier 3 — Professional multi-page PDF report generator using reportlab.

Generates a branded clinical report with:
  - Cover page with patient demographics
  - Executive summary of findings
  - Detailed lab results grouped by clinical panel
  - Clinical pattern analysis sorted by severity
  - Action plan (further tests, referrals, lifestyle)
  - RAG narrative (if available)
  - Disclaimer footer on every page
"""

import io
import textwrap
from datetime import datetime, timezone

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        NextPageTemplate,
        PageBreak,
        PageTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        KeepTogether,
    )
    from reportlab.platypus.flowables import HRFlowable

    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAGE_WIDTH, PAGE_HEIGHT = A4 if HAS_REPORTLAB else (595.27, 841.89)

# Brand colours
COLOR_DARK_HEADER = "#1a1a3e"
COLOR_ACCENT = "#6366f1"       # Indigo
COLOR_ACCENT_LIGHT = "#e0e7ff"
COLOR_BG_LIGHT = "#f8f9fc"
COLOR_WHITE = "#ffffff"

# Severity colours
SEVERITY_HEX = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "moderate": "#f59e0b",
    "low": "#84cc16",
}

SEVERITY_ORDER = {"critical": 4, "high": 3, "moderate": 2, "low": 1}

# Row colours for lab results
ROW_COLOR_NORMAL = "#edf7ed"     # Light green
ROW_COLOR_AMBER = "#fff7e0"      # Light amber
ROW_COLOR_RED = "#fde8e8"        # Light red
ROW_COLOR_GRAY = "#f3f4f6"       # Light gray for unknown

# Urgency colours for badges
URGENCY_HEX = {
    "urgent": "#dc2626",
    "soon": "#ea580c",
    "routine": "#6366f1",
}

# Panel ordering — maps panel name to member test IDs
PANEL_ORDER = [
    ("Complete Blood Count", [
        "hemoglobin", "hematocrit", "mcv", "mch", "mchc", "rdw", "wbc",
        "neutrophils", "lymphocytes", "platelets", "reticulocyte_count", "rbc",
        "neutrophils_pct", "lymphocytes_pct", "monocytes_pct", "eosinophils_pct",
        "basophils_pct", "aec",
    ]),
    ("Iron Studies", [
        "ferritin", "serum_iron", "tibc", "transferrin_saturation",
    ]),
    ("Vitamins", [
        "vitamin_b12", "folate", "vitamin_d",
    ]),
    ("Renal Function", [
        "creatinine", "bun", "egfr", "uric_acid", "urine_albumin_cr_ratio",
        "bicarbonate", "urea", "bun_creat_ratio",
    ]),
    ("Diabetes", [
        "fasting_glucose", "hba1c", "fasting_insulin", "pp_glucose",
    ]),
    ("Thyroid", [
        "tsh", "free_t4", "free_t3", "total_t3", "total_t4", "anti_tpo",
    ]),
    ("Liver Function", [
        "alt", "ast", "alp", "ggt", "total_bilirubin", "direct_bilirubin",
        "indirect_bilirubin", "albumin", "total_protein", "globulin",
        "ag_ratio", "ast_alt_ratio",
    ]),
    ("Lipid Profile", [
        "total_cholesterol", "ldl", "hdl", "triglycerides", "vldl",
        "non_hdl_cholesterol", "chol_hdl_ratio",
    ]),
    ("Electrolytes", [
        "sodium", "potassium", "chloride", "calcium", "phosphate", "magnesium",
    ]),
    ("Urine Analysis", [
        "urine_protein", "urine_glucose", "urine_ketones",
        "urine_specific_gravity", "urine_ph", "urine_pus_cells", "urine_rbc",
        "urine_casts", "urine_bacteria",
    ]),
    ("Tumor Markers", [
        "afp", "cea", "ca19_9", "ca15_3", "psa", "ca125",
    ]),
]


# ---------------------------------------------------------------------------
# Helpers — styles
# ---------------------------------------------------------------------------

def _build_styles():
    """Return a dictionary of ParagraphStyles used throughout the report."""
    base = getSampleStyleSheet()

    s = {}

    # Cover page
    s["cover_title"] = ParagraphStyle(
        "CoverTitle", parent=base["Title"],
        fontSize=28, leading=34, alignment=TA_CENTER,
        textColor=colors.HexColor(COLOR_WHITE),
        spaceAfter=4 * mm,
    )
    s["cover_subtitle"] = ParagraphStyle(
        "CoverSubtitle", parent=base["Normal"],
        fontSize=13, leading=17, alignment=TA_CENTER,
        textColor=colors.HexColor("#c7d2fe"),
        spaceAfter=2 * mm,
    )
    s["cover_info"] = ParagraphStyle(
        "CoverInfo", parent=base["Normal"],
        fontSize=11, leading=15, alignment=TA_CENTER,
        textColor=colors.HexColor(COLOR_WHITE),
        spaceAfter=1 * mm,
    )

    # Section headings
    s["section_heading"] = ParagraphStyle(
        "SectionHeading", parent=base["Heading1"],
        fontSize=18, leading=22, textColor=colors.HexColor(COLOR_DARK_HEADER),
        spaceBefore=6 * mm, spaceAfter=4 * mm,
        borderWidth=0, borderPadding=0,
    )
    s["panel_heading"] = ParagraphStyle(
        "PanelHeading", parent=base["Heading2"],
        fontSize=13, leading=16, textColor=colors.HexColor(COLOR_ACCENT),
        spaceBefore=5 * mm, spaceAfter=2 * mm,
    )
    s["sub_heading"] = ParagraphStyle(
        "SubHeading", parent=base["Heading3"],
        fontSize=11, leading=14, textColor=colors.HexColor(COLOR_DARK_HEADER),
        spaceBefore=3 * mm, spaceAfter=2 * mm,
    )

    # Body text
    s["body"] = ParagraphStyle(
        "Body", parent=base["Normal"],
        fontSize=9.5, leading=13, textColor=colors.HexColor("#1f2937"),
        spaceAfter=2 * mm,
    )
    s["body_bold"] = ParagraphStyle(
        "BodyBold", parent=s["body"],
        fontName="Helvetica-Bold",
    )
    s["body_small"] = ParagraphStyle(
        "BodySmall", parent=base["Normal"],
        fontSize=8, leading=11, textColor=colors.HexColor("#6b7280"),
        spaceAfter=1 * mm,
    )
    s["body_italic"] = ParagraphStyle(
        "BodyItalic", parent=s["body"],
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#4b5563"),
    )

    # Narrative block
    s["narrative"] = ParagraphStyle(
        "Narrative", parent=base["Normal"],
        fontSize=10, leading=15, textColor=colors.HexColor("#1f2937"),
        alignment=TA_JUSTIFY,
        spaceAfter=3 * mm,
        leftIndent=4 * mm, rightIndent=4 * mm,
    )

    # Table header cell
    s["table_header"] = ParagraphStyle(
        "TableHeader", parent=base["Normal"],
        fontSize=8, leading=10, textColor=colors.HexColor(COLOR_WHITE),
        fontName="Helvetica-Bold",
    )
    s["table_cell"] = ParagraphStyle(
        "TableCell", parent=base["Normal"],
        fontSize=8, leading=10, textColor=colors.HexColor("#1f2937"),
    )
    s["table_cell_bold"] = ParagraphStyle(
        "TableCellBold", parent=s["table_cell"],
        fontName="Helvetica-Bold",
    )

    # Executive summary stat
    s["stat_value"] = ParagraphStyle(
        "StatValue", parent=base["Normal"],
        fontSize=22, leading=26, alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor(COLOR_DARK_HEADER),
    )
    s["stat_label"] = ParagraphStyle(
        "StatLabel", parent=base["Normal"],
        fontSize=8, leading=10, alignment=TA_CENTER,
        textColor=colors.HexColor("#6b7280"),
    )

    # Disclaimer / footer
    s["disclaimer"] = ParagraphStyle(
        "Disclaimer", parent=base["Normal"],
        fontSize=7, leading=9, alignment=TA_CENTER,
        textColor=colors.HexColor("#dc2626"),
    )

    # Badge style (for inline severity badges)
    s["badge"] = ParagraphStyle(
        "Badge", parent=base["Normal"],
        fontSize=7.5, leading=10, alignment=TA_CENTER,
        textColor=colors.HexColor(COLOR_WHITE),
        fontName="Helvetica-Bold",
    )

    return s


# ---------------------------------------------------------------------------
# Helpers — reportlab flowables
# ---------------------------------------------------------------------------

def _colored_rect_table(text, bg_color_hex, text_color_hex="#ffffff", width=55, height=16, font_size=7.5):
    """Return a small Table acting as a coloured badge."""
    style = ParagraphStyle(
        "badge_inline", fontSize=font_size, leading=font_size + 2,
        alignment=TA_CENTER, textColor=colors.HexColor(text_color_hex),
        fontName="Helvetica-Bold",
    )
    p = Paragraph(text, style)
    t = Table([[p]], colWidths=[width], rowHeights=[height])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(bg_color_hex)),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
        ("LEFTPADDING", (0, 0), (0, 0), 2),
        ("RIGHTPADDING", (0, 0), (0, 0), 2),
        ("TOPPADDING", (0, 0), (0, 0), 1),
        ("BOTTOMPADDING", (0, 0), (0, 0), 1),
    ]))
    return t


def _section_divider():
    """Horizontal rule between sections."""
    return HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#d1d5db"),
        spaceAfter=4 * mm, spaceBefore=2 * mm,
    )


def _row_color_for_status(status: str):
    """Return a hex color string for table row background based on status."""
    if status in ("critical_low", "critical_high"):
        return ROW_COLOR_RED
    elif status in ("low", "high"):
        return ROW_COLOR_AMBER
    elif status == "normal":
        return ROW_COLOR_NORMAL
    return ROW_COLOR_GRAY


def _severity_badge(severity: str):
    """Return a severity badge flowable."""
    hex_color = SEVERITY_HEX.get(severity, "#6b7280")
    return _colored_rect_table(severity.upper(), hex_color, width=58, height=15, font_size=7)


def _urgency_badge(urgency: str):
    """Return an urgency badge flowable."""
    hex_color = URGENCY_HEX.get(urgency, "#6b7280")
    return _colored_rect_table(urgency.upper(), hex_color, width=52, height=15, font_size=7)


# ---------------------------------------------------------------------------
# Page templates — footer on every page
# ---------------------------------------------------------------------------

_FOOTER_TEXT = "Clinical Decision Support Only \u2014 Not a Medical Diagnosis"


def _footer(canvas, doc):
    """Draw footer with disclaimer and page number on every page."""
    canvas.saveState()
    # Divider line
    canvas.setStrokeColor(colors.HexColor("#d1d5db"))
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 14 * mm, PAGE_WIDTH - 20 * mm, 14 * mm)
    # Disclaimer text
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(colors.HexColor("#dc2626"))
    canvas.drawCentredString(PAGE_WIDTH / 2, 9.5 * mm, _FOOTER_TEXT)
    # Page number
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(PAGE_WIDTH - 20 * mm, 9.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _cover_footer(canvas, doc):
    """Footer for the cover page (just the disclaimer, centred)."""
    canvas.saveState()
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(colors.HexColor("#fca5a5"))
    canvas.drawCentredString(PAGE_WIDTH / 2, 12 * mm, _FOOTER_TEXT)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Cover page builder
# ---------------------------------------------------------------------------

def _build_cover_page(analysis: dict, styles: dict) -> list:
    """Build flowables for the branded cover page."""
    elements = []
    patient = analysis.get("patient", {})
    age = patient.get("age", "N/A")
    sex = patient.get("sex", "N/A")
    if isinstance(sex, str):
        sex = sex.title()
    timestamp = analysis.get("timestamp", "")
    analysis_id = analysis.get("id", "N/A")

    # Parse timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        date_str = dt.strftime("%B %d, %Y")
        time_str = dt.strftime("%H:%M UTC")
    except Exception:
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        time_str = datetime.now(timezone.utc).strftime("%H:%M UTC")

    # Dark header background — use a table as a coloured block
    cover_bg_data = [[""]]
    # We use spacers and paragraph elements inside a single-cell table with dark bg
    header_elements = []
    header_elements.append(Spacer(1, 35 * mm))
    header_elements.append(Paragraph("VITALYTICS", ParagraphStyle(
        "LogoText", fontSize=14, leading=18, alignment=TA_CENTER,
        textColor=colors.HexColor("#a5b4fc"), fontName="Helvetica-Bold",
        spaceAfter=2 * mm, letterSpacing=4,
    )))
    header_elements.append(Spacer(1, 4 * mm))
    header_elements.append(Paragraph("Lab Analysis Report", styles["cover_title"]))
    header_elements.append(Spacer(1, 3 * mm))
    header_elements.append(Paragraph(
        "Comprehensive Clinical Decision Support Report",
        styles["cover_subtitle"],
    ))
    header_elements.append(Spacer(1, 20 * mm))

    # Patient info rows
    info_table_data = [
        [Paragraph("<b>Patient Age</b>", ParagraphStyle(
            "ci1", fontSize=10, alignment=TA_CENTER,
            textColor=colors.HexColor("#c7d2fe"),
        )),
         Paragraph("<b>Biological Sex</b>", ParagraphStyle(
            "ci2", fontSize=10, alignment=TA_CENTER,
            textColor=colors.HexColor("#c7d2fe"),
        )),
         Paragraph("<b>Report Date</b>", ParagraphStyle(
            "ci3", fontSize=10, alignment=TA_CENTER,
            textColor=colors.HexColor("#c7d2fe"),
        ))],
        [Paragraph(f"{age}", ParagraphStyle(
            "cv1", fontSize=20, alignment=TA_CENTER,
            textColor=colors.HexColor(COLOR_WHITE), fontName="Helvetica-Bold",
        )),
         Paragraph(f"{sex}", ParagraphStyle(
            "cv2", fontSize=20, alignment=TA_CENTER,
            textColor=colors.HexColor(COLOR_WHITE), fontName="Helvetica-Bold",
        )),
         Paragraph(f"{date_str}", ParagraphStyle(
            "cv3", fontSize=14, alignment=TA_CENTER,
            textColor=colors.HexColor(COLOR_WHITE), fontName="Helvetica-Bold",
        ))],
    ]
    info_tbl = Table(info_table_data, colWidths=[50 * mm, 50 * mm, 60 * mm])
    info_tbl.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    header_elements.append(info_tbl)

    header_elements.append(Spacer(1, 8 * mm))
    header_elements.append(Paragraph(
        f"Time: {time_str}",
        styles["cover_info"],
    ))
    header_elements.append(Spacer(1, 2 * mm))
    header_elements.append(Paragraph(
        f"Analysis ID: {analysis_id}",
        ParagraphStyle("CoverID", fontSize=8, alignment=TA_CENTER,
                        textColor=colors.HexColor("#a5b4fc")),
    ))
    header_elements.append(Spacer(1, 25 * mm))

    # Wrap all header elements in a dark-background table
    inner_cell = [header_elements]
    cover_wrapper = Table([[inner_cell]], colWidths=[PAGE_WIDTH - 40 * mm])
    cover_wrapper.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(COLOR_DARK_HEADER)),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("VALIGN", (0, 0), (0, 0), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 0), (0, 0), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))

    elements.append(cover_wrapper)
    elements.append(NextPageTemplate("content"))
    elements.append(PageBreak())
    return elements


# ---------------------------------------------------------------------------
# Executive Summary
# ---------------------------------------------------------------------------

def _build_executive_summary(analysis: dict, styles: dict) -> list:
    """Build executive summary page with key statistics."""
    elements = []

    tier1 = analysis.get("tier1", {})
    tier2 = analysis.get("tier2", {})
    patterns = tier2.get("patterns", [])
    staging = tier2.get("staging", {})

    # Counts
    total_tests = len(tier1)
    abnormal_count = sum(
        1 for v in tier1.values()
        if v.get("status") in ("low", "high", "critical_low", "critical_high")
    )
    critical_count = sum(
        1 for v in tier1.values()
        if v.get("status") in ("critical_low", "critical_high")
    )
    normal_count = total_tests - abnormal_count
    pattern_count = len(patterns)

    elements.append(Paragraph("Executive Summary", styles["section_heading"]))
    elements.append(_section_divider())

    # --- Stat cards row ---
    stat_cards = []
    stat_data = [
        (str(total_tests), "Total Tests"),
        (str(normal_count), "Normal"),
        (str(abnormal_count), "Abnormal"),
        (str(critical_count), "Critical"),
        (str(pattern_count), "Patterns Found"),
    ]

    for value, label in stat_data:
        card_content = [
            [Paragraph(value, styles["stat_value"])],
            [Paragraph(label, styles["stat_label"])],
        ]
        card = Table(card_content, colWidths=[28 * mm])
        card.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (0, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (0, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (0, -1), 2 * mm),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(COLOR_BG_LIGHT)),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#e5e7eb")),
        ]))
        stat_cards.append(card)

    stat_row = Table([stat_cards], colWidths=[30 * mm] * 5)
    stat_row.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(stat_row)
    elements.append(Spacer(1, 6 * mm))

    # --- Highest severity pattern ---
    if patterns:
        sorted_patterns = sorted(
            patterns,
            key=lambda p: SEVERITY_ORDER.get(p.get("severity", "low"), 0),
            reverse=True,
        )
        top = sorted_patterns[0]
        sev = top.get("severity", "low")
        sev_hex = SEVERITY_HEX.get(sev, "#6b7280")

        elements.append(Paragraph("Highest Severity Finding", styles["sub_heading"]))

        alert_data = [[
            _severity_badge(sev),
            Paragraph(
                f"<b>{top.get('name', 'Unknown')}</b> — {top.get('interpretation', '')[:200]}",
                styles["body"],
            ),
        ]]
        alert_tbl = Table(alert_data, colWidths=[65, None])
        alert_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(ROW_COLOR_RED if sev == "critical" else ROW_COLOR_AMBER)),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
        ]))
        elements.append(alert_tbl)
        elements.append(Spacer(1, 4 * mm))

    # --- Staging results ---
    if staging:
        elements.append(Paragraph("Key Staging Results", styles["sub_heading"]))
        staging_rows = []
        for stage_key, stage_data in staging.items():
            label = stage_key.upper().replace("_", " ")
            stage_str = stage_data.get("stage", "")
            stage_label = stage_data.get("label", "")
            description = stage_data.get("description", "")
            stage_color = stage_data.get("color", "green")

            color_map = {
                "green": "#16a34a",
                "yellow": "#ca8a04",
                "amber": "#ea580c",
                "orange": "#ea580c",
                "red": "#dc2626",
                "darkred": "#991b1b",
            }
            dot_color = color_map.get(stage_color, "#6b7280")

            staging_rows.append([
                Paragraph(f"<b>{label}</b>", styles["body_bold"]),
                Paragraph(
                    f'<font color="{dot_color}"><b>{stage_str}</b></font> — {stage_label}',
                    styles["body"],
                ),
                Paragraph(description, styles["body_small"]),
            ])

        if staging_rows:
            st = Table(staging_rows, colWidths=[35 * mm, 55 * mm, None])
            st.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#e5e7eb")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COLOR_BG_LIGHT)),
                ("ROUNDEDCORNERS", [4, 4, 4, 4]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
            ]))
            elements.append(st)

    elements.append(PageBreak())
    return elements


# ---------------------------------------------------------------------------
# Detailed Lab Results by Panel
# ---------------------------------------------------------------------------

def _build_lab_results(analysis: dict, styles: dict) -> list:
    """Build detailed lab results pages grouped by clinical panel."""
    elements = []
    tier1 = analysis.get("tier1", {})

    if not tier1:
        return elements

    elements.append(Paragraph("Detailed Lab Results", styles["section_heading"]))
    elements.append(_section_divider())

    # Build a set of all test IDs already placed into a panel (to catch stragglers)
    placed_tests = set()
    for _panel_name, test_ids in PANEL_ORDER:
        placed_tests.update(test_ids)

    for panel_name, test_ids in PANEL_ORDER:
        # Filter to tests that actually exist in this analysis
        panel_tests = [tid for tid in test_ids if tid in tier1]
        if not panel_tests:
            continue

        panel_elements = []
        panel_elements.append(Paragraph(panel_name, styles["panel_heading"]))

        # Build table
        header_row = [
            Paragraph("Test Name", styles["table_header"]),
            Paragraph("Value", styles["table_header"]),
            Paragraph("Unit", styles["table_header"]),
            Paragraph("Status", styles["table_header"]),
            Paragraph("Reference Range", styles["table_header"]),
        ]
        table_data = [header_row]
        row_colors = []

        for tid in panel_tests:
            interp = tier1[tid]
            status = interp.get("status", "unknown")
            ref = interp.get("reference_range", {}) or {}
            ref_low = ref.get("low")
            ref_high = ref.get("high")
            ref_normal = ref.get("normal")

            if ref_normal:
                ref_str = f"Normal: {ref_normal}"
            elif ref_low is not None and ref_high is not None:
                ref_str = f"{ref_low} - {ref_high}"
            elif ref_low is not None:
                ref_str = f"> {ref_low}"
            elif ref_high is not None:
                ref_str = f"< {ref_high}"
            else:
                ref_str = "N/A"

            display_name = tid.replace("_", " ").title()
            value_str = str(interp.get("value", ""))
            unit_str = interp.get("unit", "")
            status_display = status.replace("_", " ").title()

            # Color the status text
            status_colors = {
                "normal": "#16a34a",
                "low": "#ea580c",
                "high": "#ea580c",
                "critical_low": "#dc2626",
                "critical_high": "#dc2626",
                "unknown": "#6b7280",
            }
            status_hex = status_colors.get(status, "#6b7280")

            row = [
                Paragraph(display_name, styles["table_cell_bold"]),
                Paragraph(value_str, styles["table_cell"]),
                Paragraph(unit_str, styles["table_cell"]),
                Paragraph(
                    f'<font color="{status_hex}"><b>{status_display}</b></font>',
                    styles["table_cell"],
                ),
                Paragraph(ref_str, styles["table_cell"]),
            ]
            table_data.append(row)
            row_colors.append(_row_color_for_status(status))

        col_widths = [42 * mm, 22 * mm, 22 * mm, 28 * mm, 38 * mm]
        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Base style
        tbl_style_cmds = [
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_DARK_HEADER)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(COLOR_WHITE)),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, 0), 0.5, colors.HexColor(COLOR_DARK_HEADER)),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
        ]

        # Row-level background colouring
        for idx, bg_hex in enumerate(row_colors):
            row_num = idx + 1  # offset for header
            tbl_style_cmds.append(
                ("BACKGROUND", (0, row_num), (-1, row_num), colors.HexColor(bg_hex))
            )

        tbl.setStyle(TableStyle(tbl_style_cmds))
        panel_elements.append(tbl)
        panel_elements.append(Spacer(1, 2 * mm))

        elements.append(KeepTogether(panel_elements))

    # Catch any tests not in predefined panels
    extra_tests = [tid for tid in tier1 if tid not in placed_tests]
    if extra_tests:
        panel_elements = []
        panel_elements.append(Paragraph("Other Tests", styles["panel_heading"]))
        header_row = [
            Paragraph("Test Name", styles["table_header"]),
            Paragraph("Value", styles["table_header"]),
            Paragraph("Unit", styles["table_header"]),
            Paragraph("Status", styles["table_header"]),
            Paragraph("Reference Range", styles["table_header"]),
        ]
        table_data = [header_row]
        row_colors = []

        for tid in extra_tests:
            interp = tier1[tid]
            status = interp.get("status", "unknown")
            ref = interp.get("reference_range", {}) or {}
            ref_low = ref.get("low")
            ref_high = ref.get("high")
            ref_normal = ref.get("normal")

            if ref_normal:
                ref_str = f"Normal: {ref_normal}"
            elif ref_low is not None and ref_high is not None:
                ref_str = f"{ref_low} - {ref_high}"
            else:
                ref_str = "N/A"

            display_name = tid.replace("_", " ").title()
            value_str = str(interp.get("value", ""))
            unit_str = interp.get("unit", "")
            status_display = status.replace("_", " ").title()

            status_colors = {
                "normal": "#16a34a", "low": "#ea580c", "high": "#ea580c",
                "critical_low": "#dc2626", "critical_high": "#dc2626",
                "unknown": "#6b7280",
            }
            status_hex = status_colors.get(status, "#6b7280")

            row = [
                Paragraph(display_name, styles["table_cell_bold"]),
                Paragraph(value_str, styles["table_cell"]),
                Paragraph(unit_str, styles["table_cell"]),
                Paragraph(
                    f'<font color="{status_hex}"><b>{status_display}</b></font>',
                    styles["table_cell"],
                ),
                Paragraph(ref_str, styles["table_cell"]),
            ]
            table_data.append(row)
            row_colors.append(_row_color_for_status(status))

        col_widths = [42 * mm, 22 * mm, 22 * mm, 28 * mm, 38 * mm]
        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl_style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_DARK_HEADER)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(COLOR_WHITE)),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, 0), 0.5, colors.HexColor(COLOR_DARK_HEADER)),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
        ]
        for idx, bg_hex in enumerate(row_colors):
            row_num = idx + 1
            tbl_style_cmds.append(
                ("BACKGROUND", (0, row_num), (-1, row_num), colors.HexColor(bg_hex))
            )
        tbl.setStyle(TableStyle(tbl_style_cmds))
        panel_elements.append(tbl)
        panel_elements.append(Spacer(1, 2 * mm))
        elements.append(KeepTogether(panel_elements))

    elements.append(PageBreak())
    return elements


# ---------------------------------------------------------------------------
# Clinical Pattern Analysis
# ---------------------------------------------------------------------------

def _build_pattern_analysis(analysis: dict, styles: dict) -> list:
    """Build clinical pattern analysis section, sorted by severity."""
    elements = []
    tier2 = analysis.get("tier2", {})
    patterns = tier2.get("patterns", [])

    if not patterns:
        return elements

    elements.append(Paragraph("Clinical Pattern Analysis", styles["section_heading"]))
    elements.append(_section_divider())

    # Sort by severity: critical first
    sorted_patterns = sorted(
        patterns,
        key=lambda p: SEVERITY_ORDER.get(p.get("severity", "low"), 0),
        reverse=True,
    )

    for p in sorted_patterns:
        sev = p.get("severity", "low")
        name = p.get("name", "Unknown Pattern")
        category = p.get("category", "")
        interpretation = p.get("interpretation", "")
        harrison_ref = p.get("harrison_ref", "")
        confidence = p.get("confidence", 0)
        matched = p.get("matched_criteria", "")

        sev_hex = SEVERITY_HEX.get(sev, "#6b7280")
        bg_hex = {
            "critical": "#fef2f2",
            "high": "#fff7ed",
            "moderate": "#fffbeb",
            "low": "#f0fdf4",
        }.get(sev, "#f9fafb")

        # Build the pattern card as a table
        card_rows = []

        # Row 1: Badge + Name + Category
        name_para = Paragraph(
            f'<b>{name}</b>'
            + (f'&nbsp;&nbsp;<font color="#6b7280" size="8">[{category}]</font>' if category else ""),
            styles["body"],
        )
        card_rows.append([_severity_badge(sev), name_para])

        # Row 2: Interpretation
        interp_para = Paragraph(interpretation, styles["body"])
        card_rows.append(["", interp_para])

        # Row 3: Harrison ref (if any)
        if harrison_ref:
            ref_para = Paragraph(
                f'<i><font color="#6366f1">Harrison\'s: {harrison_ref}</font></i>',
                styles["body_italic"],
            )
            card_rows.append(["", ref_para])

        # Row 4: Confidence + criteria
        meta_text = f"Confidence: {confidence:.0%}" if isinstance(confidence, float) else f"Confidence: {confidence}"
        if matched:
            meta_text += f"&nbsp;&nbsp;|&nbsp;&nbsp;Criteria matched: {matched}"
        meta_para = Paragraph(
            f'<font color="#6b7280" size="7">{meta_text}</font>',
            styles["body_small"],
        )
        card_rows.append(["", meta_para])

        card_tbl = Table(card_rows, colWidths=[65, None])
        card_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(sev_hex)),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("TOPPADDING", (0, 0), (0, 0), 3 * mm),
            ("TOPPADDING", (0, 1), (-1, -1), 1 * mm),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -2), 0.5 * mm),
            # Span badge cell only in first row
            ("SPAN", (0, 1), (0, -1)),
        ]))
        elements.append(KeepTogether([card_tbl, Spacer(1, 3 * mm)]))

    elements.append(PageBreak())
    return elements


# ---------------------------------------------------------------------------
# Action Plan
# ---------------------------------------------------------------------------

def _build_action_plan(analysis: dict, styles: dict) -> list:
    """Build the action plan section: further tests, referrals, lifestyle."""
    elements = []
    tier3 = analysis.get("tier3", {})
    further = tier3.get("further_tests", [])
    referrals = tier3.get("referrals", [])
    lifestyle = tier3.get("lifestyle", {})

    if not (further or referrals or lifestyle):
        return elements

    elements.append(Paragraph("Action Plan", styles["section_heading"]))
    elements.append(_section_divider())

    # --- Further Tests grouped by urgency ---
    if further:
        elements.append(Paragraph("Further Tests Recommended", styles["sub_heading"]))

        # Flatten all tests with their parent pattern info, then group by urgency
        all_tests = []
        for group in further:
            pattern_id = group.get("pattern_id", "")
            for test in group.get("tests", []):
                urgency = test.get("urgency", test.get("priority", "routine"))
                all_tests.append({
                    "test_name": test.get("test_name", ""),
                    "rationale": test.get("rationale", ""),
                    "urgency": urgency,
                    "pattern_id": pattern_id,
                })

        # Group by urgency
        urgency_order = ["urgent", "soon", "routine"]
        tests_by_urgency = {}
        for t in all_tests:
            u = t["urgency"]
            if u not in tests_by_urgency:
                tests_by_urgency[u] = []
            tests_by_urgency[u].append(t)

        for urg in urgency_order:
            group_tests = tests_by_urgency.get(urg, [])
            if not group_tests:
                continue

            header_data = [[
                _urgency_badge(urg),
                Paragraph(f"<b>{urg.title()} Priority</b>", styles["body_bold"]),
            ]]
            header_tbl = Table(header_data, colWidths=[58, None])
            header_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(header_tbl)
            elements.append(Spacer(1, 1 * mm))

            for t in group_tests:
                elements.append(Paragraph(
                    f'&bull;&nbsp;&nbsp;<b>{t["test_name"]}</b>: {t["rationale"]}',
                    styles["body"],
                ))
            elements.append(Spacer(1, 3 * mm))

        # Also add any tests with urgency not in the standard list
        for urg, group_tests in tests_by_urgency.items():
            if urg not in urgency_order and group_tests:
                elements.append(Paragraph(
                    f"<b>{urg.title()} Priority</b>",
                    styles["body_bold"],
                ))
                for t in group_tests:
                    elements.append(Paragraph(
                        f'&bull;&nbsp;&nbsp;<b>{t["test_name"]}</b>: {t["rationale"]}',
                        styles["body"],
                    ))
                elements.append(Spacer(1, 3 * mm))

    # --- Specialist Referrals ---
    if referrals:
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph("Specialist Referrals", styles["sub_heading"]))

        ref_header = [
            Paragraph("Specialist", styles["table_header"]),
            Paragraph("Urgency", styles["table_header"]),
            Paragraph("Reason", styles["table_header"]),
        ]
        ref_data = [ref_header]

        for ref in referrals:
            specialist = ref.get("specialist", "")
            urgency = ref.get("urgency", "routine")
            reason = ref.get("reason", "")

            ref_data.append([
                Paragraph(f"<b>{specialist}</b>", styles["table_cell_bold"]),
                _urgency_badge(urgency),
                Paragraph(reason, styles["table_cell"]),
            ])

        ref_tbl = Table(ref_data, colWidths=[40 * mm, 25 * mm, None])
        ref_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_DARK_HEADER)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(COLOR_WHITE)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, 0), 0.5, colors.HexColor(COLOR_DARK_HEADER)),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.HexColor(COLOR_WHITE), colors.HexColor(COLOR_BG_LIGHT),
            ]),
        ]))
        elements.append(ref_tbl)
        elements.append(Spacer(1, 4 * mm))

    # --- Lifestyle Recommendations ---
    if lifestyle:
        has_content = any(
            lifestyle.get(cat)
            for cat in ("diet", "exercise", "sleep", "stress", "weight", "smoking")
        )
        if has_content:
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph("Lifestyle Recommendations", styles["sub_heading"]))

            category_icons = {
                "diet": "Diet",
                "exercise": "Exercise",
                "sleep": "Sleep",
                "stress": "Stress Management",
                "weight": "Weight Management",
                "smoking": "Smoking",
            }

            for cat_key in ("diet", "exercise", "sleep", "stress", "weight", "smoking"):
                items = lifestyle.get(cat_key)
                if not items:
                    continue

                cat_label = category_icons.get(cat_key, cat_key.title())

                # Category header with accent background
                cat_header = Table(
                    [[Paragraph(f"<b>{cat_label}</b>", ParagraphStyle(
                        f"cat_{cat_key}", fontSize=9, leading=12,
                        textColor=colors.HexColor(COLOR_WHITE),
                        fontName="Helvetica-Bold",
                    ))]],
                    colWidths=[None],
                )
                cat_header.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(COLOR_ACCENT)),
                    ("ROUNDEDCORNERS", [3, 3, 0, 0]),
                    ("LEFTPADDING", (0, 0), (0, 0), 3 * mm),
                    ("TOPPADDING", (0, 0), (0, 0), 1.5 * mm),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 1.5 * mm),
                ]))
                elements.append(cat_header)

                # Items
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            # Exercise-style dict with type, duration, frequency
                            parts = []
                            if item.get("type"):
                                parts.append(f"<b>{item['type']}</b>")
                            if item.get("duration"):
                                parts.append(item["duration"])
                            if item.get("frequency"):
                                parts.append(item["frequency"])
                            text = " — ".join(parts) if parts else str(item)
                        else:
                            text = str(item)
                        elements.append(Paragraph(
                            f"&nbsp;&nbsp;&bull;&nbsp;&nbsp;{text}",
                            styles["body"],
                        ))
                elif isinstance(items, str):
                    elements.append(Paragraph(
                        f"&nbsp;&nbsp;&bull;&nbsp;&nbsp;{items}",
                        styles["body"],
                    ))

                elements.append(Spacer(1, 2 * mm))

    elements.append(PageBreak())
    return elements


# ---------------------------------------------------------------------------
# RAG Narrative
# ---------------------------------------------------------------------------

def _build_rag_narrative(analysis: dict, styles: dict) -> list:
    """Build the RAG narrative section if present."""
    elements = []
    rag = analysis.get("rag_narrative")
    if not rag:
        return elements

    elements.append(Paragraph("AI-Generated Clinical Narrative", styles["section_heading"]))
    elements.append(_section_divider())

    # Narrative text
    narrative = rag.get("narrative", "")
    if narrative:
        elements.append(Paragraph("Narrative", styles["sub_heading"]))
        # Split long narratives into paragraphs
        for para_text in narrative.split("\n"):
            para_text = para_text.strip()
            if para_text:
                elements.append(Paragraph(para_text, styles["narrative"]))
        elements.append(Spacer(1, 3 * mm))

    # Differentials
    differentials = rag.get("differentials", [])
    if differentials:
        elements.append(Paragraph("Differential Considerations", styles["sub_heading"]))
        for idx, diff in enumerate(differentials, 1):
            elements.append(Paragraph(
                f"<b>{idx}.</b>&nbsp;&nbsp;{diff}",
                styles["body"],
            ))
        elements.append(Spacer(1, 3 * mm))

    # Harrison's Citations
    citations = rag.get("harrison_citations", [])
    if citations:
        elements.append(Paragraph("Harrison's References", styles["sub_heading"]))
        for cite in citations:
            elements.append(Paragraph(
                f'&bull;&nbsp;&nbsp;<i><font color="{COLOR_ACCENT}">{cite}</font></i>',
                styles["body_italic"],
            ))
        elements.append(Spacer(1, 3 * mm))

    # Confidence
    confidence = rag.get("confidence")
    if confidence is not None:
        conf_pct = f"{confidence:.0%}" if isinstance(confidence, float) else str(confidence)
        elements.append(Paragraph(
            f'<font color="#6b7280">AI Confidence: <b>{conf_pct}</b></font>',
            styles["body_small"],
        ))
        elements.append(Spacer(1, 2 * mm))

    # Caveats
    caveats = rag.get("caveats", [])
    if caveats:
        elements.append(Paragraph("Important Caveats", styles["sub_heading"]))
        for caveat in caveats:
            elements.append(Paragraph(
                f'&bull;&nbsp;&nbsp;<font color="#dc2626">{caveat}</font>',
                styles["body"],
            ))
        elements.append(Spacer(1, 3 * mm))

    # Final disclaimer for RAG section
    elements.append(Spacer(1, 4 * mm))
    rag_disclaimer = Table(
        [[Paragraph(
            "<b>Note:</b> This narrative is generated by an AI model and must be reviewed "
            "by a qualified healthcare professional before any clinical decision is made.",
            ParagraphStyle("RagDisclaimer", fontSize=8, leading=11,
                           textColor=colors.HexColor("#92400e"),
                           alignment=TA_LEFT),
        )]],
        colWidths=[None],
    )
    rag_disclaimer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#fef3c7")),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ("LEFTPADDING", (0, 0), (0, 0), 4 * mm),
        ("RIGHTPADDING", (0, 0), (0, 0), 4 * mm),
        ("TOPPADDING", (0, 0), (0, 0), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (0, 0), 3 * mm),
        ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#f59e0b")),
    ]))
    elements.append(rag_disclaimer)

    return elements


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_pdf_report(analysis: dict) -> bytes:
    """Generate a professional multi-page PDF report from a full analysis result.

    Parameters
    ----------
    analysis : dict
        The complete analysis dictionary with keys: id, timestamp, patient,
        tier1, tier2, tier3, and optionally rag_narrative.

    Returns
    -------
    bytes
        The PDF file content as bytes.

    Raises
    ------
    RuntimeError
        If reportlab is not installed.
    """
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab is not installed")

    buf = io.BytesIO()
    styles = _build_styles()

    # Margins
    left_margin = 20 * mm
    right_margin = 20 * mm
    top_margin = 18 * mm
    bottom_margin = 22 * mm  # Extra space for footer

    # Frame for content pages
    content_frame = Frame(
        left_margin, bottom_margin,
        PAGE_WIDTH - left_margin - right_margin,
        PAGE_HEIGHT - top_margin - bottom_margin,
        id="content_frame",
    )

    # Frame for cover page (full width, less bottom margin)
    cover_frame = Frame(
        left_margin, 18 * mm,
        PAGE_WIDTH - left_margin - right_margin,
        PAGE_HEIGHT - top_margin - 18 * mm,
        id="cover_frame",
    )

    # Page templates
    cover_template = PageTemplate(
        id="cover",
        frames=[cover_frame],
        onPage=_cover_footer,
    )
    content_template = PageTemplate(
        id="content",
        frames=[content_frame],
        onPage=_footer,
    )

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        leftMargin=left_margin,
        rightMargin=right_margin,
        title="Vitalytics Lab Analysis Report",
        author="Vitalytics Clinical Decision Support",
    )
    doc.addPageTemplates([cover_template, content_template])

    # Build story
    story = []

    # 1. Cover Page
    story.extend(_build_cover_page(analysis, styles))

    # 2. Executive Summary
    story.extend(_build_executive_summary(analysis, styles))

    # 3. Detailed Lab Results by Panel
    story.extend(_build_lab_results(analysis, styles))

    # 4. Clinical Pattern Analysis
    story.extend(_build_pattern_analysis(analysis, styles))

    # 5. Action Plan
    story.extend(_build_action_plan(analysis, styles))

    # 6. RAG Narrative (if present)
    story.extend(_build_rag_narrative(analysis, styles))

    # 7. Final disclaimer page element (always last)
    story.append(Spacer(1, 10 * mm))
    story.append(_section_divider())
    final_disclaimer = Table(
        [[Paragraph(
            "<b>Disclaimer:</b> This report is generated by an automated clinical decision "
            "support tool (Vitalytics). It does <b>NOT</b> constitute a medical diagnosis. "
            "Always consult a qualified healthcare provider for medical advice, diagnosis, "
            "and treatment. The information in this report is intended to support, not replace, "
            "the clinician-patient relationship.",
            ParagraphStyle("FinalDisclaimer", fontSize=8, leading=12,
                           textColor=colors.HexColor("#dc2626"),
                           alignment=TA_LEFT),
        )]],
        colWidths=[None],
    )
    final_disclaimer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#fef2f2")),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ("LEFTPADDING", (0, 0), (0, 0), 4 * mm),
        ("RIGHTPADDING", (0, 0), (0, 0), 4 * mm),
        ("TOPPADDING", (0, 0), (0, 0), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (0, 0), 3 * mm),
        ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#dc2626")),
    ]))
    story.append(final_disclaimer)

    doc.build(story)
    return buf.getvalue()
