import base64
import logging
import azure.functions as func
from azure.communication.email import EmailClient

import config
from data_engine import fetch_deep_dive_data, fetch_long_term_data
from ai_analyst import get_ai_narrative
from predictive_analytics import generate_executive_charts
from report_generator import build_pdf

app = func.FunctionApp()

def run_orchestrator():
    print("--- STARTING EXECUTIVE BENCHMARK SEQUENCE ---")
    
    # 1. Fetch Weekly Tactical Data (History)
    weekly_data = fetch_deep_dive_data()
    
    # 2. Fetch Long-Term Historic Data (History)
    history_df = fetch_long_term_data()
    
    # 3. GENERATE GRAPHS + PREDICTIVE DATA (The Swap!)
    # 'forecast_stats' to pass to the AI
    img_speed, img_vol, img_err, img_tactical, forecast_stats = generate_executive_charts(history_df)
    
    # 4. Generate AI Commentary (Now with Forecast Intelligence)
    narrative = get_ai_narrative(weekly_data, forecast_stats)
    
    # 5. Build PDF
    print("   -> Compiling Executive PDF...")
    pdf_bytes = build_pdf(narrative, weekly_data, img_speed, img_vol, img_err, img_tactical)
    
    # 6. Save Locally
    with open("EXECUTIVE_BENCHMARK.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF Saved as EXECUTIVE_BENCHMARK.pdf")

    # 7. Send Email
    print(f"--- Dispatching to {config.RECIPIENT_EMAIL} ---")
    try:
        client = EmailClient.from_connection_string(config.ACS_CONNECTION_STRING)
        message = {
            "senderAddress": config.SENDER_ADDRESS,
            "recipients": {"to": [{"address": config.RECIPIENT_EMAIL}]},
            "content": {
                "subject": f"Executive Benchmark: {config.FILTER_COUNTRY} ({weekly_data['Period']})",
                "plainText": "Attached is the Predictive Executive Benchmark Report.",
            },
            "attachments": [
                {
                    "name": "Executive_Benchmark.pdf", 
                    "contentType": "application/pdf", 
                    "contentInBase64": base64.b64encode(pdf_bytes).decode()
                }
            ]
        }
        client.begin_send(message)
        print("Email Sent.")
    except Exception as e:
        print(f"❌ Email Failed: {e}")

# Azure Function Trigger
@app.schedule(schedule="0 0 8 * * 1", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    logging.info('Timer trigger function initiated.')
    run_orchestrator()
    logging.info('Timer trigger function completed.')

if __name__ == "__main__":
    run_orchestrator()