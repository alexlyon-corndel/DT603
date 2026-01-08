import json
from openai import AzureOpenAI
import config

def get_ai_narrative(data):
    """
    Generates a preliminary operational summary using Azure OpenAI.
    
    In 'Test Mode', this function receives a reduced dataset. The system prompt 
    is adjusted to strictly analyse the provided asset list, disregarding 
    missing baseline or trend data to prevent hallucination.

    Args:
        data (dict): The data dictionary returned by data_engine.fetch_deep_dive_data().

    Returns:
        str: A text response containing the AI-generated analysis of the top assets.
    """
    print("   -> Requesting AI analysis of asset data...")
    
    client = AzureOpenAI(
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT, 
        api_key=config.AZURE_OPENAI_KEY, 
        api_version=config.AZURE_API_VERSION
    )

    # Simplified Prompt for Test Mode
    system_prompt = f"""
    You are a Printer Reliability Engineer.
    Your task is to review the following list of high-volume printers (Top 5 by usage) and provide a brief, professional summary of which printers are under the heaviest load.
    TASK:
    Review the following list of high-volume printers (Top 5 by usage) and provide a brief, professional summary of which printers are under the heaviest load.
    Provide a brief, professional summary of which assets are under the heaviest load. Your output should be no more than 300 tokens.
    
    Your output should be no more than 1 page. 
    
    DATA:
    {json.dumps(data['Assets'])}
    
    OUTPUT FORMAT:
    - Use British English.
    - Bullet points.
    - No filler text.
    """

    response = client.chat.completions.create(
        model=config.AZURE_OPENAI_MODEL,
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.2,
        max_tokens=300
    )
    return response.choices[0].message.content