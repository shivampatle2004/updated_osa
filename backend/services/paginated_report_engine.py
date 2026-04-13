import io
import datetime
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter, landscape as rl_landscape, portrait as rl_portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def generate_chart_image(data, chart_type='bar', title='', width=6*inch, height=3*inch):
    """
    Generate a chart image (PNG) from data.
    Returns base64 encoded PNG image bytes.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        
        fig, ax = plt.subplots(figsize=(width/inch, height/inch))
        
        if not data or len(data) == 0:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            ax.axis('off')
        else:
            # Extract labels and values
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    keys = list(data[0].keys())
                    labels = [str(row.get(keys[0], ''))[:20] for row in data[:10]]
                    try:
                        values = [float(row.get(keys[1], 0)) for row in data[:10]]
                    except:
                        values = list(range(len(data)))
                else:
                    labels = [str(i) for i in range(len(data))]
                    values = data
            else:
                labels = []
                values = []
            
            # Create chart based on type
            if chart_type == 'bar':
                ax.bar(labels, values, color='#78176b', alpha=0.8)
                ax.set_xlabel(keys[0] if len(keys) > 0 else 'Category')
                ax.set_ylabel(keys[1] if len(keys) > 1 else 'Value')
            elif chart_type == 'line':
                ax.plot(labels, values, marker='o', color='#78176b', linewidth=2)
                ax.set_xlabel(keys[0] if len(keys) > 0 else 'Category')
                ax.set_ylabel(keys[1] if len(keys) > 1 else 'Value')
            elif chart_type == 'pie':
                ax.pie(values, labels=labels, autopct='%1.1f%%', colors=['#78176b', '#9b59b6', '#3498db', '#2ecc71', '#f1c40f'])
            else:
                ax.bar(labels, values, color='#78176b', alpha=0.8)
            
            if title:
                ax.set_title(title, fontsize=12, fontweight='bold')
            
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        return buf.getvalue()
    except Exception as e:
        import traceback
        print(f"Error generating chart: {e}")
        traceback.print_exc()
        return None


class PaginatedReportEngine:
    @staticmethod
    def generate_pdf(report_config, elements, data_provider_fn):
        """
        Generates a COMPLETE Power BI-style paginated report PDF.
        
        Structure:
        1. Header (title + date)
        2. Summary section (KPIs)
        3. Chart section (optional)
        4. Table section (paginated)
        5. Footer (Page X of Y)
        
        report_config: {
            page_size: "A4" or "LETTER",
            orientation: "portrait" or "landscape",
            header_text: "Report Title",
            rows_per_page: 30,
            show_header: true,
            show_footer: true,
            include_summary: true,
            include_chart: false,
            chart_type: "bar"
        }
        
        elements: [{
            type: "table" | "chart" | "text",
            config_json: {...}
        }]
        
        data_provider_fn(data_source_index) -> list of dicts
        """
        buffer = io.BytesIO()
        
        # Page size configuration
        page_size_str = report_config.get("page_size", "A4").upper()
        page_size = letter if page_size_str == "LETTER" else A4
            
        orientation_str = report_config.get("orientation", "portrait").lower()
        if orientation_str == "landscape":
            page_size = rl_landscape(page_size)
        else:
            page_size = rl_portrait(page_size)
            
        # Margins
        left_margin = 0.75 * inch
        right_margin = 0.75 * inch
        top_margin = 0.75 * inch
        bottom_margin = 0.75 * inch
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            rightMargin=right_margin,
            leftMargin=left_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin
        )

        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(name='ReportTitle', parent=styles['Heading1'], 
                                   fontSize=24, textColor=colors.HexColor('#78176b'), 
                                   spaceAfter=10, keepWithNext=True))
        styles.add(ParagraphStyle(name='ReportDate', parent=styles['Normal'], 
                                   fontSize=10, textColor=colors.grey, spaceAfter=20))
        styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], 
                                   fontSize=14, textColor=colors.HexColor('#78176b'), 
                                   spaceAfter=10, spaceBefore=20))
        styles.add(ParagraphStyle(name='KPIValue', parent=styles['Normal'], 
                                   fontSize=20, textColor=colors.HexColor('#78176b'), alignment=1))
        styles.add(ParagraphStyle(name='KPILabel', parent=styles['Normal'], 
                                   fontSize=10, textColor=colors.grey, alignment=1))
        
        # Get config values
        header_text = report_config.get("header_text", "Report")
        default_rows_per_page = report_config.get("rows_per_page", 30)
        show_footer_setting = report_config.get("show_footer", True)
        include_summary = report_config.get("include_summary", True)
        include_chart = report_config.get("include_chart", False)
        chart_type = report_config.get("chart_type", 'bar')
        
        # Calculate page dimensions
        page_width = page_size[0] - left_margin - right_margin
        
        # ===== 1. HEADER SECTION =====
        story.append(Paragraph(header_text, styles['ReportTitle']))
        story.append(Paragraph(datetime.datetime.now().strftime('%B %d, %Y'), styles['ReportDate']))
        story.append(Spacer(1, 0.2 * inch))
        
        # ===== 2. SUMMARY SECTION (KPIs) =====
        if include_summary:
            story.append(Paragraph('Summary', styles['SectionHeader']))
            
            # Get data for summary
            data_source_index = 0
            data_rows = data_provider_fn(data_source_index)
            
            if data_rows and len(data_rows) > 0:
                # Calculate KPIs
                total_rows = len(data_rows)
                
                # Get numeric columns for summary
                numeric_cols = []
                if len(data_rows) > 0:
                    sample = data_rows[0]
                    for key, val in sample.items():
                        try:
                            float(val)
                            numeric_cols.append(key)
                        except:
                            pass
                
                # Create KPI table
                kpi_data = [['Metric', 'Value']]
                
                kpi_data.append(['Total Records', str(total_rows)])
                
                # Calculate average for numeric columns (limit to first 3)
                for col in numeric_cols[:3]:
                    try:
                        values = [float(row.get(col, 0)) for row in data_rows if row.get(col) is not None]
                        if values:
                            avg = sum(values) / len(values)
                            total = sum(values)
                            kpi_data.append([f'{col} - Total', f'{total:,.2f}'])
                            kpi_data.append([f'{col} - Average', f'{avg:,.2f}'])
                    except:
                        pass
                
                # Limit to first 6 rows for KPI summary
                kpi_table = Table(kpi_data[:7], colWidths=[page_width/2, page_width/2])
                kpi_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#78176b')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ])
                kpi_table.setStyle(kpi_style)
                story.append(kpi_table)
            
            story.append(Spacer(1, 0.3 * inch))
        
        # ===== 3. CHART SECTION =====
        if include_chart:
            story.append(Paragraph('Visualization', styles['SectionHeader']))
            
            data_rows = data_provider_fn(0)
            if data_rows and len(data_rows) > 0:
                chart_bytes = generate_chart_image(data_rows[:20], chart_type, header_text)
                if chart_bytes:
                    img = PlatypusImage(io.BytesIO(chart_bytes), width=page_width, height=2.5*inch)
                    story.append(img)
              
            story.append(Spacer(1, 0.3 * inch))
        
        # First, render all charts
        has_charts = False
        for element in elements:
            el_type = element.get("type")
            config = element.get("config_json", {})
            chart_d = config.get("chart_data")
            print(f"PDF Element: type={el_type}, has_chart_data={chart_d is not None}, keys={list(config.keys())}")
            if el_type == "chart":
                has_charts = True
        
        print(f"PDF Has charts: {has_charts}, total elements: {len(elements)}")
        
        if has_charts:
            story.append(Paragraph('Visualizations', styles['SectionHeader']))
            
            for element in elements:
                el_type = element.get("type")
                config = element.get("config_json", {})
                
                if el_type == "chart":
                    chart_data = config.get("chart_data")
                    chart_type = config.get("chart_type", "bar")
                    title = config.get("title", "Chart")
                    
                    print(f"Rendering chart: {title}, type: {chart_type}, data rows: {len(chart_data) if chart_data else 0}")
                    
                    if chart_data and len(chart_data) > 0:
                        chart_bytes = generate_chart_image(chart_data, chart_type, title)
                        if chart_bytes:
                            print(f"Chart image generated: {len(chart_bytes)} bytes")
                            img = PlatypusImage(io.BytesIO(chart_bytes), width=page_width, height=2.5*inch)
                            story.append(img)
                    
                    story.append(Spacer(1, 0.2 * inch))
        
        # Then, render tables
        story.append(PageBreak())
        story.append(Paragraph('Data Tables', styles['SectionHeader']))
        
        for element in elements:
            el_type = element.get("type")
            config = element.get("config_json", {})
            
            if el_type == "text":
                text = config.get("content", "")
                story.append(Paragraph(text, styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))
               
            elif el_type == "table":
                columns = config.get("columns", [])
                rows_per_page = config.get("rows_per_page", default_rows_per_page)
                show_header_el = config.get("show_header", True)

                table_data = config.get("table_data")
                if table_data:
                    data_rows = table_data
                elif not columns:
                    data_rows = data_provider_fn(config.get("data_source_index", 0))

                if not columns and data_rows and len(data_rows) > 0:
                    columns = list(data_rows[0].keys())
                
                if not columns:
                    continue

                if not data_rows:
                    story.append(Paragraph("No data available.", styles['Normal']))
                    continue
                
                # Prepare column names
                col_names = [col.get("name") for col in columns]
                col_headers = [col.get("header", col.get("name")) for col in columns]
                
                # Calculate column widths (equal distribution)
                num_cols = len(col_names)
                if num_cols > 0:
                    col_width = page_width / num_cols
                    col_widths = [col_width] * num_cols
                else:
                    col_widths = None
                
                # Split data into pages
                total_rows = len(data_rows)
                total_pages = (total_rows + rows_per_page - 1) // rows_per_page
                
                for page_num in range(total_pages):
                    start_idx = page_num * rows_per_page
                    end_idx = min(start_idx + rows_per_page, total_rows)
                    page_data = data_rows[start_idx:end_idx]
                    
                    # Build table data
                    table_data = []
                    
                    # Header row
                    if page_num == 0 or show_header_el:
                        table_data.append(col_headers)
                    
                    # Data rows
                    for row_dict in page_data:
                        row_data = [str(row_dict.get(col_name, ""))[:50] for col_name in col_names]
                        table_data.append(row_data)
                    
                    # Create table
                    t = Table(table_data, colWidths=col_widths, repeatRows=1)
                    
                    # Style
                    t_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#78176b')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ])
                    
                    # Alternating row colors
                    header_rows = 1 if (page_num == 0 or show_header_el) else 0
                    for i in range(header_rows, len(table_data)):
                        if i % 2 == 0:
                            t_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fafb'))
                    
                    t.setStyle(t_style)
                    story.append(t)
                    
                    # Page number info for this chunk
                    story.append(Spacer(1, 0.1 * inch))
                    story.append(Paragraph(
                        f'<small>Showing {start_idx + 1} - {end_idx} of {total_rows} records</small>',
                        styles['Normal']
                    ))
                    
                    # Page break
                    if page_num < total_pages - 1:
                        story.append(PageBreak())
                
                story.append(Spacer(1, 0.2 * inch))

        # ===== 5. FOOTER =====
        # Using canvas callback for page numbers
        def add_page_number(canvas, doc):
            page_num = canvas.getPageNumber()
            canvas.saveState()
            
            # Footer line
            canvas.setStrokeColor(colors.lightgrey)
            canvas.setLineWidth(0.5)
            canvas.line(left_margin, bottom_margin - 0.2*inch, 
                       page_size[0] - right_margin, bottom_margin - 0.2*inch)
            
            # Page number
            canvas.setFont('Helvetica', 9)
            canvas.setFillColor(colors.grey)
            canvas.drawRightString(page_size[0] - right_margin, 0.3 * inch, f"Page {page_num}")
            
            canvas.restoreState()

        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes