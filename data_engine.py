import pandas as pd
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.helpers import dataframe_from_result_table
import config

def get_client():
    kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(config.ADX_CLUSTER)
    return KustoClient(kcsb)

def fetch_deep_dive_data():
    """Fetches the current week's detailed tactical data for the AI Narrative."""
    client = get_client()
    print(f"   -> Fetching Tactical Data ({config.CURRENT_WEEK_START})...")

    # 1. BASELINE (Context)
    query_baseline = f"""
    let End = endofday(datetime({config.CURRENT_WEEK_END}));
    let Start = startofday(datetime({config.CURRENT_WEEK_END}) - 90d);
    PrinterLogs
    | where Submitted between (Start .. End) and Country == "{config.FILTER_COUNTRY}"
    | summarize 
        Baseline_Vol_Weekly = count() / 12.8, 
        Baseline_Error_Rate = (countif(JobStatus=='Error') * 100.0) / count(),
        Baseline_Speed = avg(todouble(AutomationTimeSeconds))
    """

    # 2. SHIFT ANALYSIS (Day vs Night)
    query_shifts = f"""     
    PrinterLogs
    | where Submitted between (startofday(datetime({config.CURRENT_WEEK_START})) .. endofday(datetime({config.CURRENT_WEEK_END})))
    | where Country == "{config.FILTER_COUNTRY}"
    | summarize 
        Vol = count(), 
        Errors = countif(JobStatus == 'Error'),
        Speed = round(avg(todouble(AutomationTimeSeconds)), 1)
        by Shift 
    | extend ErrorRate = round((todouble(Errors)/Vol)*100, 2)
    """

    # 3. FAILURE HEATMAP (Specific Bad Hours)
    query_heatmap = f"""
    PrinterLogs
    | where Submitted between (startofday(datetime({config.CURRENT_WEEK_START})) .. endofday(datetime({config.CURRENT_WEEK_END})))
    | where Country == "{config.FILTER_COUNTRY}"
    | summarize ErrorCount = countif(JobStatus=='Error') by bin(Submitted, 1h)
    | top 5 by ErrorCount desc
    | project Time = Submitted, ErrorCount
    """

    # 4. ASSET WATCHLIST (Worst Offenders)
    query_assets = f"""
    PrinterLogs
    | where Submitted between (startofday(datetime({config.CURRENT_WEEK_START})) .. endofday(datetime({config.CURRENT_WEEK_END})))
    | where Country == "{config.FILTER_COUNTRY}"
    | summarize Vol=count(), Errors=countif(JobStatus=='Error'), Speed=round(avg(todouble(AutomationTimeSeconds)),1) by EnginePrinter, WarehouseName
    | extend ErrorRate = round((todouble(Errors)/Vol)*100, 2)
    | top 5 by ErrorRate desc
    """

    # Execution
    print("      ...Executing KQL batch")
    base_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_baseline).primary_results[0])
    shifts_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_shifts).primary_results[0])
    heatmap_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_heatmap).primary_results[0])
    assets_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_assets).primary_results[0])

    # Formatting
    if not heatmap_df.empty:
        heatmap_df['Time'] = pd.to_datetime(heatmap_df['Time']).dt.strftime('%Y-%m-%d %H:00')

    baseline = {
        "Volume": int(base_df['Baseline_Vol_Weekly'].iloc[0]),
        "ErrorRate": round(float(base_df['Baseline_Error_Rate'].iloc[0]), 2),
        "Speed": round(float(base_df['Baseline_Speed'].iloc[0]), 2)
    }

    def safe_json(df):
        return df.head(10).astype(str).to_dict(orient='records')

    return {
        "Period": f"{config.CURRENT_WEEK_START} to {config.CURRENT_WEEK_END}",
        "Baseline": baseline,
        "Shifts": safe_json(shifts_df),
        "Heatmap": safe_json(heatmap_df),
        "Assets": safe_json(assets_df),
        "Assets_DF": assets_df
    }

def fetch_long_term_data():
    """
    Fetches 180 days of granular data to build the Executive Predictive Models.
    This enables seasonality detection and regression forecasting.
    """
    client = get_client()
    print("   -> Fetching 180-Day Historic Data for Predictive Modeling...")

    query_history = f"""
    let End = endofday(datetime({config.CURRENT_WEEK_END}));
    let Start = startofday(datetime({config.CURRENT_WEEK_END}) - 180d);
    PrinterLogs
    | where Submitted between (Start .. End) and Country == "{config.FILTER_COUNTRY}"
    | summarize 
        Vol = count(), 
        Errors = countif(JobStatus=='Error'), 
        Speed = avg(todouble(AutomationTimeSeconds))
        by bin(Submitted, 1d)
    | order by Submitted asc
    """
    
    try:
        response = client.execute(config.ADX_DB, query_history)
        df = dataframe_from_result_table(response.primary_results[0])
        
        # Type Conversion
        df['Submitted'] = pd.to_datetime(df['Submitted'])
        df['Vol'] = pd.to_numeric(df['Vol'])
        df['Speed'] = pd.to_numeric(df['Speed'])
        df['Errors'] = pd.to_numeric(df['Errors'])
        
        # Calculate Daily Error Rate %
        df['ErrorRate'] = (df['Errors'] / df['Vol']) * 100
        df['ErrorRate'] = df['ErrorRate'].fillna(0)
        
        print(f"      ...Retrieved {len(df)} days of historic context.")
        return df
    except Exception as e:
        print(f"Failed to fetch history: {e}")
        return pd.DataFrame()