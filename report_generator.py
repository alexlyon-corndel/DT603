from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Executive Benchmark & Predictive Model', 0, 0, 'R')
        self.ln(10)

def clean_utf8(text):
    """
    Sanitizes text to be compatible with Latin-1 PDF encoding.
    Replaces common incompatible characters (like smart quotes, em-dashes, etc.)
    """
    if not isinstance(text, str):
        return str(text)
        
    replacements = {
        '\u2018': "'",  # Left single quote
        '\u2019': "'",  # Right single quote
        '\u201c': '"',  # Left double quote
        '\u201d': '"',  # Right double quote
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '\u2026': '...', # Ellipsis
        '\u00A0': ' ',   # Non-breaking space
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
        
    # Final fallback: encode to latin-1, replacing errors with '?'
    return text.encode('latin-1', 'replace').decode('latin-1')

def build_pdf(text, data, img_speed, img_vol, img_err):
    pdf = PDFReport()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Executive Benchmark Report", ln=True)
    pdf.set_font("Arial", "", 10)
    # Sanitize the period string just in case
    clean_period = clean_utf8(f"Region: {data.get('Period', 'Unknown')}")
    pdf.cell(0, 10, clean_period, ln=True)
    pdf.ln(5)

    # AI Summary
    pdf.set_font("Arial", "", 11)
    # Clean the Markdown AND the special characters
    clean_text = clean_utf8(text.replace("**", "").replace("###", ""))
    pdf.multi_cell(0, 6, clean_text)
    pdf.ln(10)

    # Asset Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Appendix: Critical Asset Watchlist", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, "Warehouse", 1, 0, 'C', 1)
    pdf.cell(60, 10, "Printer ID", 1, 0, 'C', 1)
    pdf.cell(30, 10, "Vol", 1, 0, 'C', 1)
    pdf.cell(30, 10, "Error %", 1, 1, 'C', 1)
    
    pdf.set_font("Arial", "", 10)
    # Check if Assets_DF exists before iterating
    if 'Assets_DF' in data and not data['Assets_DF'].empty:
        for _, row in data['Assets_DF'].iterrows():
            if row['ErrorRate'] > 5.0: pdf.set_text_color(200, 0, 0)
            else: pdf.set_text_color(0, 0, 0)
            
            # Clean table data
            w_name = clean_utf8(row['WarehouseName'])
            p_name = clean_utf8(row['EnginePrinter'])
            
            pdf.cell(60, 10, w_name, 1)
            pdf.cell(60, 10, p_name, 1)
            pdf.cell(30, 10, str(row['Vol']), 1, 0, 'C')
            pdf.cell(30, 10, f"{row['ErrorRate']}%", 1, 1, 'C')
    else:
        pdf.cell(0, 10, "No Asset Data Available", 1, 1, 'C')
        
    pdf.set_text_color(0, 0, 0)

    # --- CHART 1: SPEED ---
    if img_speed:
        pdf.add_page(orientation='L')
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "1. Speed & Latency Forecast", ln=True)
        with open("temp_speed.png", "wb") as f: f.write(img_speed.getbuffer())
        pdf.image("temp_speed.png", x=10, y=25, w=270)

    # --- CHART 2: VOLUME ---
    if img_vol:
        pdf.add_page(orientation='L')
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "2. Volume & Capacity Forecast", ln=True)
        with open("temp_vol.png", "wb") as f: f.write(img_vol.getbuffer())
        pdf.image("temp_vol.png", x=10, y=25, w=270)

    # --- CHART 3: ERRORS ---
    if img_err:
        pdf.add_page(orientation='L')
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "3. Reliability & Error Rate Forecast", ln=True)
        with open("temp_err.png", "wb") as f: f.write(img_err.getbuffer())
        pdf.image("temp_err.png", x=10, y=25, w=270)

    return pdf.output(dest='S').encode('latin-1')