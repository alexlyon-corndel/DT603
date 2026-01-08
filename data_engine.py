import pandas as pd
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.helpers import dataframe_from_result_table
import config

def fetch_deep_dive_data():
    """
    Establishes a connection to the Azure Data Explorer (ADX) cluster and executes 
    a preliminary diagnostic query to verify connectivity and data retrieval on the 'PrinterLogs' table.

    This function performs the following operations:
    1. Authenticates using Azure CLI credentials.
    2. Executes a query to fetch the top 5 printers by volume on the 'PrinterLogs' table.
    3. Transforms the Kusto result set into a Pandas DataFrame.
    4. Returns a structured dictionary containing the retrieved printer data 
       and placeholder values for metric keys required by downstream consumers (main.py).

    Returns:
        dict: A dictionary containing:
            - 'Period': Status string indicating test mode.
            - 'Assets': List of dictionaries representing the top 5 printers by volume.
            - 'Assets_DF': Pandas DataFrame of the printer data.
            - Placeholder keys ('Baseline', 'Deltas', 'Shifts', 'Heatmap', 
              'Daily', 'Trends_DF') initialised with empty or zero values 
              to maintain compatibility with the main orchestration logic.
    
    Raises:
        Exception: Captures and logs any connectivity or query execution errors, 
        returning None to prevent application crash.
    """
    
    # Initialize connection to the ADX cluster using configuration credentials
    print(f"Initializing connection to ADX Cluster: {config.ADX_CLUSTER}")
    kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(config.ADX_CLUSTER)
    client = KustoClient(kcsb)

    # Define diagnostic query to fetch top 5 printers by volume
    # Filters by country defined in config.py
    print("Executing diagnostic query...")
    
    query_simple = f"""
    PrinterLogs
    | where Country == "{config.FILTER_COUNTRY}"
    | summarize Vol=count() by EnginePrinter, WarehouseName
    | top 5 by Vol desc
    """

    try:
        # Execute query against the specific database (config.ADX_DB)
        response = client.execute(config.ADX_DB, query_simple)
        
        # Transform primary result table into Pandas DataFrame (df)
        df = dataframe_from_result_table(response.primary_results[0])
        print("✅ Query execution successful. Data retrieved.")
        print(df) 
        
    except Exception as e:
        print(f"❌ Database connection or execution failed: {e}")
        return None

    # Construct and return the data dictionary
    # Includes skeleton structure to satisfy dependency requirements in main.py
    return {
        "Period": "TEST MODE - DIAGNOSTIC RUN",
        "Baseline": {"Volume": 0, "ErrorRate": 0.0, "Speed": 0.0},
        "Deltas": {"Vol_Current": 0},
        "Shifts": [],
        "Heatmap": [],
        "Assets": df.head(5).astype(str).to_dict(orient='records'),
        "Daily": [],
        "Trends_DF": pd.DataFrame(),
        "Assets_DF": df
    }