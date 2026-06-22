#!/usr/bin/env python3
"""Convert content.md to an A4 landscape PDF for N3 vocabulary.
Uses dual-font strategy:
  - IPAGothic for Japanese characters (kanji, hiragana, katakana)
  - DejaVu Sans for Vietnamese/Latin characters
This ensures both scripts render correctly.
"""

import sys
import os
import re
import unicodedata

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ---------------------------------------------------------------------------
# Font registration
# ---------------------------------------------------------------------------
FONT_LATIN    = "DejaVuSans"
FONT_LATIN_B  = "DejaVuSans-Bold"
FONT_CJK      = "IPAGothic"

def register_fonts():
    pdfmetrics.registerFont(TTFont(
        FONT_LATIN,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont(
        FONT_LATIN_B,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont(
        FONT_CJK,
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"))


# ---------------------------------------------------------------------------
# Mixed-script text renderer
# ---------------------------------------------------------------------------
def is_cjk(ch):
    """Return True if char is CJK (kanji, hiragana, katakana, etc.)."""
    cp = ord(ch)
    return (
        0x3000 <= cp <= 0x9FFF   # CJK Unified + kana + symbols
        or 0xF900 <= cp <= 0xFAFF  # CJK Compatibility Ideographs
        or 0xFF00 <= cp <= 0xFFEF  # Halfwidth/Fullwidth Forms
        or 0x20000 <= cp <= 0x2FA1F  # CJK Ext B–F
    )


def _escape(text):
    """Escape XML special chars for ReportLab Paragraph."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_mixed_xml(text, bold=False):
    """Return ReportLab XML markup string with font tags for mixed CJK+Latin text."""
    if not text:
        return ""
    segments = []
    current_cjk = is_cjk(text[0])
    current_seg  = text[0]
    for ch in text[1:]:
        if is_cjk(ch) == current_cjk:
            current_seg += ch
        else:
            segments.append((current_cjk, current_seg))
            current_cjk = is_cjk(ch)
            current_seg  = ch
    segments.append((current_cjk, current_seg))
    parts = []
    for cjk_flag, seg in segments:
        font = FONT_CJK if cjk_flag else (FONT_LATIN_B if bold else FONT_LATIN)
        parts.append(f'<font name="{font}">{_escape(seg)}</font>')
    return "".join(parts)


def mixed_para(text, base_size=12, bold=False):
    """
    Build a ReportLab Paragraph that renders CJK chars with IPAGothic
    and Latin/Vietnamese chars with DejaVu Sans.
    """
    xml = build_mixed_xml(text, bold)
    if not xml:
        xml = ""
    style = ParagraphStyle(
        "mixed",
        fontName=FONT_LATIN,
        fontSize=base_size,
        leading=base_size * 1.4,
        wordWrap="CJK",
        spaceAfter=1,
    )
    return Paragraph(xml, style)


def vocab_reading_para(vocab, reading, vocab_size=12, reading_size=11):
    """
    Two-line cell: vocabulary on line 1, reading (furigana) on line 2.
    Neither line wraps — column must be wide enough.
    """
    line1 = build_mixed_xml(vocab)
    line2 = build_mixed_xml(reading)
    xml   = f'{line1}<br/><font name="{FONT_CJK}" size="{reading_size}">{_escape("")}</font>{line2}'
    # Use explicit size tags for the two lines
    xml = (
        f'<font size="{vocab_size}">{build_mixed_xml(vocab)}</font>'
        f'<br/>'
        f'<font size="{reading_size}" color="#444444">{build_mixed_xml(reading)}</font>'
    )
    style = ParagraphStyle(
        "vr",
        fontName=FONT_CJK,
        fontSize=vocab_size,
        leading=vocab_size * 1.5,
        wordWrap="CJK",
        splitLongWords=False,
    )
    return Paragraph(xml, style)


# ---------------------------------------------------------------------------
# Footer / canvas callback
# ---------------------------------------------------------------------------
LEFT_MARGIN  = 42   # 3 × 14
RIGHT_MARGIN = 14
BOT_MARGIN   = 32   # taller bottom to fit footer text

FOOTER_LINE1_PREFIX = "N\u01a1i mua c\u00e1c t\u00e0i li\u1ec7u kh\u00e1c: "
FOOTER_LINE1_URL    = "https://templatestores.com/"
FOOTER_LINE2_PREFIX = "H\u1ecdc t\u1eadp th\u00f4ng minh v\u1edbi h\u00e0ng ngh\u00ecn b\u1ed9 flashcard: "
FOOTER_LINE2_URL    = "https://ankiva.cc/"


def draw_footer(canvas, doc):
    """Draw page number (right) and two promo lines (left) in the footer area."""
    page_w, page_h = landscape(A4)
    canvas.saveState()

    FOOTER_FONT_SIZE = 8
    LINE1_Y = 27   # top promo line y-position
    LINE2_Y = 15   # bottom promo line y-position
    PAGE_Y  = (LINE1_Y + LINE2_Y) / 2  # vertically center page num

    # --- page number (right-aligned, grey) ---
    canvas.setFont(FONT_LATIN, FOOTER_FONT_SIZE)
    canvas.setFillColor(colors.HexColor("#555555"))
    page_num_text = f"Trang {doc.page}"
    canvas.drawRightString(page_w - RIGHT_MARGIN, PAGE_Y, page_num_text)

    # --- promo line 1: prefix (grey) + URL (red) ---
    canvas.setFont(FONT_LATIN, FOOTER_FONT_SIZE)
    canvas.setFillColor(colors.HexColor("#555555"))
    x = LEFT_MARGIN
    canvas.drawString(x, LINE1_Y, FOOTER_LINE1_PREFIX)
    prefix_w = canvas.stringWidth(FOOTER_LINE1_PREFIX, FONT_LATIN, FOOTER_FONT_SIZE)
    canvas.setFillColor(colors.HexColor("#CC0000"))
    canvas.drawString(x + prefix_w, LINE1_Y, FOOTER_LINE1_URL)

    # --- promo line 2: prefix (grey) + URL (red) ---
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(x, LINE2_Y, FOOTER_LINE2_PREFIX)
    prefix_w2 = canvas.stringWidth(FOOTER_LINE2_PREFIX, FONT_LATIN, FOOTER_FONT_SIZE)
    canvas.setFillColor(colors.HexColor("#CC0000"))
    canvas.drawString(x + prefix_w2, LINE2_Y, FOOTER_LINE2_URL)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Parse content.md
# ---------------------------------------------------------------------------
def parse_md(md_path):
    rows = []
    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("|") and not line.startswith("| STT") and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")][1:-1]
                if len(parts) == 6:
                    stt, vocab, meaning, reading, example, translation = parts
                    if stt != "---":
                        rows.append([stt, vocab, meaning, reading, example, translation])
    return rows


# ---------------------------------------------------------------------------
# Build PDF
# ---------------------------------------------------------------------------
def build_pdf(rows, pdf_path):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
        topMargin=14, bottomMargin=BOT_MARGIN,
    )

    # -----------------------------------------------------------------------
    # Column widths — fixed pt values so STT & vocab columns never wrap
    # Usable width: A4-landscape (841.89pt) - LEFT_MARGIN(42) - RIGHT_MARGIN(14) = ~786pt
    # -----------------------------------------------------------------------
    COL_STT    = 46    # "1393" at 12pt = 30.5pt + 8pt padding + buffer
    COL_VOCAB  = 145   # longest vocab ~7 CJK chars (7×12=84) + reading below; wide margin
    COL_MEAN   = 108   # meaning (Vietnamese)
    remaining  = landscape(A4)[0] - LEFT_MARGIN - RIGHT_MARGIN - COL_STT - COL_VOCAB - COL_MEAN
    COL_EX     = remaining * 0.50  # example sentence
    COL_TRANS  = remaining * 0.50  # translation
    col_widths = [COL_STT, COL_VOCAB, COL_MEAN, COL_EX, COL_TRANS]

    header_style = ParagraphStyle(
        "hdr", fontName=FONT_LATIN_B, fontSize=13, leading=16,
        textColor=colors.white, wordWrap="CJK",
    )

    header_row = [
        Paragraph("STT", header_style),
        Paragraph("Từ vựng (Cách đọc)", header_style),
        Paragraph("Ý nghĩa", header_style),
        Paragraph("Câu ví dụ", header_style),
        Paragraph("Dịch câu ví dụ", header_style),
    ]

    data = [header_row]
    for row in rows:
        stt, vocab, meaning, reading, example, translation = row
        data.append([
            Paragraph(stt, ParagraphStyle("stt", fontName=FONT_LATIN, fontSize=12, leading=15, alignment=1, wordWrap="LTR")),
            vocab_reading_para(vocab, reading),
            mixed_para(meaning, base_size=12),
            mixed_para(example, base_size=12),
            mixed_para(translation, base_size=12),
        ])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("ALIGN",       (0, 0), (0, -1), "CENTER"),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    doc.build([table], onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(f"Created {pdf_path} with {len(rows)} entries")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    md_file  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "content.md")
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "content_N3.pdf")

    register_fonts()
    rows = parse_md(md_file)
    build_pdf(rows, pdf_file)
