import base64
import logging
import azure.functions as func
from azure.communication.email import EmailClient 

# Import Local Modules
import config
from data_engine import fetch_deep_dive_data # This function is used to retrieve the asset data from the Kusto (ADX) cluster
from ai_analyst import get_ai_narrative # This function is used to generate the AI commentary on the retrieved assets
from visualisation import create_charts # This function is used to create the volume chart
from report_generator import build_pdf # This function is used to build the PDF document

app = func.FunctionApp() # This is the Azure Function App

def run_orchestrator(): # This function is used to run the diagnostic routine
    """
    Main execution pipeline for the diagnostic routine. 
    
    Sequence of Operations:
    1. Retrieve asset data from Kusto (ADX). 
    2. Generate AI commentary on the retrieved assets. 
    3. Render a volume chart.
    4. Compile results into a PDF.
    5. Dispatch the report via Email.
    """
    print("--- STARTING DIAGNOSTIC SEQUENCE ---") 
    
    # Step 1: Data Retrieval
    data = fetch_deep_dive_data()
    
    if not data:
        print("Critical Failure: No data received. Aborting.") # If no data is received, the function will return
        return

    # Step 2: Intelligence Layer
    narrative = get_ai_narrative(data) # This function is used to generate the AI commentary on the retrieved assets
    
    # Step 3: Visualisation Layer
    # Passing the Assets DataFrame specifically
    chart_img = create_charts(data['Assets_DF']) # This function is used to create the volume chart
    
    # Step 4: Report Generation
    pdf_bytes = build_pdf(narrative, data, chart_img) # This function is used to build the PDF document
    
    # Step 5: Local Save (Artifact Retention)
    with open("DIAGNOSTIC_REPORT.pdf", "wb") as f: # Write the PDF to a file
        f.write(pdf_bytes)
    print("Local PDF artifact saved as 'DIAGNOSTIC_REPORT.pdf'") # Confirmation message

    # Step 6: Communication Layer
    print(f"--- Initiating dispatch to {config.RECIPIENT_EMAIL} ---") # Confirmation message
    try:
        client = EmailClient.from_connection_string(config.ACS_CONNECTION_STRING)
        message = {
            "senderAddress": config.SENDER_ADDRESS,
            "recipients": {"to": [{"address": config.RECIPIENT_EMAIL}]},
            "content": {
                "subject": f"System Diagnostic: {data['Period']}",
                "plainText": "Attached is the diagnostic output from the Top 5 Assets test run.",
            },
            "attachments": [
                {
                    "name": "Diagnostic_Report.pdf", 
                    "contentType": "application/pdf", 
                    "contentInBase64": base64.b64encode(pdf_bytes).decode()
                }
            ]
        }
        client.begin_send(message)
        print("Email dispatch successful.") # Confirmation message
    except Exception as e:
        print(f"Email dispatch failed: {e}") # Error message

# Azure Function Trigger
@app.schedule(schedule="0 0 8 * * 1", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    logging.info('Timer trigger function initiated.') # Confirmation message
    run_orchestrator()
    logging.info('Timer trigger function completed.') # Confirmation message

# Local Entry Point
if __name__ == "__main__":
    run_orchestrator() # Run the diagnostic routine