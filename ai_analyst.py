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
    2. **Comparative Trends (WoW & MoM):** {json.dumps(data['Comparatives'])}
       *CRITICAL: Use these pre-calculated deltas. Note the speed interpretation.*
    3. **Shift Comparison:** {json.dumps(data['Shifts'])}
    4. **Problematic Hours:** {json.dumps(data['Heatmap'])}
    5. **Asset Performance:** {json.dumps(data['Assets'])}

    ### CRITICAL METRIC DEFINITIONS:
    * **Automation Speed (Seconds):** This represents the time taken to process a unit.
      - **LOWER IS BETTER.** (Example: 20s is faster/better than 50s).
      - **Negative Change (e.g., -5s) = IMPROVEMENT (Faster).**
      - **Positive Change (e.g., +10s) = DEGRADATION (Slower).**

    ### REPORT REQUIREMENTS:
    **Tone:** Clinical, decisive, British English.
    
    **1. Executive Summary & Trends:**
    - Provide a "Stability Score" out of 10.
    - **Summarise Week-on-Week (WoW) performance:**
      - Did Volume increase or decrease?
      - Did the system get FASTER (lower seconds) or SLOWER (higher seconds)?
      - Mention Month-on-Month (MoM) trends if significant.

    **2. Operational Bottlenecks:**
    - Compare Day vs Night shift efficiency (remember: Lower Speed = Better).
    - Identify the specific problematic hour and check if it aligns with historic trends.

    **3. Statistical Asset Benchmarking:**
    - Highlight the worst performing asset.
    - Compare its current Error Rate vs its 180-day Historic Average.
    - Compare its current Speed vs its Historic Speed (Is it slowing down?).
    """

    response = client.chat.completions.create(
        model=config.AZURE_OPENAI_MODEL,
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.2,
        max_tokens=800
    )
    return response.choices[0].message.content