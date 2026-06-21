#!/usr/bin/env python3
"""Tạo PDF từ file CSV từ vựng tiếng Nhật bất kỳ.

Input CSV cần có các cột (theo thứ tự hoặc theo tên):
  word, phonetic, word_meaning, example_sentence, ExampleMeaning

Output: PDF A4 landscape cùng thông số với content_N3.pdf
  - STT tự động đánh số
  - Từ vựng dòng 1, cách đọc dòng 2
  - Font dual: IPAGothic (CJK) + DejaVu Sans (Latin/Việt)
  - Footer: số trang + promo lines
"""

import csv
import sys
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
FONT_LATIN   = "DejaVuSans"
FONT_LATIN_B = "DejaVuSans-Bold"
FONT_CJK     = "IPAGothic"

def register_fonts():
    pdfmetrics.registerFont(TTFont(FONT_LATIN,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_LATIN_B,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_CJK,
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"))


# ---------------------------------------------------------------------------
# Mixed-script helpers
# ---------------------------------------------------------------------------
def is_cjk(ch):
    cp = ord(ch)
    return (0x3000 <= cp <= 0x9FFF
            or 0xF900 <= cp <= 0xFAFF
            or 0xFF00 <= cp <= 0xFFEF
            or 0x20000 <= cp <= 0x2FA1F)

def _escape(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

def build_mixed_xml(text, bold=False):
    if not text:
        return ""
    segments, cur_cjk, cur_seg = [], is_cjk(text[0]), text[0]
    for ch in text[1:]:
        if is_cjk(ch) == cur_cjk:
            cur_seg += ch
        else:
            segments.append((cur_cjk, cur_seg))
            cur_cjk, cur_seg = is_cjk(ch), ch
    segments.append((cur_cjk, cur_seg))
    parts = []
    for cjk_flag, seg in segments:
        font = FONT_CJK if cjk_flag else (FONT_LATIN_B if bold else FONT_LATIN)
        parts.append(f'<font name="{font}">{_escape(seg)}</font>')
    return "".join(parts)

def mixed_para(text, size=12):
    xml = build_mixed_xml(text)
    style = ParagraphStyle("m", fontName=FONT_LATIN, fontSize=size,
                           leading=size * 1.4, wordWrap="CJK", spaceAfter=1)
    return Paragraph(xml or "", style)

def vocab_reading_para(vocab, reading, vocab_size=12, reading_size=11):
    xml = (
        f'<font size="{vocab_size}">{build_mixed_xml(vocab)}</font>'
        f'<br/>'
        f'<font size="{reading_size}" color="#444444">{build_mixed_xml(reading)}</font>'
    )
    style = ParagraphStyle("vr", fontName=FONT_CJK, fontSize=vocab_size,
                           leading=vocab_size * 1.5, wordWrap="CJK", splitLongWords=False)
    return Paragraph(xml, style)


# ---------------------------------------------------------------------------
# Footer
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
    FS = 8
    L1_Y, L2_Y = 27, 15
    PAGE_Y = (L1_Y + L2_Y) / 2

    canvas.setFont(FONT_LATIN, FS)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawRightString(page_w - RIGHT_MARGIN, PAGE_Y, f"Trang {doc.page}")

    x = LEFT_MARGIN
    for prefix, url, y in [
        (FOOTER_LINE1_PREFIX, FOOTER_LINE1_URL, L1_Y),
        (FOOTER_LINE2_PREFIX, FOOTER_LINE2_URL, L2_Y),
    ]:
        canvas.setFont(FONT_LATIN, FS)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(x, y, prefix)
        pw = canvas.stringWidth(prefix, FONT_LATIN, FS)
        canvas.setFillColor(colors.HexColor("#CC0000"))
        canvas.drawString(x + pw, y, url)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Read CSV (N5 format)
# ---------------------------------------------------------------------------
def read_csv(csv_path):
    """Return list of dicts with keys: word, phonetic, meaning, example, translation"""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Normalize column names (case-insensitive, strip spaces)
            row = {k.strip().lower(): (v or "").strip() for k, v in r.items()}
            word        = row.get("word", "")
            phonetic    = row.get("phonetic", "")
            meaning     = row.get("word_meaning", "")
            example     = row.get("example_sentence", "")
            translation = row.get("examplemeaning", "")
            if word:
                rows.append((word, phonetic, meaning, example, translation))
    return rows


# ---------------------------------------------------------------------------
# Build PDF
# ---------------------------------------------------------------------------
def build_pdf(rows, pdf_path, title="Từ vựng tiếng Nhật"):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
        topMargin=14, bottomMargin=BOT_MARGIN,
        title=title,
    )

    COL_STT   = 46
    COL_VOCAB = 145
    COL_MEAN  = 108
    remaining = landscape(A4)[0] - LEFT_MARGIN - RIGHT_MARGIN - COL_STT - COL_VOCAB - COL_MEAN
    col_widths = [COL_STT, COL_VOCAB, COL_MEAN, remaining * 0.50, remaining * 0.50]

    hdr_style = ParagraphStyle("hdr", fontName=FONT_LATIN_B, fontSize=13, leading=16,
                                textColor=colors.white, wordWrap="CJK")
    stt_style = ParagraphStyle("stt", fontName=FONT_LATIN, fontSize=12, leading=15,
                                alignment=1, wordWrap="LTR")

    header_row = [
        Paragraph("STT",              hdr_style),
        Paragraph("Từ vựng / Cách đọc", hdr_style),
        Paragraph("Ý nghĩa",          hdr_style),
        Paragraph("Câu ví dụ",        hdr_style),
        Paragraph("Dịch câu ví dụ",   hdr_style),
    ]

    data = [header_row]
    for i, (word, phonetic, meaning, example, translation) in enumerate(rows, start=1):
        data.append([
            Paragraph(str(i), stt_style),
            vocab_reading_para(word, phonetic),
            mixed_para(meaning),
            mixed_para(example),
            mixed_para(translation),
        ])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#2C3E50")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (0, 0), (0,  -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))

    doc.build([table], onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(f"✅ Đã tạo {pdf_path} với {len(rows)} từ vựng")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Dùng: python3 csv_to_pdf.py <input.csv> [output.pdf]")
        sys.exit(1)

    csv_path = sys.argv[1]
    if len(sys.argv) >= 3:
        pdf_path = sys.argv[2]
    else:
        pdf_path = os.path.splitext(csv_path)[0] + ".pdf"

    register_fonts()
    rows = read_csv(csv_path)
    build_pdf(rows, pdf_path, title=os.path.basename(pdf_path))
