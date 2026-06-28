#!/usr/bin/env python3
"""Convert content.md to an A4 landscape PDF for Chinese Flashcard (7 cột).
Uses dual-font strategy:
  - NotoSansSC for Chinese characters (CJK Simplified Chinese)
  - DejaVu Sans for Vietnamese/Latin/Pinyin characters
"""

import sys
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ---------------------------------------------------------------------------
# Font registration
# ---------------------------------------------------------------------------
FONT_LATIN   = "DejaVuSans"
FONT_LATIN_B = "DejaVuSans-Bold"
FONT_CJK     = "NotoSansSC"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def register_fonts():
    pdfmetrics.registerFont(TTFont(
        FONT_LATIN,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont(
        FONT_LATIN_B,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    
    # Check variable font first, fallback to regular if needed
    font_path = os.path.join(BASE_DIR, "fonts", "NotoSansSC-Variable.ttf")
    if not os.path.exists(font_path):
        font_path = os.path.join(BASE_DIR, "fonts", "NotoSansCJKsc-Regular.otf")
    
    pdfmetrics.registerFont(TTFont(FONT_CJK, font_path))


# ---------------------------------------------------------------------------
# Mixed-script text renderer
# ---------------------------------------------------------------------------
def is_cjk(ch):
    cp = ord(ch)
    return (
        0x3000 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0xFF00 <= cp <= 0xFFEF
        or 0x20000 <= cp <= 0x2FA1F
    )


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_mixed_xml(text, bold=False):
    if not text:
        return ""
    segments = []
    current_cjk = is_cjk(text[0])
    current_seg = text[0]
    for ch in text[1:]:
        if is_cjk(ch) == current_cjk:
            current_seg += ch
        else:
            segments.append((current_cjk, current_seg))
            current_cjk = is_cjk(ch)
            current_seg = ch
    segments.append((current_cjk, current_seg))
    parts = []
    for cjk_flag, seg in segments:
        font = FONT_CJK if cjk_flag else (FONT_LATIN_B if bold else FONT_LATIN)
        escaped_seg = _escape(seg).replace("\n", "<br/>")
        parts.append(f'<font name="{font}">{escaped_seg}</font>')
    return "".join(parts)


def mixed_para(text, base_size=9, bold=False):
    xml = build_mixed_xml(text, bold)
    if not xml:
        xml = ""
    style = ParagraphStyle(
        "mixed",
        fontName=FONT_LATIN,
        fontSize=base_size,
        leading=base_size * 1.4,
        wordWrap="CJK",
        spaceAfter=2,
    )
    return Paragraph(xml, style)


# ---------------------------------------------------------------------------
# Footer / canvas callback
# ---------------------------------------------------------------------------
LEFT_MARGIN  = 42
RIGHT_MARGIN = 14
BOT_MARGIN   = 32

FOOTER_LINE1_PREFIX = "Nơi mua các tài liệu khác: "
FOOTER_LINE1_URL    = "https://templatestores.com/"
FOOTER_LINE2_PREFIX = "Học tập thông minh với hàng nghìn bộ flashcard: "
FOOTER_LINE2_URL    = "https://ankiva.cc/"


def draw_footer(canvas, doc):
    page_w, _ = landscape(A4)
    canvas.saveState()

    FOOTER_FONT_SIZE = 8
    LINE1_Y = 27
    LINE2_Y = 15
    PAGE_Y  = (LINE1_Y + LINE2_Y) / 2

    canvas.setFont(FONT_LATIN, FOOTER_FONT_SIZE)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawRightString(page_w - RIGHT_MARGIN, PAGE_Y, f"Trang {doc.page}")

    x = LEFT_MARGIN
    canvas.setFont(FONT_LATIN, FOOTER_FONT_SIZE)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(x, LINE1_Y, FOOTER_LINE1_PREFIX)
    prefix_w = canvas.stringWidth(FOOTER_LINE1_PREFIX, FONT_LATIN, FOOTER_FONT_SIZE)
    canvas.setFillColor(colors.HexColor("#CC0000"))
    canvas.drawString(x + prefix_w, LINE1_Y, FOOTER_LINE1_URL)

    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(x, LINE2_Y, FOOTER_LINE2_PREFIX)
    prefix_w2 = canvas.stringWidth(FOOTER_LINE2_PREFIX, FONT_LATIN, FOOTER_FONT_SIZE)
    canvas.setFillColor(colors.HexColor("#CC0000"))
    canvas.drawString(x + prefix_w2, LINE2_Y, FOOTER_LINE2_URL)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Parse content.md (7 columns: STT | Từ vựng gốc | Từ loại | Phiên âm | Ý nghĩa | Câu ví dụ | Dịch câu ví dụ)
# ---------------------------------------------------------------------------
def parse_md(md_path):
    rows = []
    if not os.path.exists(md_path):
        print(f"Error: {md_path} does not exist.")
        return rows

    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("|") and not (
                line.startswith("| STT") or
                line.startswith("|---|") or
                line.startswith("|-----")
            ):
                parts = [p.strip() for p in line.split("|")][1:-1]
                if len(parts) >= 7:
                    stt = parts[0].strip()
                    vocab = parts[1].replace("<br/>", "\n").replace("｜", "|")
                    pos = parts[2].replace("<br/>", "\n").replace("｜", "|")
                    pinyin = parts[3].replace("<br/>", "\n").replace("｜", "|")
                    meaning = parts[4].replace("<br/>", "\n").replace("｜", "|")
                    example = parts[5].replace("<br/>", "\n").replace("｜", "|")
                    translation = parts[6].replace("<br/>", "\n").replace("｜", "|")
                    rows.append([stt, vocab, pos, pinyin, meaning, example, translation])
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

    usable_width = landscape(A4)[0] - LEFT_MARGIN - RIGHT_MARGIN # ~785.89 pt
    
    # Phân bổ cột
    COL_STT      = 30
    remaining    = usable_width - COL_STT # ~755.89 pt
    COL_VOCAB    = 80
    COL_POS      = 60
    COL_PINYIN   = 90
    COL_MEANING  = 130
    COL_EXAMPLE  = 200
    COL_TRANSL   = remaining - COL_VOCAB - COL_POS - COL_PINYIN - COL_MEANING - COL_EXAMPLE # ~195.89 pt
    
    col_widths = [COL_STT, COL_VOCAB, COL_POS, COL_PINYIN, COL_MEANING, COL_EXAMPLE, COL_TRANSL]

    header_style = ParagraphStyle(
        "hdr", fontName=FONT_LATIN_B, fontSize=9, leading=12,
        textColor=colors.white, wordWrap="CJK",
    )
    stt_style = ParagraphStyle(
        "stt", fontName=FONT_LATIN, fontSize=9, leading=12,
        alignment=1,  # center
    )

    header_row = [
        Paragraph("STT", header_style),
        Paragraph("Từ vựng gốc", header_style),
        Paragraph("Từ loại", header_style),
        Paragraph("Phiên âm", header_style),
        Paragraph("Ý nghĩa", header_style),
        Paragraph("Câu ví dụ", header_style),
        Paragraph("Dịch câu ví dụ", header_style),
    ]

    data = [header_row]
    for row in rows:
        stt, vocab, pos, pinyin, meaning, example, translation = row
        data.append([
            Paragraph(stt, stt_style),
            mixed_para(vocab, base_size=9),
            mixed_para(pos, base_size=9),
            mixed_para(pinyin, base_size=9),
            mixed_para(meaning, base_size=9),
            mixed_para(example, base_size=9),
            mixed_para(translation, base_size=9),
        ])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]))

    doc.build([table], onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(f"Created {pdf_path} with {len(rows)} entries")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    md_file  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "content.md")
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE_DIR, "content_chinese.pdf")

    register_fonts()
    rows = parse_md(md_file)
    build_pdf(rows, pdf_file)
