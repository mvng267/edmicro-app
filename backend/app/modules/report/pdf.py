"""Phiếu báo cáo học tập PDF (thân thiện phụ huynh). Xem SRS REPORT §5.4, US-REPORT-09.
M-live: bản tiếng Việt 1 trang; song ngữ + gửi Zalo tự động để slice sau.
Font DejaVuSans (có sẵn trên Debian) đủ glyph tiếng Việt; thiếu font thì fallback Helvetica.
"""

import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
_FONT = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
if (_FONT_DIR / "DejaVuSans.ttf").exists():
    pdfmetrics.registerFont(TTFont("DejaVu", str(_FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(_FONT_DIR / "DejaVuSans-Bold.ttf")))
    _FONT, _FONT_BOLD = "DejaVu", "DejaVu-Bold"


def build_student_report_pdf(
    *,
    tenant_name: str,
    student_name: str,
    report: dict[str, Any],
    attendance: list[dict[str, Any]] | None = None,
) -> bytes:
    """Dựng PDF từ dữ liệu student_report (summary + items). Trả bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        title=f"Báo cáo học tập — {student_name}",
    )
    h1 = ParagraphStyle("h1", fontName=_FONT_BOLD, fontSize=16, leading=20)
    sub = ParagraphStyle("sub", fontName=_FONT, fontSize=9, textColor=colors.grey)
    body = ParagraphStyle("body", fontName=_FONT, fontSize=10, leading=14)

    s = report["summary"]
    avg = s["avg_score"] if s["avg_score"] is not None else "—"
    made = datetime.now(UTC).strftime("%d/%m/%Y")

    els: list[Any] = [
        Paragraph("BÁO CÁO HỌC TẬP", h1),
        Paragraph(f"{tenant_name} · Ngày lập: {made}", sub),
        Spacer(1, 6 * mm),
        Paragraph(f"Học sinh: <b>{student_name}</b>", body),
        Spacer(1, 3 * mm),
    ]

    # Bảng tóm tắt
    summary_tbl = Table(
        [
            ["Bài được giao", "Đã nộp", "Điểm trung bình"],
            [str(s["assigned"]), str(s["submitted"]), str(avg)],
        ],
        colWidths=[55 * mm, 55 * mm, 55 * mm],
    )
    summary_tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), _FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    els += [summary_tbl, Spacer(1, 6 * mm)]

    # Bảng bài đã nộp
    els.append(Paragraph("<b>Các bài đã nộp</b>", body))
    els.append(Spacer(1, 2 * mm))
    if report["items"]:
        rows = [["Bài", "Điểm", "Đúng", "Ngày nộp"]]
        for it in report["items"]:
            rows.append(
                [
                    Paragraph(it["practice_name"], body),
                    str(it["score"] if it["score"] is not None else "—"),
                    f"{it['correct_count']}/{it['total_count']}",
                    (it["submitted_at"] or "")[:10],
                ]
            )
        t = Table(rows, colWidths=[85 * mm, 25 * mm, 25 * mm, 30 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                    ("FONTNAME", (0, 1), (-1, -1), _FONT),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        els.append(t)
    else:
        els.append(Paragraph("Chưa có bài nào được nộp.", body))

    # Chuyên cần (nếu có dữ liệu)
    if attendance:
        els += [Spacer(1, 6 * mm), Paragraph("<b>Chuyên cần gần đây</b>", body), Spacer(1, 2 * mm)]
        label = {
            "present": "Có mặt",
            "absent": "Vắng",
            "late": "Muộn",
            "excused": "Có phép",
        }
        rows = [["Buổi học", "Ngày", "Trạng thái"]]
        for a in attendance[:10]:
            rows.append(
                [
                    Paragraph(a.get("topic") or "Buổi học", body),
                    (a.get("starts_at") or "")[:10],
                    label.get(a.get("status") or "", a.get("status") or "—"),
                ]
            )
        t = Table(rows, colWidths=[95 * mm, 35 * mm, 35 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                    ("FONTNAME", (0, 1), (-1, -1), _FONT),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        els.append(t)

    els += [
        Spacer(1, 8 * mm),
        Paragraph(
            "Phiếu được tạo tự động từ hệ thống Edmicro. "
            "Quý phụ huynh có thắc mắc vui lòng liên hệ giáo viên chủ nhiệm.",
            sub,
        ),
    ]
    doc.build(els)
    return buf.getvalue()
