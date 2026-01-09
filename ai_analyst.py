import json
from openai import AzureOpenAI
import config

def get_ai_narrative(data):
    """Generates the Executive Benchmark Narrative."""
    print("   -> Requesting AI Analysis...")
    
    client = AzureOpenAI(
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT, 
        api_key=config.AZURE_OPENAI_KEY, 
        api_version=config.AZURE_API_VERSION
    )

    system_prompt = f"""
    You are the Senior Reliability Engineer for a logistics network (UK Region).
    Your job is to write a strategic "Executive Benchmark Report".

    ### INPUT INTELLIGENCE (JSON):
    1. **Baseline Context:** {json.dumps(data['Baseline'])}
    2. **Shift Comparison (Day vs Night):** {json.dumps(data['Shifts'])}
       *Compare efficiency. Is the Night shift struggling?*
    3. **Problematic Hours" (Heatmap):** {json.dumps(data['Heatmap'])}
       *Identify the specific hour where failures spike. Hypothesise why.*
    4. **Printer Watchlist:** {json.dumps(data['Assets'])}
       *The worst performing printer this week.*

    ### REPORT REQUIREMENTS:
    **Tone:** Clinical, decisive, British English (e.g., 'Optimise', 'Centre', 'Programme').
    **Structure:**
    
    **1. Executive Summary:** - A 2-sentence synopsis of the week's health.
    - Give a "Stability Score" out of 10.

    **2. Operational Bottlenecks (Shift & Time):**
    - Explicitly compare Day vs Night performance.
    - Call out the specific time of day causing the most pain (from Heatmap).
    
    **3. Asset & Remediation:**
    - Name the worst performing Warehouse/Printer.
    - Provide 2 technical recommendations for next week.
    """

    response = client.chat.completions.create(
        model=config.AZURE_OPENAI_MODEL,
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.2,
        max_tokens=800
    )
    return response.choices[0].message.content