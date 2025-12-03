"""
Report export module for generating HTML and PDF reports.
"""
import os
import logging
import json
import webbrowser
import html
from pathlib import Path
from typing import Dict, List, Optional, Literal, Union
from datetime import datetime
from dataclasses import asdict

# Import config from the root directory
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import config as app_config

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from utils import REPORTS_DIR
from .report_extractor import StudentReport, ReportCriteria

OutputFormat = Literal['html', 'pdf']

class ReportExporter:
    """Handles exporting reports to different formats."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = REPORTS_DIR
        self.output_dir.mkdir(exist_ok=True)
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        try:
            # Try parsing with the new DD/MM/YYYY format first
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return dt.strftime('%d %B %Y')  # e.g. "25 November 2023"
        except ValueError:
            # Fallback for any other format
            try:
                # Try parsing with the old format for backward compatibility
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%d/%m/%Y')  # Convert to DD/MM/YYYY
            except (ValueError, TypeError):
                return date_str
    
    def _get_html_template(self) -> str:
        """Return the base HTML template for reports."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Student Report - {title}</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    margin: 0; 
                    padding: 20px;
                    color: #333;
                }}
                .header {{ 
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 2px solid #333; 
                    padding-bottom: 10px; 
                    margin-bottom: 20px; 
                }}
                .logo-container {{
                    max-width: 150px;
                    text-align: right;
                }}
                .logo-container img {{
                    max-width: 100%;
                    height: auto;
                }}
                .report-title {{ 
                    color: #2c3e50; 
                    margin: 0;
                }}
                .student-name {{ 
                    color: #2980b9; 
                    margin: 10px 0 0 0;
                }}
                .report-info {{
                    flex: 1;
                }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 15px 0; 
                }}
                th, td {{ 
                    border: 1px solid #ddd; 
                    padding: 8px; 
                    text-align: left; 
                }}
                th {{ 
                    background-color: #f2f2f2; 
                }}
                tr:nth-child(even) {{ 
                    background-color: #f9f9f9; 
                }}
                .report-date {{ 
                    color: #7f8c8d; 
                    font-style: italic; 
                }}
                .page-break {{ 
                    page-break-before: always; 
                }}
                @media print {{
                    .no-print {{
                        display: none;
                    }}
                }}
            </style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """
    
    def _generate_html_report(self, reports: Dict[str, List[StudentReport]], criteria: ReportCriteria) -> str:
        """Generate HTML report content."""
        content_parts = []
        
        # Get logo path from config if available
        logo_path = app_config.get("reports.logo_path") or ""
        
        for student, student_reports in reports.items():
            # Student header with logo
            content_parts.append('<div class="header">')
            content_parts.append('<div class="report-info">')
            content_parts.append('<h1 class="report-title">Student Progress Report</h1>')
            # Escape student name to prevent XSS
            content_parts.append(f'<h2 class="student-name">{html.escape(student)}</h2>')
            
            # Add report period if specified
            if criteria.month and criteria.year:
                month_name = datetime(criteria.year, criteria.month, 1).strftime('%B %Y')
                content_parts.append(f'<p class="report-date">Report Period: {month_name}</p>')
                
            content_parts.append('</div>')  # Close report-info
            
            # Add logo if available
            if logo_path and os.path.exists(logo_path):
                try:
                    # Convert path to file URL for HTML
                    logo_url = Path(logo_path).as_uri()
                    content_parts.append(f'''
                    <div class="logo-container">
                        <img src="{logo_url}" alt="Logo" />
                    </div>''')
                except Exception as e:
                    logging.warning(f"Failed to include logo in report: {e}")
            

            content_parts.append('</div>')
            
            # Reports table
            for report in student_reports:
                content_parts.append('<div class="report">')
                content_parts.append(f'<p class="report-date">Report Date: {self._format_date(report.get("date", ""))}</p>')
                
                # Create a table for the report data
                # Escape HTML to prevent XSS attacks
                def escape_html(text: str) -> str:
                    """Escape HTML special characters."""
                    if not text:
                        return ""
                    return html.escape(str(text))
                
                def format_multiline(text: str) -> str:
                    """Format multiline text with HTML line breaks."""
                    if not text:
                        return "N/A"
                    # Escape HTML first, then convert newlines to <br>
                    escaped = escape_html(text)
                    return escaped.replace("\n", "<br>")
                
                report_data = [
                    ["Field", "Value"],
                    ["Teacher", escape_html(report.get("teacher_name", "N/A"))],
                    ["Quran Surah", escape_html(report.get("quran_surah", "N/A"))],
                    ["Tafseer", escape_html(report.get("tafseer", "N/A"))],
                    ["Noor Page", escape_html(report.get("noor_page", "N/A"))],
                    ["Tajweed Rules", escape_html(report.get("tajweed_rules", "N/A"))],
                    ["Topic", escape_html(report.get("topic", "N/A"))],
                    ["Homework", format_multiline(report.get("homework", ""))],
                    ["Parent Notes", format_multiline(report.get("parent_notes", ""))],
                    ["Admin Notes", format_multiline(report.get("admin_notes", ""))]
                ]
                
                table_html = ['<table>']
                for row in report_data:
                    table_html.append('<tr>')
                    for cell in row:
                        table_html.append(f'<td>{cell}</td>')
                    table_html.append('</tr>')
                table_html.append('</table>')
                
                content_parts.extend(table_html)
                content_parts.append('</div>')
                content_parts.append('<hr>')  # Separator between reports
        
        # Join all parts and insert into template
        content = '\n'.join(content_parts)
        return self._get_html_template().format(
            title=f"Student Report - {datetime.now().strftime('%Y-%m-%d')}",
            content=content
        )
    
    def _generate_pdf_report(
        self, 
        reports: Dict[str, List[StudentReport]], 
        output_path: Path,
        criteria: ReportCriteria
    ) -> Path:
        """Generate a PDF report and return the file path.
        
        Args:
            reports: Dictionary of student reports
            output_path: Path where PDF should be saved
            criteria: Report criteria used for generation
            
        Returns:
            Path to the generated PDF file
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus.flowables import KeepTogether
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get logo path from config
        logo_path = app_config.get("reports.logo_path", "")
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=6,
            alignment=1  # Center aligned
        )
        heading_style = ParagraphStyle(
            'Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=6,
            alignment=1  # Center aligned
        )
        
        # Function to create header with logo
        def create_header(student: str, elements: list) -> None:
            # Create a table for the header with logo
            header_data = []
            
            # Add logo if available
            logo_img = None
            if logo_path and os.path.exists(logo_path):
                try:
                    logo_img = Image(logo_path, width=1.5*inch, height=0.75*inch)
                    logo_img.hAlign = 'RIGHT'
                except Exception as e:
                    logging.warning(f"Failed to load logo for PDF: {e}")
            
            # Create a table with two columns: title and logo
            header_table = Table([
                [
                    Paragraph("Student Progress Report", title_style),
                    logo_img or ''  # Empty string if no logo
                ]
            ], colWidths=['70%', '30%'])
            
            # Style the header table
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(header_table)
            elements.append(Paragraph(student, heading_style))
            
            if criteria.month and criteria.year:
                month_name = datetime(criteria.year, criteria.month, 1).strftime('%B %Y')
                elements.append(Paragraph(f"Report Period: {month_name}", styles['Normal']))
            
            elements.append(Spacer(1, 12))
        
        # Build the document content
        elements = []
        
        for student, student_reports in reports.items():
            # Add header with logo
            create_header(student, elements)
            
            # Add each report
            for report in student_reports:
                # Report date
                report_date = self._format_date(report.get("date", ""))
                
                # Create table data
                table_data = [
                    ["Field", "Value"],
                    ["Teacher", report.get("teacher_name", "N/A")],
                    ["Quran Surah", report.get("quran_surah", "N/A")],
                    ["Tafseer", report.get("tafseer", "N/A")],
                    ["Noor Page", report.get("noor_page", "N/A")],
                    ["Tajweed Rules", report.get("tajweed_rules", "N/A")],
                    ["Topic", report.get("topic", "N/A")],
                    ["Homework", report.get("homework", "N/A")],
                    ["Parent Notes", report.get("parent_notes", "N/A")],
                    ["Admin Notes", report.get("admin_notes", "N/A")]
                ]
                
                # Create table
                table = Table(table_data, colWidths=[doc.width/3.0, doc.width*2/3.0])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 24))  # Add space between reports
                
                # Add page break if not the last report
                if report != student_reports[-1]:
                    elements.append(Spacer(1, 12))
                    elements.append(Paragraph("-" * 50, styles['Normal']))
                    elements.append(Spacer(1, 12))
                else:
                    elements.append(Spacer(1, 12))
        
        # Build the PDF
        doc.build(elements)
        
        return output_path
    
    def export_report(
        self, 
        reports: Dict[str, List[StudentReport]], 
        output_format: OutputFormat,
        criteria: ReportCriteria,
        open_after: bool = True
    ) -> Path:
        """
        Export reports to the specified format.
        
        Args:
            reports: Dictionary of student reports
            output_format: 'html' or 'pdf'
            criteria: Report criteria used for generation
            open_after: Whether to open the file after generation
            
        Returns:
            Path to the generated report file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"student_report_{timestamp}.{output_format}"
        output_path = self.output_dir / filename
        
        if output_format == 'html':
            html_content = self._generate_html_report(reports, criteria)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        else:  # PDF
            output_path = self._generate_pdf_report(reports, output_path, criteria)
        
        if open_after:
            webbrowser.open(f"file://{output_path.absolute()}")
            
        return output_path
