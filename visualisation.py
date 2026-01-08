import io
import matplotlib.pyplot as plt

def create_charts(assets_df):
    """
    Generates a static bar chart visualising volume per asset. 
    This chart is used to visualise the top 5 printers by volume.
    Args:
        assets_df (pd.DataFrame): DataFrame containing 'EnginePrinter' and 'Vol'.

    Returns:
        io.BytesIO: A binary buffer containing the generated PNG image.
    """
    # Switch backend to Agg to prevent GUI windows from opening during automated execution
    plt.switch_backend('Agg')
    
    if assets_df.empty:
        print("   -> Warning: No data available for visualisation.")
        return None

    # Configure plot aesthetics
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create Bar Chart
    printers = assets_df['EnginePrinter'].astype(str)
    volumes = assets_df['Vol']
    
    ax.bar(printers, volumes, color='#1f77b4')
    
    # Labels and Titles
    ax.set_title("Top 5 Printers by Volume (Diagnostic Run)", fontweight='bold') 
    ax.set_ylabel("Total Jobs Processed")
    ax.set_xlabel("Asset ID")
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    
    return buf 