from fpdf import FPDF

class PDFReport(FPDF): 
    def header(self):
        """Defines the standard header for all pages. 
        This header is used to identify the report as a diagnostic report."""
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Engineering Diagnostic Report', 0, 0, 'R') # 'R' for right alignment
        self.ln(10) # Line break

def build_pdf(narrative_text, data, chart_buffer):
    """
    Compiles the textual analysis and visual assets into a PDF document. This PDF document is used to report the diagnostic results to the user.

    Args:
        narrative_text (str): The text returned by the AI Analyst.
        data (dict): The raw data dictionary. This data is used to populate the PDF document.
        chart_buffer (io.BytesIO): The image buffer from visualization.py.

    Returns:
        bytes: The binary content of the generated PDF.
    """
    pdf = PDFReport()
    pdf.add_page()
    
    # 1. Document Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "System Diagnostic & Asset Check", ln=True) # ln=True is used to move to the next line
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Status: {data['Period']}", ln=True) # ln=True is used to move to the next line
    pdf.ln(5)

    # 2. AI Narrative Section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Automated Analysis", ln=True) # ln=True is used to move to the next line
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, narrative_text) # Multi-cell is used to wrap the text to the width of the page
    pdf.ln(10)

    # 3. Asset Data Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Asset Utilisation Data", ln=True) # ln=True is used to move to the next line
    
    # Table Header
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(80, 10, "Printer ID", 1, 0, 'C', 1) # 'C' is used to center the text
    pdf.cell(60, 10, "Warehouse Location", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Volume", 1, 1, 'C', 1)
    
    # Table Rows
    pdf.set_font("Arial", "", 10)
    for _, row in data['Assets_DF'].iterrows():
        pdf.cell(80, 10, str(row['EnginePrinter']), 1)
        pdf.cell(60, 10, str(row['WarehouseName']), 1)
        pdf.cell(40, 10, str(row['Vol']), 1, 1, 'C')

    # 4. Visualization
    if chart_buffer:
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Visualisation: Volume Distribution", ln=True)
        
        # Write buffer to temporary file for FPDF to read
        with open("temp_chart.png", "wb") as f: # Write the buffer to a temporary file
            f.write(chart_buffer.getbuffer())
        
        pdf.image("temp_chart.png", x=10, y=30, w=180) # Add the image to the PDF

    return pdf.output(dest='S').encode('latin-1') # Encode the PDF to latin-1 to avoid Unicode errors

# This function is used to build the PDF document.