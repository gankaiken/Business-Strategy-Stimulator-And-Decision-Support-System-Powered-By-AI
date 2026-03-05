"""
PDF export for AI-optimized strategy
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
import sys
import subprocess


def export_ai_strategy_to_pdf(
    company,
    best_decisions,
    best_fitness,
    summary_metrics,
    year,
    filename=None,
):
    """
    Export AI strategy to a professional 1–2 page PDF.
    """

    if filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M")

        project_root = os.getcwd()
        report_dir = os.path.join(project_root, "report")
        os.makedirs(report_dir, exist_ok=True)

        filename = os.path.join(
            report_dir,
            f"AI_Strategy_{company.business_id}_{year}_{ts}.pdf",
        )

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=12,
    )

    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=8,
    )

    normal = styles["Normal"]

    elements = []

    elements.append(
        Paragraph(
            "Intelligent Business Advisor – AI Strategy Report",
            title,
        )
    )

    elements.append(
        Paragraph(
            f"<b>Business ID:</b> {company.business_id}<br/>"
            f"<b>Business Type:</b> {company.business_type.title()}<br/>"
            f"<b>Year:</b> {year}<br/>"
            f"<b>Generated:</b> {datetime.now().strftime('%d %B %Y %H:%M')}",
            normal,
        )
    )

    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("Executive Summary", heading))

    summary_text = (
        f"<b>Strategy Type:</b> AI-Optimized<br/>"
        f"<b>Fitness Score:</b> {best_fitness:,.2f}<br/>"
        f"<b>Projected Total Profit:</b> RM{summary_metrics['total_profit']:,.0f}<br/>"
        f"<b>Final Cash Balance:</b> RM{summary_metrics['ending_cash']:,.0f}<br/>"
        f"<b>Minimum Cash Runway:</b> {summary_metrics['min_runway']}<br/>"
        f"<b>Overall Risk Level:</b> {summary_metrics['risk_level']}"
    )

    elements.append(Paragraph(summary_text, normal))
    elements.append(Spacer(1, 0.35 * inch))
    elements.append(Paragraph("Recommended 12-Month AI Strategy", heading))

    table_data = [
        [
            "Month",
            "Price ±%",
            "Marketing (RM)",
            "Staff Adj (RM)",
            "Waste Red %",
            "Inventory Tightness",
        ]
    ]

    for r in best_decisions:
        month = int(r[2])
        price = float(r[3])
        marketing = float(r[4])
        staff = float(r[5])
        waste = float(r[6])
        inventory = float(r[7])

        table_data.append(
            [
                month,
                f"{price * 100:+.1f}%",
                f"{marketing:,.0f}",
                f"{staff:+,.0f}",
                f"{waste * 100:.1f}%",
                f"{inventory:.2f}",
            ]
        )

    table = Table(
        table_data,
        colWidths=[0.9 * inch] * 6,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(
        Paragraph(
            "This report records the final AI-recommended business strategy. "
            "It is intended as a decision support artifact for planning and evaluation. "
            "All simulations and optimization logic were developed in-house.",
            normal,
        )
    )

    print(f" PDF saved to: {filename}")
    doc.build(elements)

    open_pdf_file(filename)

    return filename


def open_pdf_file(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform.startswith("darwin"):
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception as e:
        print("Could not auto-open PDF:", e)
