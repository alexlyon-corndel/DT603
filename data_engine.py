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

    # 1. BASELINE (Current Week Context)
    query_baseline = f"""
    let End = endofday(datetime({config.CURRENT_WEEK_END}));
    let Start = startofday(datetime({config.CURRENT_WEEK_START}));
    PrinterLogs
    | where Submitted between (Start .. End) and Country == "{config.FILTER_COUNTRY}"
    | summarize 
        Vol = count(), 
        Errors = countif(JobStatus=='Error'),
        Speed = avg(todouble(AutomationTimeSeconds))
    | extend ErrorRate = (todouble(Errors) * 100.0) / Vol
    """

    # 2. COMPARATIVE ANALYSIS (WoW & MoM)
    # Calculates metrics for Previous Week (-7d) and Previous Month (-28d)
    query_comparatives = f"""
    let curr_start = startofday(datetime({config.CURRENT_WEEK_START}));
    let curr_end = endofday(datetime({config.CURRENT_WEEK_END}));
    let prev_week_start = curr_start - 7d;
    let prev_week_end = curr_end - 7d;
    let prev_month_start = curr_start - 28d;
    let prev_month_end = curr_end - 28d;
    
    let Current = PrinterLogs 
    | where Submitted between (curr_start .. curr_end) and Country == "{config.FILTER_COUNTRY}"
    | summarize Vol=count(), Err=countif(JobStatus=='Error'), Spd=avg(todouble(AutomationTimeSeconds));
    
    let WeekPrior = PrinterLogs 
    | where Submitted between (prev_week_start .. prev_week_end) and Country == "{config.FILTER_COUNTRY}"
    | summarize Vol=count(), Err=countif(JobStatus=='Error'), Spd=avg(todouble(AutomationTimeSeconds));
    
    let MonthPrior = PrinterLogs 
    | where Submitted between (prev_month_start .. prev_month_end) and Country == "{config.FILTER_COUNTRY}"
    | summarize Vol=count(), Err=countif(JobStatus=='Error'), Spd=avg(todouble(AutomationTimeSeconds));
    
    union (Current | extend Period="Current"), (WeekPrior | extend Period="LastWeek"), (MonthPrior | extend Period="LastMonth")
    | project Period, Vol, ErrorRate=round((todouble(Err)/Vol)*100, 2), Speed=round(Spd, 2)
    """

    # 3. SHIFT ANALYSIS
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

    # 4. FAILURE HEATMAP
    query_heatmap = f"""
    PrinterLogs
    | where Submitted between (startofday(datetime({config.CURRENT_WEEK_START})) .. endofday(datetime({config.CURRENT_WEEK_END})))
    | where Country == "{config.FILTER_COUNTRY}"
    | summarize ErrorCount = countif(JobStatus=='Error') by bin(Submitted, 1h)
    | top 5 by ErrorCount desc
    | project Time = Submitted, ErrorCount
    """
    
    # 5. HISTORIC HOURLY TREND
    query_hourly_trend = f"""
    PrinterLogs
    | where Submitted > ago(180d) and Country == "{config.FILTER_COUNTRY}"
    | extend HourOnly = hourofday(Submitted)
    | summarize AvgErrors = countif(JobStatus=='Error') / 180.0 by HourOnly
    | order by AvgErrors desc
    | take 5
    """

    # 6. ASSET WATCHLIST
    query_assets = f"""
    PrinterLogs
    | where Submitted between (startofday(datetime({config.CURRENT_WEEK_START})) .. endofday(datetime({config.CURRENT_WEEK_END})))
    | where Country == "{config.FILTER_COUNTRY}"
    | summarize Vol=count(), Errors=countif(JobStatus=='Error'), Speed=round(avg(todouble(AutomationTimeSeconds)),1) by EnginePrinter, WarehouseName
    | extend ErrorRate = round((todouble(Errors)/Vol)*100, 2)
    | top 10 by ErrorRate desc
    """

    # 7. ASSET BENCHMARKS
    query_asset_benchmarks = f"""
    PrinterLogs
    | where Submitted > ago(180d) and Country == "{config.FILTER_COUNTRY}"
    | summarize 
        Hist_Speed = round(avg(todouble(AutomationTimeSeconds)), 1),
        Hist_ErrorRate = round((countif(JobStatus=='Error') * 100.0) / count(), 2)
        by EnginePrinter
    """

    # Execution
    print("      ...Executing KQL batch")
    # Note: KustoClient execution order must match the query definition order above
    base_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_baseline).primary_results[0])
    comp_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_comparatives).primary_results[0])
    shifts_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_shifts).primary_results[0])
    heatmap_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_heatmap).primary_results[0])
    hourly_trend_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_hourly_trend).primary_results[0])
    assets_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_assets).primary_results[0])
    bench_df = dataframe_from_result_table(client.execute(config.ADX_DB, query_asset_benchmarks).primary_results[0])

    # Formatting
    if not heatmap_df.empty:
        heatmap_df['Time'] = pd.to_datetime(heatmap_df['Time']).dt.strftime('%Y-%m-%d %H:00')

    baseline = {
        "Volume": int(base_df['Vol'].iloc[0]),
        "ErrorRate": round(float(base_df['ErrorRate'].iloc[0]), 2),
        "Speed": round(float(base_df['Speed'].iloc[0]), 2)
    }

    # Process Comparative Data (Calculate Deltas)
    def get_comp_val(period, col):
        row = comp_df[comp_df['Period'] == period]
        return float(row[col].iloc[0]) if not row.empty else 0

    curr_vol = get_comp_val('Current', 'Vol')
    last_vol = get_comp_val('LastWeek', 'Vol')
    curr_spd = get_comp_val('Current', 'Speed')
    last_spd = get_comp_val('LastWeek', 'Speed')
    
    comparatives = {
        "WoW": {
            "Volume_Change": f"{((curr_vol - last_vol)/last_vol)*100:.1f}%" if last_vol else "N/A",
            "Speed_Current": curr_spd,
            "Speed_Prior": last_spd,
            "Speed_Diff_Seconds": round(curr_spd - last_spd, 2),
            "Speed_Interpretation": "IMPROVED (Faster)" if curr_spd < last_spd else "DEGRADED (Slower)"
        },
        "MoM": {
            "Volume_Change": f"{((curr_vol - get_comp_val('LastMonth', 'Vol'))/get_comp_val('LastMonth', 'Vol'))*100:.1f}%" if get_comp_val('LastMonth', 'Vol') else "N/A",
            "Speed_Diff_Seconds": round(curr_spd - get_comp_val('LastMonth', 'Speed'), 2)
        }
    }

    def safe_json(df):
        return df.head(10).astype(str).to_dict(orient='records')

    merged_assets = pd.merge(assets_df, bench_df, on='EnginePrinter', how='left')

    return {
        "Period": f"{config.CURRENT_WEEK_START} to {config.CURRENT_WEEK_END}",
        "Baseline": baseline,
        "Comparatives": comparatives, # <--- This key is what was missing!
        "Shifts": safe_json(shifts_df),
        "Heatmap": safe_json(heatmap_df),
        "Historic_Hourly_Trend": safe_json(hourly_trend_df),
        "Assets": safe_json(merged_assets),
        "Assets_DF": assets_df
    }

def fetch_long_term_data():
    """Fetches 180 days of granular data to build the Executive Predictive Models."""
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
        
        df['Submitted'] = pd.to_datetime(df['Submitted'])
        df['Vol'] = pd.to_numeric(df['Vol'])
        df['Speed'] = pd.to_numeric(df['Speed'])
        df['Errors'] = pd.to_numeric(df['Errors'])
        df['ErrorRate'] = (df['Errors'] / df['Vol']) * 100
        df['ErrorRate'] = df['ErrorRate'].fillna(0)
        
        print(f"      ...Retrieved {len(df)} days of historic context.")
        return df
    except Exception as e:
        print(f"Failed to fetch history: {e}")
        return pd.DataFrame()