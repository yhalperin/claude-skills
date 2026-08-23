"""
L3-Agents Status PPTX Generator
Usage: python generate_pptx.py --data <path-to-data.json>

Input JSON schema:
{
  "rows": [
    {
      "agent":          "Agent Name (KEY)" | "Not mapped yet",
      "theme":          "Theme Summary\n(IAI-XXXX)",
      "business_value": "one-line value",
      "impact":         "one-line impact",
      "status":         "In Progress" | "Planned" | "Open" | ...,
      "pi":             "27-Q1",
      "dev_phase":      1-6
    }
  ],
  "output_dir": "C:\\path\\to\\output"
}

Output: <output_dir>/l3-agents-status-YYYY-MM-DD.pptx
"""

import argparse
import json
import os
import sys
from datetime import date
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Phase definitions ─────────────────────────────────────────────────────────

PHASES = {
    1: "P1 · Discovery & Research",
    2: "P2 · Data Ingestion",
    3: "P3 · MLOps & Algorithm",
    4: "P4 · Embedded in Product",
    5: "P5 · Conversational Layer",
    6: "P6 · Test & Monitoring",
}

PHASE_LEGEND_SHORT = [
    "P1 Discovery & Research",
    "P2 Data Ingestion",
    "P3 MLOps & Algorithm",
    "P4 Embedded in Product",
    "P5 Conversational Layer",
    "P6 Test & Monitoring",
]

HEADERS = [
    "Agent (Master Feature)",
    "Theme Name (Jira ID)",
    "Business Value",
    "Impact",
    "Status",
    "PI",
    "Dev Phase",
]

# Column widths in inches — must sum to ~12.63 (slide width 13.33 − 2×0.35 margins)
COL_W = [1.95, 2.05, 2.60, 2.10, 1.10, 0.53, 2.30]

# ── Color palette ─────────────────────────────────────────────────────────────

WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
SLIDE_BG      = RGBColor(0xFF, 0xFF, 0xFF)
HEADER_BG     = RGBColor(0x1F, 0x6B, 0xC8)
HEADER_TXT    = WHITE
ROW_BG        = WHITE
ROW_ALT_BG    = RGBColor(0xEB, 0xF3, 0xFB)
BORDER_COLOR  = RGBColor(0xC0, 0xCC, 0xD8)
TITLE_COLOR   = RGBColor(0x1A, 0x1A, 0x2E)
SUBTITLE_CLR  = RGBColor(0x55, 0x55, 0x66)
DARK_TEXT     = RGBColor(0x1A, 0x1A, 0x1A)
DIM_TEXT      = RGBColor(0x55, 0x55, 0x66)

# Jira-aligned status colors: In Progress=blue, Planned=green, everything else=gray
STATUS_COLORS = {
    "Done":                 RGBColor(0x42, 0x52, 0x6E),
    "In Progress":          RGBColor(0x00, 0x52, 0xCC),
    "HL Dev Discovery":     RGBColor(0x42, 0x52, 0x6E),
    "HL Product Discovery": RGBColor(0x42, 0x52, 0x6E),
    "Planned":              RGBColor(0x21, 0x6E, 0x4E),
    "Open":                 RGBColor(0x42, 0x52, 0x6E),
}

PHASE_COLORS = {
    1: RGBColor(0x75, 0x75, 0x75),
    2: RGBColor(0x1F, 0x6B, 0xC8),
    3: RGBColor(0x7C, 0x5C, 0xBF),
    4: RGBColor(0x1E, 0x8A, 0x44),
    5: RGBColor(0x0E, 0x7C, 0x86),
    6: RGBColor(0xC0, 0x85, 0x32),
}

LEGEND_DOTS = [
    (RGBColor(0x00, 0x52, 0xCC), "In Progress"),
    (RGBColor(0x21, 0x6E, 0x4E), "Planned"),
    (RGBColor(0x42, 0x52, 0x6E), "Open / Discovery / Other"),
]

# ── XML helpers ───────────────────────────────────────────────────────────────

def set_cell_bg(cell, rgb: RGBColor):
    from pptx.oxml.ns import qn
    from lxml import etree
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for tag in ("a:solidFill", "a:noFill", "a:gradFill", "a:pattFill"):
        for el in tcPr.findall(qn(tag)):
            tcPr.remove(el)
    solidFill = etree.SubElement(tcPr, qn("a:solidFill"))
    srgbClr   = etree.SubElement(solidFill, qn("a:srgbClr"))
    srgbClr.set("val", f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")


def add_cell_border(cell, rgb: RGBColor, width_pt: float = 0.5):
    from pptx.oxml.ns import qn
    from lxml import etree
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    w = int(width_pt * 12700)
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for el in tcPr.findall(qn(tag)):
            tcPr.remove(el)
        ln = etree.SubElement(tcPr, qn(tag))
        ln.set("w", str(w))
        sf = etree.SubElement(ln, qn("a:solidFill"))
        sc = etree.SubElement(sf, qn("a:srgbClr"))
        sc.set("val", f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")


def set_cell_text(cell, text: str, font_size: float, bold: bool,
                  color: RGBColor, align=PP_ALIGN.LEFT):
    tf = cell.text_frame
    tf.word_wrap = True
    tf.clear()
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.size  = Pt(font_size)
        run.font.bold  = bold
        run.font.color.rgb = color


def add_legend_dot(slide, left, top, size, rgb: RGBColor):
    shape = slide.shapes.add_shape(1, left, top, size, size)
    from pptx.oxml.ns import qn
    sp = shape._element
    spPr = sp.find(qn("p:spPr"))
    prstGeom = spPr.find(qn("a:prstGeom"))
    if prstGeom is not None:
        prstGeom.set("prst", "ellipse")
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb
    shape.line.fill.background()

# ── Slide builder ─────────────────────────────────────────────────────────────

def add_slide(prs, chunk, slide_num, total_slides, today_str):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = SLIDE_BG

    SW = prs.slide_width
    SH = prs.slide_height
    M  = Inches(0.38)

    # Title
    tb = slide.shapes.add_textbox(M, M, Inches(8.0), Inches(0.50))
    tf = tb.text_frame
    p  = tf.paragraphs[0]
    run = p.add_run()
    run.text = "L3 Agents Progress"
    run.font.size  = Pt(22)
    run.font.bold  = True
    run.font.color.rgb = TITLE_COLOR

    # Subtitle
    sb = slide.shapes.add_textbox(M, Inches(0.86), Inches(9.0), Inches(0.22))
    tf2 = sb.text_frame
    p2  = tf2.paragraphs[0]
    run2 = p2.add_run()
    run2.text = (
        f"Project IAI · label: L3-Agents · PlannedPI: cf[14422] · Agent: cf[11140] · "
        f"{today_str}  —  Slide {slide_num} of {total_slides}"
    )
    run2.font.size  = Pt(8)
    run2.font.color.rgb = SUBTITLE_CLR

    # Legend (top-right)
    dot_r   = Inches(0.13)
    dot_gap = Inches(0.06)
    lbl_w   = Inches(1.45)
    leg_top = Inches(0.23)
    total_leg_w = len(LEGEND_DOTS) * (dot_r + dot_gap + lbl_w + Inches(0.10))
    leg_x   = SW - M - total_leg_w + Inches(0.1)

    for i, (color, label) in enumerate(LEGEND_DOTS):
        x = leg_x + i * (dot_r + dot_gap + lbl_w + Inches(0.10))
        add_legend_dot(slide, x, leg_top + Inches(0.04), dot_r, color)
        ltb = slide.shapes.add_textbox(x + dot_r + dot_gap, leg_top, lbl_w, Inches(0.22))
        ltf = ltb.text_frame
        lp  = ltf.paragraphs[0]
        lr  = lp.add_run()
        lr.text = label
        lr.font.size  = Pt(8.5)
        lr.font.color.rgb = DARK_TEXT

    # Table
    n_rows     = len(chunk) + 1
    table_top  = Inches(1.12)
    table_h    = SH - table_top - M - Inches(0.30)
    table_w    = SW - 2 * M
    row_h_hdr  = Inches(0.38)
    row_h_data = (table_h - row_h_hdr) / max(len(chunk), 1)

    tbl_shape = slide.shapes.add_table(n_rows, len(HEADERS), M, table_top, table_w, table_h)
    tbl = tbl_shape.table

    total_col_w = sum(COL_W)
    for ci, w in enumerate(COL_W):
        tbl.columns[ci].width = int(table_w * w / total_col_w)

    tbl.rows[0].height = row_h_hdr
    for ri in range(1, n_rows):
        tbl.rows[ri].height = int(row_h_data)

    # Header row
    for ci, hdr in enumerate(HEADERS):
        cell = tbl.cell(0, ci)
        set_cell_bg(cell, HEADER_BG)
        add_cell_border(cell, BORDER_COLOR, 0.5)
        set_cell_text(cell, hdr, 10, True, HEADER_TXT)
        cell.margin_top    = Pt(5)
        cell.margin_bottom = Pt(5)
        cell.margin_left   = Pt(6)
        cell.margin_right  = Pt(4)

    # Data rows
    for ri, row in enumerate(chunk):
        bg   = ROW_ALT_BG if ri % 2 == 1 else ROW_BG
        s_color = STATUS_COLORS.get(row["status"], DIM_TEXT)
        p_color = PHASE_COLORS.get(row["dev_phase"], DIM_TEXT)
        phase_label = PHASES.get(row["dev_phase"], "—")

        values = [row["agent"], row["theme"], row["business_value"],
                  row["impact"], row["status"], row["pi"], phase_label]
        colors = [DIM_TEXT, DARK_TEXT, DARK_TEXT, DIM_TEXT, s_color, DARK_TEXT, p_color]
        bolds  = [False, True, False, False, True, False, False]

        for ci, (val, col, bold) in enumerate(zip(values, colors, bolds)):
            cell = tbl.cell(ri + 1, ci)
            set_cell_bg(cell, bg)
            add_cell_border(cell, BORDER_COLOR, 0.4)
            set_cell_text(cell, val, 9, bold, col)
            cell.margin_top    = Pt(5)
            cell.margin_bottom = Pt(5)
            cell.margin_left   = Pt(6)
            cell.margin_right  = Pt(4)

    # Phase legend strip at bottom
    leg_top = SH - M - Inches(0.22)
    leg_box = slide.shapes.add_textbox(M, leg_top, SW - 2 * M, Inches(0.22))
    ltf = leg_box.text_frame
    lp  = ltf.paragraphs[0]
    lr  = lp.add_run()
    lr.text = "  ·  ".join(PHASE_LEGEND_SHORT)
    lr.font.size      = Pt(7)
    lr.font.color.rgb = RGBColor(0x88, 0x88, 0x99)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate L3-Agents status PPTX")
    parser.add_argument("--data", required=True, help="Path to JSON data file")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows       = data["rows"]
    output_dir = data.get("output_dir", r"C:\Users\yhalperin\Documents\L3_status_presentations")

    os.makedirs(output_dir, exist_ok=True)

    today_str = date.today().strftime("%Y-%m-%d")
    out_file  = os.path.join(output_dir, f"l3-agents-status-{today_str}.pptx")

    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    CHUNK_SIZE = 6
    chunks = [rows[i:i + CHUNK_SIZE] for i in range(0, len(rows), CHUNK_SIZE)]
    if not chunks:
        print("ERROR: No rows provided", file=sys.stderr)
        sys.exit(1)

    for idx, chunk in enumerate(chunks):
        add_slide(prs, chunk, idx + 1, len(chunks), today_str)

    prs.save(out_file)
    print(out_file)
    print(f"Slides: {len(chunks)}  Rows: {len(rows)}", file=sys.stderr)


if __name__ == "__main__":
    main()
