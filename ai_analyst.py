import json
from openai import AzureOpenAI
import config

def get_ai_narrative(data, forecast_data):
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
    2. **Comparative Trends (WoW & MoM):** {json.dumps(data['Comparatives'])}
    3. **Shift Comparison:** {json.dumps(data['Shifts'])}
    4. **Problematic Hours:** {json.dumps(data['Heatmap'])}
    5. **Asset Performance:** {json.dumps(data['Assets'])}
    
    ### PREDICTIVE INTELLIGENCE (FUTURE OUTLOOK):
    The following data comes from our Machine Learning models (Regression + Holt-Winters):
    {json.dumps(forecast_data)}
    
    *Use this to write the 'Future Outlook' section.*

    ### REPORT REQUIREMENTS:
    **Tone:** Clinical, decisive, British English.
    
    **1. Executive Summary & Trends:**
    - Provide a "Stability Score" out of 10.
    - Summarise Week-on-Week (WoW) performance.
    
    **2. Operational Bottlenecks:**
    - Compare Day vs Night shift efficiency.
    - Identify the specific problematic hour.

    **3. Statistical Asset Benchmarking:**
    - Highlight the worst performing asset vs its history.
    
    **4. Future Outlook & Projections:**
    - Explicitly mention the **Projected Volume** for the next 7 days.
    - Discuss the **Trend Direction** (Increasing/Decreasing) for Speed and Errors over the next month.
    - Provide a tactical recommendation based on these forecasts (e.g., "Prepare for rising volume next week").
    """

    response = client.chat.completions.create(
        model=config.AZURE_OPENAI_MODEL,
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.2,
        max_tokens=1000
    )
    return response.choices[0].message.content