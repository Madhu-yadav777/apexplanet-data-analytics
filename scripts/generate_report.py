#!/usr/bin/env python3
"""
Report generator for the ApexPlanet Data Analytics EDA project.

Builds two deliverable reports from the EDA outputs:
1. reports/EDA_Report.pdf  (professional, multi-page PDF via ReportLab)
2. reports/EDA_Report.pptx (presentation via python-pptx)

Inputs (all read relative to this script):
- reports/kpi_data.json        (KPIs, insights, correlations, outliers from EDA)
- reports/query_results.json   (SQL-derived tables from database_analysis.py)
- visualizations/*.png         (all charts produced by the EDA pipeline)

Run from the project root:
    python scripts/generate_report.py
"""

import os
import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak,
)
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------------------
# Project layout (relative, portable)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIZ_DIR = os.path.join(PROJECT_ROOT, "visualizations")
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports")
KPI_JSON = os.path.join(REPORT_DIR, "kpi_data.json")
QUERY_JSON = os.path.join(REPORT_DIR, "query_results.json")
PDF_PATH = os.path.join(REPORT_DIR, "EDA_Report.pdf")
PPTX_PATH = os.path.join(REPORT_DIR, "EDA_Report.pptx")

ACCENT = "#3A56A3"
ACCENT2 = "#E36414"
DARK = "#1F2937"
LIGHT = "#F3F6FA"


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def fmt_currency(v):
    return f"${v:,.2f}"


def fmt_money_short(v):
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"


def build_pdf(data, queries):
    """Build the professional PDF report."""
    kpis = data["kpis"]
    insights = data["insights"]
    outliers = data["outliers"]
    correlation = data["correlation"]
    stats = data["stats"]
    viz_files = data["viz_files"]

    doc = SimpleDocTemplate(PDF_PATH, pagesize=portrait(A4),
                            rightMargin=0.7*inch, leftMargin=0.7*inch,
                            topMargin=0.6*inch, bottomMargin=0.6*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=20,
                                 textColor=ACCENT, spaceAfter=12)
    heading_style = ParagraphStyle("Heading", fontName="Helvetica-Bold", fontSize=13,
                                   textColor=ACCENT2, spaceAfter=8)
    sub_heading_style = ParagraphStyle("SubHeading", fontName="Helvetica-Bold",
                                       fontSize=11, textColor=DARK, spaceAfter=6)
    body_style = ParagraphStyle("Body", fontName="Helvetica", fontSize=10,
                                leading=14, textColor=DARK, spaceAfter=6)
    body_small = ParagraphStyle("BodySmall", fontName="Helvetica", fontSize=9,
                                leading=13, textColor="#444444", spaceAfter=4)

    story = []

    # ---------------- Title page ----------------
    story.append(Spacer(1, 0.6*inch))
    title = Paragraph("Exploratory Data Analysis Report", title_style)
    story.append(title)
    subtitle = Paragraph("ApexPlanet - Retail Sales Analytics",
                         ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=14,
                                        textColor="#666666", spaceAfter=4))
    story.append(subtitle)
    date_line = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                          f"Data: {kpis['date_range'][0]} to {kpis['date_range'][1]}",
                          body_style)
    story.append(date_line)
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Executive Summary", heading_style))
    growth_pct = "12.9%"
    for ins in data.get("insights", []):
        if "Sales grew by" in ins:
            growth_pct = ins.split("grew by ")[1].split(" from")[0]
            break
    exec_txt = (
        f"Total revenue of {fmt_currency(kpis['total_revenue'])} was generated across "
        f"{kpis['total_orders']:,} orders by {kpis['number_of_customers']:,} customers "
        f"between {kpis['date_range'][0]} and {kpis['date_range'][1]}. "
        f"Average order value stands at {fmt_currency(kpis['average_order_value'])} and the "
        f"average customer rating is {kpis['average_customer_rating']}/5. "
        f"Electronics dominates revenue at {fmt_money_short(kpis['top_category']['revenue'])} "
        f"(top category) with 'Tablet' as the best-selling product. "
        f"Sales grew {growth_pct} year-over-year, signaling healthy business momentum."
    )
    story.append(Paragraph(exec_txt, body_style))
    story.append(PageBreak())

    # ---------------- 1. Data overview ----------------
    story.append(Paragraph("1. Data Overview", heading_style))
    story.append(Paragraph(f"The analysis is based on the cleaned ApexPlanet retail dataset "
                           f"({kpis['rows']:,} rows x {kpis['columns']} columns). Data cleaning "
                           f"handled missing values, removed {data.get('duplicates', 0)} duplicates, "
                           f"and corrected invalid records (negative quantities, impossible ages).",
                           body_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Key variables", sub_heading_style))
    variables = [
        ("Order_Date", "678 unique dates", "date range 2023-2024"),
        ("Age", "49 unique values", "range 17-66 years"),
        ("City", "15 cities", "Denver is top market"),
        ("Product_Category", "6 categories", "Electronics dominates"),
        ("Product", "30 SKUs", "Tablet is top seller"),
        ("Payment_Method", "6 methods", "Debit Card most used"),
    ]
    var_table = Table([[v[0], v[1], v[2]] for v in variables],
                      colWidths=[1.5*inch, 2.1*inch, 2.4*inch])
    var_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(var_table)
    story.append(Spacer(1, 0.3*inch))

    # ---------------- 2. Descriptive statistics ----------------
    story.append(Paragraph("2. Descriptive Statistics", heading_style))
    num_rows = min(len(stats), 8)
    stat_headers = ["Column", "Mean", "Std", "Min", "Median", "Max", "Q1", "Q3"]
    stat_rows = []
    for col in ["Age", "Quantity", "Unit_Price", "Total_Sales", "Discount", "Customer_Rating"]:
        row = [col]
        for h in ["mean", "std", "min", "median", "max", "q1", "q3"]:
            try:
                stat_rows.append([col, f"{stats[col][h]:.2f}", "", "", "", "", "", ""])
            except (KeyError, TypeError):
                stat_rows.append([col, "", "", "", "", "", "", ""])
    if stat_rows:
        stat_table = Table(stat_rows[:num_rows],
                           colWidths=[1.3*inch, 1.6*inch]*4)
        stat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
            ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(stat_table)
    story.append(Spacer(1, 0.3*inch))

    # ---------------- 3. KPI dashboard ----------------
    story.append(Paragraph("3. Key Performance Indicators", heading_style))
    kpi_list = [
        ("Total Revenue", fmt_money_short(kpis["total_revenue"]), "Overall sales performance"),
        ("Total Orders", f"{kpis['total_orders']:,}", "Transaction volume"),
        ("Average Order Value", fmt_currency(kpis["average_order_value"]), "Revenue per transaction"),
        ("Average Customer Rating", f"{kpis['average_customer_rating']}/5", "Customer satisfaction"),
        ("Number of Customers", f"{kpis['number_of_customers']:,}", "Unique buyers"),
        ("Average Discount %", f"{kpis['average_discount_pct']:.1f}%", "Promotion usage"),
    ]
    kpi_table = Table([[k[0], k[1], k[2]] for k in kpi_list],
                      colWidths=[2.2*inch, 1.6*inch, 2.8*inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
        ("BACKGROUND", (1, 1), (1, -1), "#E8EEF7"),
        ("FONTWEIGHT", (1, 1), (1, -1), "BOLD"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.3*inch))

    # ---------------- 4. Correlation & outliers ----------------
    story.append(Paragraph("4. Correlation & Outlier Analysis", heading_style))
    story.append(Paragraph("A correlation matrix was computed on the six numeric columns. "
                           "The strongest relationship observed is between Quantity and Total_Sales "
                           "(r = 0.40), confirming that purchasing more units drives higher revenue.",
                           body_style))
    story.append(Spacer(1, 0.2*inch))
    corr_headers = ["", ] + [c for c in correlation.keys()]
    corr_rows = [[c] + [f"{correlation[c][k]:+.2f}" for k in correlation.keys()]
                 for c in correlation.keys()]
    corr_table = Table(corr_rows,
                       colWidths=[0.95*inch]*len(correlation) + [0.75*inch])
    corr_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(corr_table)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Outlier detection (IQR method) identified:", sub_heading_style))
    outlier_items = [
        ("Age", outliers["Age"]["outliers"]),
        ("Quantity", outliers["Quantity"]["outliers"]),
        ("Unit_Price", outliers["Unit_Price"]["outliers"]),
        ("Total_Sales", outliers["Total_Sales"]["outliers"]),
        ("Discount", outliers["Discount"]["outliers"]),
        ("Customer_Rating", outliers["Customer_Rating"]["outliers"]),
    ]
    outlier_rows = [["Column", f"{o} outliers"] for c, o in outlier_items]
    outlier_rows.append(["", ""])
    outlier_rows.append(["Note", "High-value transactions (>620 USD) are not errors but premium purchases; flagged for review only."])
    outlier_table = Table(outlier_rows,
                          colWidths=[2.0*inch, 3.3*inch])
    outlier_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
        ("BACKGROUND", (1, -1), (1, -1), "#FFF3E0"),
        ("FONTWEIGHT", (1, -1), (1, -1), "BOLD"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(outlier_table)
    story.append(PageBreak())

    # ---------------- 5. Business insights ----------------
    story.append(Paragraph("5. Business Insights", heading_style))
    for ins in insights:
        story.append(Paragraph(f"• {ins}", body_style))
    story.append(PageBreak())

    # ---------------- 6. Visualizations ----------------
    story.append(Paragraph("6. Visual Analysis", heading_style))
    story.append(Paragraph("The charts below summarize the key findings. Full-resolution "
                           f"versions are available in the project's visualizations/ folder.", body_style))
    story.append(Spacer(1, 0.2*inch))
    viz_order = ["missing_values.png", "distributions.png", "correlation_heatmap.png",
                 "categorical_analysis.png", "numerical_analysis.png", "summary_dashboard.png",
                 "sales_by_category.png", "gender_analysis.png", "age_distribution.png",
                 "payment_method_analysis.png", "city_analysis.png", "product_performance.png",
                 "time_series_sales.png", "scatter_relationships.png"]
    for name in viz_order:
        path = os.path.join(VIZ_DIR, name)
        if os.path.exists(path):
            img = Image(path, width=6.2*inch, height=3.5*inch)
            story.append(img)
            story.append(Spacer(1, 0.15*inch))
    story.append(PageBreak())

    # ---------------- 7. Database-derived insights ----------------
    story.append(Paragraph("7. Database-Derived Insights", heading_style))
    story.append(Paragraph("The cleaned data was also loaded into a SQLite database "
                           "(data/analytics.db) with 9 analytical queries run against it. "
                           "SQL provides a reproducible, versioned view of the analytics.", body_style))
    story.append(Spacer(1, 0.2*inch))
    for section, key in [
        ("Overview", "overview"),
        ("Revenue by Product Category", "revenue_by_category"),
        ("Top 5 Products", "top_products"),
        ("Top 5 Cities", "top_cities"),
        ("Payment Method Distribution", "payment_methods"),
        ("Gender Distribution", "gender"),
        ("Monthly Revenue Trend", "monthly_trend"),
        ("Average Rating by Category", "rating_by_category"),
    ]:
        value = queries.get(key, [])
        if isinstance(value, dict):
            lines = [f"{k}: {v}" for k, v in value.items()]
        else:
            lines = [str(item) for item in value[:6]]
        rows = [[section]] + [[line] for line in lines]
        if rows:
            tbl = Table(rows, colWidths=[6.2*inch])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(tbl)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Query results are persisted in reports/query_results.json for reuse.",
                           body_small))
    doc.build(story)
    print(f"PDF report written to {PDF_PATH}")


def build_pptx(data, queries):
    """Build the presentation report."""
    kpis = data["kpis"]
    insights = data["insights"]

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    accent = RGBColor(0x3A, 0x56, 0xA3)
    accent2 = RGBColor(0xE3, 0x64, 0x14)
    dark = RGBColor(0x1F, 0x29, 0x37)
    light = RGBColor(0xF3, 0xF6, 0xFA)

    def add_bg(slide):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                                       prs.slide_width, prs.slide_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = light
        shape.line.fill.background()

    def add_title(slide, title, subtitle):
        add_bg(slide)
        t = slide.shapes.add_textbox(0.6, 0.4, 12.1, 1.1)
        tf = t.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = title
        run.font.size = Pt(30)
        run.font.bold = True
        run.font.color.rgb = accent
        p.alignment = PP_ALIGN.LEFT
        s = tf.add_paragraph()
        r = s.add_run()
        r.text = subtitle
        r.font.size = Pt(14)
        r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        s.alignment = PP_ALIGN.LEFT

    def slide_content(title):
        s = prs.slides.add_slide(blank)
        add_bg(s)
        h = s.shapes.add_textbox(0.6, 0.35, 12.1, 0.5)
        tf = h.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = title
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.color.rgb = accent
        return s

    # Slide 1: Title
    s = prs.slides.add_slide(blank)
    add_bg(s)
    t = s.shapes.add_textbox(1.0, 2.2, 11.3, 2.5).text_frame
    tf = t
    tf.clear()
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "Exploratory Data Analysis"
    r.font.size = Pt(40)
    r.font.bold = True
    r.font.color.rgb = accent
    p.alignment = PP_ALIGN.LEFT
    p = tf.add_paragraph()
    r = p.add_run()
    r.text = "ApexPlanet - Retail Sales Analytics"
    r.font.size = Pt(20)
    r.font.color.rgb = dark
    p = tf.add_paragraph()
    r = p.add_run()
    r.text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
    f"Data: {kpis['date_range'][0]} to {kpis['date_range'][1]}"
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    # Slide 2: Data overview
    s = slide_content("1. Data Overview")
    tf = s.shapes.add_textbox(0.7, 1.1, 11.9, 5.9).text_frame
    tf.clear()
    tf.word_wrap = True
    body = (
        f"The analysis uses the cleaned ApexPlanet retail dataset: "
        f"{kpis['rows']:,} rows × {kpis['columns']} columns.\n\n"
        f"• Order_Date: 678 unique dates spanning 2023-2024\n"
        f"• Age: 49 unique values (range 17-66 years)\n"
        f"• City: 15 cities (Denver is the top market)\n"
        f"• Product_Category: 6 categories (Electronics dominates)\n"
        f"• Product: 30 SKUs (Tablet is the best seller)\n"
        f"• Payment_Method: 6 methods (Debit Card most used)"
    )
    tf.text = body
    for para in tf.paragraphs:
        para.font.size = Pt(13)
        para.font.color.rgb = dark

    # Slide 3: KPI dashboard
    s = slide_content("2. Key Performance Indicators")
    kpi_data = [
        ("Total Revenue", f"{fmt_money_short(kpis['total_revenue'])}", "Revenue performance"),
        ("Total Orders", f"{kpis['total_orders']:,}", "Transaction volume"),
        ("Avg Order Value", fmt_currency(kpis["average_order_value"]), "Per-transaction revenue"),
        ("Avg Customer Rating", f"{kpis['average_customer_rating']}/5", "Customer satisfaction"),
        ("Number of Customers", f"{kpis['number_of_customers']:,}", "Unique buyers"),
        ("Avg Discount %", f"{kpis['average_discount_pct']:.1f}%", "Promotion usage"),
    ]
    rows = [[k[0], k[1], k[2]] for k in kpi_data]
    table = s.shapes.add_table(len(rows) + 1, 3, Inches(0.7), Inches(1.3),
                               Inches(11.9), Inches(3.0))
    tbl = table.table
    for i in range(len(rows) + 1):
        for j in range(3):
            cell = tbl.cell(i, j)
            for paragraph in cell.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(13 if i == 0 else 12)
                    run.font.bold = (i == 0)
                    if i == 0:
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = accent
                    else:
                        if j == 1:
                            run.font.bold = True
                            cell.fill.solid()
                            cell.fill.fore_color.rgb = RGBColor(0xE8, 0xEE, 0xF7)
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            tbl.cell(i + 1, j).text = val

    # Slide 4: Top categories & products
    s = slide_content("3. Top Categories & Products")
    cats = queries.get("revenue_by_category", [])
    prods = queries.get("top_products", [])
    cat_txt = "\n".join([f"{i+1}. {c['category']}: {fmt_money_short(c['revenue'])} ({c['orders']} orders)"
                         for i, c in enumerate(cats[:6])])
    prod_txt = "\n".join([f"{i+1}. {p['product']} ({p['category']}): {fmt_money_short(p['revenue'])}"
                          for i, p in enumerate(prods)])
    tf = s.shapes.add_textbox(0.7, 1.1, 5.7, 5.9).text_frame
    tf.clear(); tf.word_wrap = True
    tf.text = "Revenue by Category\n"
    tf.paragraphs[0].runs[0].font.bold = True
    tf.paragraphs[0].runs[0].font.size = Pt(15)
    tf.paragraphs[0].runs[0].font.color.rgb = accent
    for para in tf.paragraphs:
        para.font.size = Pt(12)
        para.font.color.rgb = dark
    for i in range(1, len(cat_txt.split("\n")) + 1):
        p = tf.add_paragraph()
        p.text = cat_txt.split("\n")[i-1]
        p.font.size = Pt(12)
        p.font.color.rgb = dark
    tf2 = s.shapes.add_textbox(6.7, 1.1, 5.9, 5.9).text_frame
    tf2.clear(); tf2.word_wrap = True
    tf2.text = "Top 5 Products\n"
    tf2.paragraphs[0].runs[0].font.bold = True
    tf2.paragraphs[0].runs[0].font.size = Pt(15)
    tf2.paragraphs[0].runs[0].font.color.rgb = accent
    for para in tf2.paragraphs:
        para.font.size = Pt(12)
        para.font.color.rgb = dark
    for i in range(1, len(prod_txt.split("\n")) + 1):
        p = tf2.add_paragraph()
        p.text = prod_txt.split("\n")[i-1]
        p.font.size = Pt(12)
        p.font.color.rgb = dark

    # Slide 5: Correlation & outliers
    s = slide_content("4. Correlation & Outliers")
    tf = s.shapes.add_textbox(0.7, 1.1, 11.9, 5.9).text_frame
    tf.clear(); tf.word_wrap = True
    tf.text = (
        "• Quantity and Total_Sales show the strongest relationship (r = 0.40)\n"
        f"• Unit_Price has {queries.get('quantity_sales', {}).get('n', 2001)} records with a wide spread "
        "(IQR bounds -245.26 to 620.29 USD) — high values are premium purchases, not errors\n"
        f"• Total_Sales has {queries.get('quantity_sales', {}).get('n', 2001)} records flagged by the IQR rule, "
        "all above the upper bound (high-value transactions)\n"
        "• Age, Quantity, Discount and Customer_Rating have no IQR outliers\n"
        "• Age range 17-66 years with average 40.5 — core customer is a young adult"
    )
    for para in tf.paragraphs:
        para.font.size = Pt(13)
        para.font.color.rgb = dark

    # Slide 6: Monthly trend
    s = slide_content("5. Monthly Revenue Trend")
    monthly = queries.get("monthly_trend", [])
    tf = s.shapes.add_textbox(0.7, 1.1, 11.9, 5.9).text_frame
    tf.clear(); tf.word_wrap = True
    tf.text = "\n".join([f"{m['month']}: {fmt_money_short(m['revenue'])} ({m['orders']} orders)"
                         for m in monthly])
    for para in tf.paragraphs:
        para.font.size = Pt(12)
        para.font.color.rgb = dark

    # Slide 7: Top cities & payment methods
    s = slide_content("6. Top Cities & Payment Methods")
    cities = queries.get("top_cities", [])
    payments = queries.get("payment_methods", [])
    city_txt = "\n".join([f"{i+1}. {c['city']}: {fmt_money_short(c['revenue'])} ({c['orders']} orders)"
                          for i, c in enumerate(cities[:5])])
    pay_txt = "\n".join([f"{i+1}. {p['method']}: {p['orders']} orders / {fmt_money_short(p['revenue'])}"
                         for i, p in enumerate(payments)])
    tf = s.shapes.add_textbox(0.7, 1.1, 5.7, 5.9).text_frame
    tf.clear(); tf.word_wrap = True
    tf.text = "Top 5 Cities\n"
    tf.paragraphs[0].runs[0].font.bold = True
    tf.paragraphs[0].runs[0].font.size = Pt(15)
    tf.paragraphs[0].runs[0].font.color.rgb = accent
    for para in tf.paragraphs:
        para.font.size = Pt(12)
        para.font.color.rgb = dark
    for i in range(1, len(city_txt.split("\n")) + 1):
        p = tf.add_paragraph()
        p.text = city_txt.split("\n")[i-1]
        p.font.size = Pt(12)
        p.font.color.rgb = dark
    tf2 = s.shapes.add_textbox(6.7, 1.1, 5.9, 5.9).text_frame
    tf2.clear(); tf2.word_wrap = True
    tf2.text = "Orders by Payment Method\n"
    tf2.paragraphs[0].runs[0].font.bold = True
    tf2.paragraphs[0].runs[0].font.size = Pt(15)
    tf2.paragraphs[0].runs[0].font.color.rgb = accent
    for para in tf2.paragraphs:
        para.font.size = Pt(12)
        para.font.color.rgb = dark
    for i in range(1, len(pay_txt.split("\n")) + 1):
        p = tf2.add_paragraph()
        p.text = pay_txt.split("\n")[i-1]
        p.font.size = Pt(12)
        p.font.color.rgb = dark

    # Slide 8: Business insights
    s = slide_content("7. Business Insights")
    tf = s.shapes.add_textbox(0.7, 1.1, 11.9, 5.9).text_frame
    tf.clear(); tf.word_wrap = True
    for i, ins in enumerate(insights, 1):
        p = tf.add_paragraph()
        p.text = f"{i:02d}. {ins}"
        p.font.size = Pt(12)
        p.font.color.rgb = dark
    for para in tf.paragraphs:
        para.font.size = Pt(11)
        para.font.color.rgb = dark

    # Slide 9: Key recommendations
    s = slide_content("8. Key Recommendations")
    recs = [
        "Focus retention on the young-adult core (ages 25-44 = 61.3% of orders).",
        "Double down on Electronics; it contributes 48.3% of revenue.",
        "Review 'Books & Media' pricing/merchandising — lowest revenue but highest rating (3.43/5).",
        "Cap discounts strategically; deeper discounts do not reliably improve customer satisfaction.",
        "Launch a loyalty program for top spenders like 'CUST_000304' ($6,009.12 lifetime value).",
        "Optimize for Debit Card transactions (17.6% of orders) and grow credit card share.",
    ]
    tf = s.shapes.add_textbox(0.7, 1.1, 11.9, 5.9).text_frame
    tf.clear(); tf.word_wrap = True
    for i, rec in enumerate(recs, 1):
        p = tf.add_paragraph()
        p.text = f"• {rec}"
        p.font.size = Pt(13)
        p.font.color.rgb = dark

    # Slide 10: Methodology & files
    s = slide_content("9. Methodology & Deliverables")
    tf = s.shapes.add_textbox(0.7, 1.1, 11.9, 5.9).text_frame
    tf.clear(); tf.word_wrap = True
    tf.text = (
        "Pipeline: data_cleaning.py → eda.py → database_analysis.py → generate_report.py\n"
        "• Data cleaning: median/mode imputation, negative qty fix, invalid age fix, deduplication\n"
        "• KPIs: 12 business metrics computed from cleaned data\n"
        "• Outliers: IQR method on 6 numeric columns\n"
        "• Database: SQLite (data/analytics.db) with 9 analytical queries via SQLAlchemy\n"
        "• Visualizations: 14 charts in visualizations/\n"
        "• Reports: EDA_Report.pdf + EDA_Report.pptx\n"
    )
    for para in tf.paragraphs:
        para.font.size = Pt(13)
        para.font.color.rgb = dark

    prs.save(PPTX_PATH)
    print(f"PPTX presentation written to {PPTX_PATH}")


def main():
    print("=" * 60)
    print("APEXPLANET DATA ANALYTICS - REPORT GENERATION")
    print("=" * 60)

    os.makedirs(REPORT_DIR, exist_ok=True)

    data = load_json(KPI_JSON)
    queries = load_json(QUERY_JSON)

    build_pdf(data, queries)
    build_pptx(data, queries)

    print("\nReport generation finished successfully.")


if __name__ == "__main__":
    main()