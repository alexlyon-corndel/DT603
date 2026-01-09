import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from datetime import timedelta
import config

# --- VISUAL STYLE ---
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")

def add_extended_regression(ax, dates, values, future_days=28, color='green', label='Trend Line'):
    """
    Draws the Line of Best Fit (Linear Regression) and extends it into the future.
    """
    if len(dates) < 2: return

    # 1. Fit Model on Historic Data
    X = np.array([d.toordinal() for d in dates]).reshape(-1, 1)
    y = values.values.reshape(-1, 1)
    
    model = LinearRegression()
    model.fit(X, y)

    # 2. Generate Future Dates
    last_date = dates.iloc[-1]
    future_dates = [last_date + timedelta(days=i) for i in range(1, future_days + 1)]
    
    # 3. Predict for History + Future
    all_dates = list(dates) + future_dates
    X_all = np.array([d.toordinal() for d in all_dates]).reshape(-1, 1)
    y_pred = model.predict(X_all)

    # 4. Plot
    ax.plot(all_dates, y_pred, color=color, linestyle='--', linewidth=2.5, 
            alpha=0.8, label=f'{label} (Projection)')
    
    # 5. Add Value Label at end of Regression
    final_date = all_dates[-1]
    final_val = y_pred[-1][0]
    ax.text(final_date, final_val, f"{final_val:.1f}", color=color, 
            fontweight='bold', ha='left', va='center', fontsize=10)

def add_holt_winters_forecast(ax, dates, values, future_days=28, color='red'):
    """
    Adds the Seasonal Forecast (Holt-Winters) on top of the data.
    """
    # Ensure float for statsmodels
    series = pd.Series(values.values, index=dates).astype(float).asfreq('D').interpolate()

    if len(series) < 14: return

    try:
        model = ExponentialSmoothing(
            series, 
            trend='add', 
            seasonal='add', 
            seasonal_periods=7,
            damped_trend=True # Tries to dampen wild swings
        ).fit()

        forecast = model.forecast(future_days)
        
        # Connect last actual to first forecast for visual continuity
        plot_dates = [series.index[-1]] + list(forecast.index)
        plot_values = [series.iloc[-1]] + list(forecast.values)

        ax.plot(plot_dates, plot_values, color=color, linestyle='-', linewidth=3, 
                label=f'Seasonal Model (+{future_days} Days)')

    except Exception as e:
        print(f"   -> HW Forecast Error: {e}")

def generate_zoom_forecast(history_df):
    """
    Generates the 7-Day Zoom Chart (formerly Tactical).
    """
    if history_df.empty: return None

    dates = pd.to_datetime(history_df['Submitted'])
    values = history_df['Vol']
    
    series = pd.Series(values.values, index=dates).astype(float).asfreq('D').interpolate()
    try:
        model = ExponentialSmoothing(series, trend='add', seasonal='add', seasonal_periods=7).fit()
        forecast = model.forecast(7)
    except:
        return None

    plt.switch_backend('Agg')
    fig, ax = plt.subplots(figsize=(12, 7)) # Taller to fit titles
    
    # Plot forecast
    ax.plot(forecast.index, forecast.values, color='#d62728', marker='o', linestyle='-', linewidth=3, label='Predicted Volume')
    
    # Add labels
    for x, y in zip(forecast.index, forecast.values):
        ax.text(x, y + (y*0.02), f"{int(y)}", ha='center', va='bottom', fontsize=11, fontweight='bold')

    # UPDATED TITLE
    ax.set_title("Predictive Forecast: Next 7 Days (Zoom)", fontweight='bold', fontsize=16, y=1.05)
    ax.set_ylabel("Projected Jobs")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%A\n%d-%b'))
    
    # Fix Layout
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_executive_charts(history_df):
    """
    Generates charts with BOTH Regression and Holt-Winters.
    """
    if history_df.empty: return None, None, None, None

    print("   -> Generating Multi-Model Predictive Charts (Regression + HW)...")
    
    cutoff_date = pd.to_datetime(config.CURRENT_WEEK_END)
    history_df['Submitted'] = pd.to_datetime(history_df['Submitted']).dt.tz_localize(None)
    history_df = history_df[history_df['Submitted'] <= cutoff_date].copy()
    
    if history_df.empty: return None, None, None, None

    plt.switch_backend('Agg') 
    buffers = []

    # --- 1. PREDICTED SPEED (4 WEEKS) ---
    fig1, ax1 = plt.subplots(figsize=(14, 8)) # Increased height
    
    # Background Vol
    ax1.bar(history_df['Submitted'], history_df['Vol'], color='silver', alpha=0.3, label='Daily Vol')
    
    ax2 = ax1.twinx()
    # Actuals
    ax2.plot(history_df['Submitted'], history_df['Speed'], color='tab:blue', alpha=0.3, label='Actual Speed')
    
    # 7-Day Moving Avg
    history_df['Speed_Trend'] = history_df['Speed'].rolling(window=7).mean()
    ax2.plot(history_df['Submitted'], history_df['Speed_Trend'], color='navy', linewidth=2, label='7-Day Avg')
    
    # A. Regression (The Line of Best Fit - Extended)
    add_extended_regression(ax2, history_df['Submitted'], history_df['Speed'], future_days=28, color='green', label='Regression Trend')
    
    # B. Holt-Winters (The Seasonal Forecast)
    add_holt_winters_forecast(ax2, history_df['Submitted'], history_df['Speed'], future_days=28, color='#d62728')

    ax2.set_ylabel("Automation Time (Sec - Lower is Better)", color='navy', fontweight='bold')
    # Moved Title UP (y=1.08)
    ax1.set_title("Predicted Speed Forecast: History + 28 Day Projection", fontweight='bold', fontsize=16, y=1.08)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    
    # Combined Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0, 1.05), ncol=2)

    plt.tight_layout(rect=[0, 0, 1, 0.95]) # Make room for title
    buf1 = io.BytesIO()
    plt.savefig(buf1, format='png', dpi=100)
    buf1.seek(0)
    buffers.append(buf1)
    plt.close(fig1)

    # --- 2. PREDICTED VOLUME (4 WEEKS) ---
    fig2, ax = plt.subplots(figsize=(14, 8))
    
    # Actuals
    ax.plot(history_df['Submitted'], history_df['Vol'], color='tab:green', alpha=0.5, label='Actual Volume')
    
    # A. Regression (Extended)
    add_extended_regression(ax, history_df['Submitted'], history_df['Vol'], future_days=28, color='black', label='Linear Trend')
    
    # B. Holt-Winters
    add_holt_winters_forecast(ax, history_df['Submitted'], history_df['Vol'], future_days=28, color='orange')

    ax.set_ylabel("Total Jobs Processed", fontweight='bold')
    ax.set_title("Predicted Volume Forecast: History + 28 Day Projection", fontweight='bold', fontsize=16, y=1.08)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.05), ncol=3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png', dpi=100)
    buf2.seek(0)
    buffers.append(buf2)
    plt.close(fig2)

    # --- 3. PREDICTED RELIABILITY (4 WEEKS) ---
    fig3, ax = plt.subplots(figsize=(14, 8))
    
    ax.plot(history_df['Submitted'], history_df['ErrorRate'], color='tab:red', alpha=0.5, label='Actual Failure %')
    
    # A. Regression
    add_extended_regression(ax, history_df['Submitted'], history_df['ErrorRate'], future_days=28, color='blue', label='Linear Trend')
    
    # B. Holt-Winters
    add_holt_winters_forecast(ax, history_df['Submitted'], history_df['ErrorRate'], future_days=28, color='black')

    ax.set_ylabel("Failure Rate (%)", fontweight='bold', color='darkred')
    ax.set_title("Predicted Reliability Forecast: History + 28 Day Projection", fontweight='bold', fontsize=16, y=1.08)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.05), ncol=3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    buf3 = io.BytesIO()
    plt.savefig(buf3, format='png', dpi=100)
    buf3.seek(0)
    buffers.append(buf3)
    plt.close(fig3)

    # --- 4. PREDICTIVE ZOOM (7 DAYS) ---
    buf_tactical = generate_zoom_forecast(history_df)

    return buf1, buf2, buf3, buf_tactical