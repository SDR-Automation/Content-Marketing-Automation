import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

DARK_BG  = HexColor("#0D1117")
ACCENT   = HexColor("#00C2FF")
LIGHT_BG = HexColor("#F4F6FA")
MUTED    = HexColor("#6B7280")
BORDER   = HexColor("#E5E7EB")
TEXT_DARK = HexColor("#111827")
TEXT_BODY = HexColor("#374151")
GREEN_OK = HexColor("#10B981")
RED_NG   = HexColor("#EF4444")

def _make_styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("H1", parent=base["Normal"], fontSize=22, leading=28, textColor=TEXT_DARK, fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=8),
        "h2": ParagraphStyle("H2", parent=base["Normal"], fontSize=15, leading=20, textColor=HexColor("#1D4ED8"), fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6),
        "h3": ParagraphStyle("H3", parent=base["Normal"], fontSize=12, leading=16, textColor=HexColor("#374151"), fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("Body", parent=base["Normal"], fontSize=10, leading=15, textColor=TEXT_BODY, fontName="Helvetica", alignment=TA_JUSTIFY, spaceBefore=4, spaceAfter=4),
        "bullet": ParagraphStyle("Bullet", parent=base["Normal"], fontSize=10, leading=14, textColor=TEXT_BODY, fontName="Helvetica", leftIndent=20, spaceBefore=2, spaceAfter=2),
        "caption": ParagraphStyle("Caption", parent=base["Normal"], fontSize=8, leading=11, textColor=MUTED, fontName="Helvetica-Oblique", alignment=TA_CENTER),
        "meta": ParagraphStyle("Meta", parent=base["Normal"], fontSize=9, leading=12, textColor=MUTED, fontName="Helvetica"),
        "score_label": ParagraphStyle("ScoreLabel", parent=base["Normal"], fontSize=9, leading=12, textColor=TEXT_DARK, fontName="Helvetica-Bold"),
        "score_val": ParagraphStyle("ScoreVal", parent=base["Normal"], fontSize=9, leading=12, textColor=TEXT_BODY, fontName="Helvetica"),
    }

def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = letter
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, h - 36, w, 36, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(ACCENT)
    canvas.drawString(0.5 * inch, h - 23, "CONTENT AGENT  |  Groq Llama 3.3 70B  ->  Claude Sonnet")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(white)
    canvas.drawRightString(w - 0.5 * inch, h - 23, datetime.now().strftime("%B %d, %Y"))
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0.5 * inch, 0.4 * inch, w - 0.5 * inch, 0.4 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.5 * inch, 0.25 * inch, "LLM-1: Groq Llama 3.3 70B  |  LLM-2: Claude Sonnet")
    canvas.drawRightString(w - 0.5 * inch, 0.25 * inch, f"Page {doc.page}")
    canvas.restoreState()

def _safe(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _parse_markdown(content, styles):
    flowables = []
    for line in content.split("\n"):
        if line.startswith("### "):
            flowables.append(Paragraph(_safe(line[4:]), styles["h3"]))
        elif line.startswith("## "):
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=2))
            flowables.append(Paragraph(_safe(line[3:]), styles["h2"]))
        elif line.startswith("# "):
            flowables.append(Paragraph(_safe(line[2:]), styles["h1"]))
        elif line.startswith(("- ", "* ")):
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _safe(line[2:]))
            flowables.append(Paragraph(f"• {text}", styles["bullet"]))
        elif not line.strip():
            flowables.append(Spacer(1, 6))
        else:
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _safe(line))
            flowables.append(Paragraph(text, styles["body"]))
    return flowables

def _cover_block(metadata, styles):
    w = letter[0] - inch
    rows = [
        [Paragraph(metadata["content_type"].upper(), styles["meta"])],
        [Paragraph(_safe(metadata["topic"]), styles["h1"])],
        [Paragraph(f"Audience: {_safe(metadata['audience'])}", styles["meta"])],
        [Paragraph(f"Generated: {metadata['timestamp']}", styles["meta"])],
    ]
    tbl = Table([[r[0]] for r in rows], colWidths=[w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("LINEBELOW", (0, -1), (-1, -1), 2, ACCENT),
    ]))
    return [tbl, Spacer(1, 14)]

def _qa_block(review, styles):
    score    = review.get("score", 0)
    approved = review.get("approved", False)
    feedback = review.get("feedback", "")
    criteria = review.get("criteria_scores", {})
    labels = [
        ("technical_accuracy", "Technical Accuracy"),
        ("relevance", "Relevance & Value"),
        ("seo", "SEO Compliance"),
        ("brand_tone", "Brand & Tone"),
        ("quality", "Quality & Clarity"),
    ]
    rows = [[Paragraph("Criteria", styles["score_label"]), Paragraph("Score", styles["score_label"])]]
    for key, label in labels:
        val = criteria.get(key, "-")
        rows.append([Paragraph(label, styles["score_val"]), Paragraph(str(val), styles["score_val"])])
    rows.append([Paragraph("Total Score", styles["score_label"]), Paragraph(f"{score}/100", styles["score_label"])])
    rows.append([Paragraph("Status", styles["score_label"]), Paragraph("APPROVED" if approved else "REVISED", styles["score_label"])])
    tbl = Table(rows, colWidths=[3.5 * inch, 1 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    flowables = [Paragraph("<b>Quality Assurance Report</b>", styles["h3"]), Spacer(1, 6), tbl]
    if feedback:
        flowables.append(Spacer(1, 8))
        flowables.append(Paragraph(f"<b>Reviewer Notes:</b> {_safe(feedback[:400])}", styles["meta"]))
    flowables.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceBefore=10, spaceAfter=10))
    return flowables

def export_pdf(content, metadata, review, path):
    styles = _make_styles()
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=0.75*inch, rightMargin=0.75*inch, topMargin=0.85*inch, bottomMargin=0.65*inch)
    story = []
    story.extend(_cover_block(metadata, styles))
    story.extend(_qa_block(review, styles))
    story.extend(_parse_markdown(content, styles))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Generated by Content Marketing Agent", styles["caption"]))
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)