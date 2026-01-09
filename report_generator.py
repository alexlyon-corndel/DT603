from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Executive Benchmark & Predictive Model', 0, 0, 'R')
        self.ln(10)

def clean_utf8(text):
    if not isinstance(text, str): return str(text)
    return text.encode('latin-1', 'replace').decode('latin-1')

def build_pdf(text, data, img_speed, img_vol, img_err, img_tactical):
    pdf = PDFReport()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Executive Benchmark Report", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, clean_utf8(f"Region: {data.get('Period', 'Unknown')}"), ln=True)
    pdf.ln(5)

    # AI Summary
    pdf.set_font("Arial", "", 11)
    clean_text = clean_utf8(text.replace("**", "").replace("###", ""))
    pdf.multi_cell(0, 6, clean_text)
    pdf.ln(10)

    # Asset Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Appendix: Asset Benchmarking Watchlist", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    
    # Headers
    pdf.cell(50, 10, "Printer ID", 1, 0, 'C', 1)
    pdf.cell(35, 10, "Cur Err%", 1, 0, 'C', 1)
    pdf.cell(35, 10, "Hist Err%", 1, 0, 'C', 1)
    pdf.cell(35, 10, "Cur Speed", 1, 0, 'C', 1)
    pdf.cell(35, 10, "Hist Speed", 1, 1, 'C', 1)
    
    pdf.set_font("Arial", "", 10)
    if 'Assets' in data and data['Assets']:
        for row in data['Assets']:
            err_curr = float(row.get('ErrorRate', 0))
            err_hist = float(row.get('Hist_ErrorRate', 0))
            
            if err_curr > (err_hist * 1.5) and err_curr > 3.0: 
                pdf.set_text_color(200, 0, 0)
            else: 
                pdf.set_text_color(0, 0, 0)
            
            p_name = clean_utf8(row.get('EnginePrinter', 'N/A'))
            
            pdf.cell(50, 10, p_name, 1)
            pdf.cell(35, 10, f"{err_curr}%", 1, 0, 'C')
            pdf.cell(35, 10, f"{err_hist}%", 1, 0, 'C')
            pdf.cell(35, 10, str(row.get('Speed',0)), 1, 0, 'C')
            pdf.cell(35, 10, str(row.get('Hist_Speed',0)), 1, 1, 'C')
    else:
        pdf.cell(0, 10, "No Asset Data Available", 1, 1, 'C')
        
    pdf.set_text_color(0, 0, 0)

    # --- 1. PREDICTIVE 7-DAY ZOOM ---
    if img_tactical:
        pdf.add_page(orientation='L')
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "1. Predictive Forecast: Next 7 Days (Zoom)", ln=True)
        with open("temp_tactical.png", "wb") as f: f.write(img_tactical.getbuffer())
        pdf.image("temp_tactical.png", x=10, y=25, w=270)

    # --- 2. PREDICTED VOLUME ---
    if img_vol:
        pdf.add_page(orientation='L')
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "2. Predicted Volume Forecast (4 Weeks)", ln=True)
        with open("temp_vol.png", "wb") as f: f.write(img_vol.getbuffer())
        pdf.image("temp_vol.png", x=10, y=25, w=270)
        
    # --- 3. PREDICTED SPEED ---
    if img_speed:
        pdf.add_page(orientation='L')
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "3. Predicted Speed Forecast (4 Weeks)", ln=True)
        with open("temp_speed.png", "wb") as f: f.write(img_speed.getbuffer())
        pdf.image("temp_speed.png", x=10, y=25, w=270)

    # --- 4. PREDICTED RELIABILITY (ADDED THIS MISSING BLOCK) ---
    if img_err:
        pdf.add_page(orientation='L')
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "4. Predicted Reliability Forecast (4 Weeks)", ln=True)
        with open("temp_err.png", "wb") as f: f.write(img_err.getbuffer())
        pdf.image("temp_err.png", x=10, y=25, w=270)

    return pdf.output(dest='S').encode('latin-1')