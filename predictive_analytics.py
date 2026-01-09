import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from datetime import timedelta
import config  # IMPORTED to get the cutoff date

# --- VISUAL STYLE ---
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")

def add_linear_trend(ax, dates, values, color='green'):
    """
    Requirement 1: Linear Regression Model.
    Draws a straight line of best fit THROUGH the historic data.
    """
    if len(dates) < 2: return

    # Convert dates to ordinal for sklearn
    X = np.array([d.toordinal() for d in dates]).reshape(-1, 1)
    y = values.values.reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)

    # Predict values for the existing range (Trend Line)
    y_pred = model.predict(X)

    # Plot the Trend Line
    ax.plot(dates, y_pred, color=color, linestyle='-', linewidth=2, 
            alpha=0.6, label='Linear Trend (Regression)')

def add_predictive_forecast(ax, dates, values, future_days=7, color='red'):
    """
    Requirement 2: Predictive Analysis Model (Holt-Winters).
    Projects 7 days into the future starting from the last available data point.
    """
    # Prepare Time Series
    series = pd.Series(values.values, index=dates)
    
    series = series.astype(float).asfreq('D').interpolate()

    if len(series) < 14:
        # Fallback if not enough data for complex math
        return

    try:
        # Fit the Seasonal Model
        model = ExponentialSmoothing(
            series, 
            trend='add', 
            seasonal='add', 
            seasonal_periods=7
        ).fit()

        # Forecast the NEXT 7 days
        forecast = model.forecast(future_days)
        
        # Connect the lines visually (Last Actual -> First Forecast)
        plot_dates = [series.index[-1]] + list(forecast.index)
        plot_values = [series.iloc[-1]] + list(forecast.values)

        # Plot the Forecast
        ax.plot(plot_dates, plot_values, color=color, linestyle='--', linewidth=3, 
                label=f'Predictive Forecast (+{future_days} Days)')
        
        # Add value label at the end
        final_val = plot_values[-1]
        ax.text(plot_dates[-1], final_val, f"{final_val:.1f}", 
                color=color, fontweight='bold', ha='left', va='center')

    except Exception as e:
        print(f"   -> Forecast Error: {e}")

def generate_executive_charts(history_df):
    """
    Generates charts containing:
    1. Actual History (Up to Nov 30)
    2. Linear Regression Trend (Green overlay)
    3. Predictive Forecast (Red projection into Dec)
    """
    if history_df.empty: return None, None, None

    print("   -> Generating Multi-Model Predictive Charts...")
    
    cutoff_date = pd.to_datetime(config.CURRENT_WEEK_END)
    
    # 1. Convert to datetime
    history_df['Submitted'] = pd.to_datetime(history_df['Submitted'])
    
    history_df['Submitted'] = history_df['Submitted'].dt.tz_localize(None)
    
    # 3. Filter the dataframe
    history_df = history_df[history_df['Submitted'] <= cutoff_date].copy()
    
    if history_df.empty:
        print("   -> Warning: No data found before the cutoff date.")
        return None, None, None
    # --------------------------------------

    plt.switch_backend('Agg') 
    buffers = []

    # 1. SPEED & LATENCY FORECAST
    fig1, ax1 = plt.subplots(figsize=(14, 7))
    
    # Background: Volume
    ax1.bar(history_df['Submitted'], history_df['Vol'], color='silver', alpha=0.3, label='Daily Vol')
    ax1.grid(False)
    ax1.set_ylabel("Job Volume", color='gray')
    
    # Foreground: Speed
    ax2 = ax1.twinx()
    
    # A. The Actuals (Blue)
    ax2.plot(history_df['Submitted'], history_df['Speed'], color='tab:blue', alpha=0.4, label='Actual Speed')
    
    # B. The 7-Day Moving Avg (Navy)
    history_df['Speed_Trend'] = history_df['Speed'].rolling(window=7).mean()
    ax2.plot(history_df['Submitted'], history_df['Speed_Trend'], color='navy', linewidth=2, label='7-Day Avg')
    
    # C. Linear Regression (Green)
    valid_data = history_df.dropna(subset=['Speed'])
    add_linear_trend(ax2, valid_data['Submitted'], valid_data['Speed'], color='green')
    
    # D. Predictive Forecast (Red)
    add_predictive_forecast(ax2, history_df['Submitted'], history_df['Speed'], color='#d62728')

    ax2.set_ylabel("Automation Time (Sec)", color='navy', fontweight='bold')
    ax1.set_title("Executive Benchmark: Speed (History + Regression + Forecast)", fontweight='bold', fontsize=16)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    
    # Combined Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    buf1 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf1, format='png', dpi=100)
    buf1.seek(0)
    buffers.append(buf1)
    plt.close(fig1)

    # 2. VOLUME & CAPACITY FORECAST
    fig2, ax = plt.subplots(figsize=(14, 7))
    
    # A. Actuals
    ax.plot(history_df['Submitted'], history_df['Vol'], color='tab:green', alpha=0.6, label='Actual Volume')
    
    # B. Moving Avg
    history_df['Vol_Trend'] = history_df['Vol'].rolling(window=7).mean()
    ax.plot(history_df['Submitted'], history_df['Vol_Trend'], color='darkgreen', linewidth=2, label='7-Day Avg')
    
    # C. Linear Regression (Grey)
    add_linear_trend(ax, history_df['Submitted'], history_df['Vol'], color='gray')
    
    # D. Prediction (Orange)
    add_predictive_forecast(ax, history_df['Submitted'], history_df['Vol'], color='orange')

    ax.set_ylabel("Total Jobs Processed", fontweight='bold')
    ax.set_title("Executive Benchmark: Capacity (History + Regression + Forecast)", fontweight='bold', fontsize=16)
    ax.legend(loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))

    buf2 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf2, format='png', dpi=100)
    buf2.seek(0)
    buffers.append(buf2)
    plt.close(fig2)

    # 3. RELIABILITY & ERROR FORECAST
    fig3, ax = plt.subplots(figsize=(14, 7))
    
    # A. Actuals
    ax.plot(history_df['Submitted'], history_df['ErrorRate'], color='tab:red', alpha=0.5, label='Actual Failure %')
    
    # B. Moving Avg
    history_df['Err_Trend'] = history_df['ErrorRate'].rolling(window=7).mean()
    ax.plot(history_df['Submitted'], history_df['Err_Trend'], color='darkred', linewidth=2, label='7-Day Avg')
    
    # C. Linear Regression (Blue)
    add_linear_trend(ax, history_df['Submitted'], history_df['ErrorRate'], color='blue')
    
    # D. Prediction (Black)
    add_predictive_forecast(ax, history_df['Submitted'], history_df['ErrorRate'], color='black')

    ax.set_ylabel("Failure Rate (%)", fontweight='bold', color='darkred')
    ax.set_title("Executive Benchmark: Reliability (History + Regression + Forecast)", fontweight='bold', fontsize=16)
    ax.legend(loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))

    buf3 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf3, format='png', dpi=100)
    buf3.seek(0)
    buffers.append(buf3)
    plt.close(fig3)

    return buf1, buf2, buf3