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

def get_trend_stats(dates, values):
    """Calculates simple trend direction for the AI."""
    if len(dates) < 2: return "Stable", 0
    
    X = np.array([d.toordinal() for d in dates]).reshape(-1, 1)
    y = values.values.reshape(-1, 1)
    model = LinearRegression()
    model.fit(X, y)
    slope = model.coef_[0][0]
    
    trend = "Stable"
    if slope > 0.05: trend = "Increasing"
    if slope < -0.05: trend = "Decreasing"
    
    return trend, slope

def add_extended_regression(ax, dates, values, future_days=28, color='green', label='Trend Line'):
    """Draws regression line and returns the final projected value."""
    if len(dates) < 2: return None

    # 1. Fit Model
    X = np.array([d.toordinal() for d in dates]).reshape(-1, 1)
    y = values.values.reshape(-1, 1)
    model = LinearRegression()
    model.fit(X, y)

    # 2. Predict
    last_date = dates.iloc[-1]
    future_dates = [last_date + timedelta(days=i) for i in range(1, future_days + 1)]
    all_dates = list(dates) + future_dates
    X_all = np.array([d.toordinal() for d in all_dates]).reshape(-1, 1)
    y_pred = model.predict(X_all)

    # 3. Plot
    ax.plot(all_dates, y_pred, color=color, linestyle='--', linewidth=2.5, 
            alpha=0.8, label=f'{label} (Projection)')
    
    # 4. Label
    final_val = y_pred[-1][0]
    ax.text(all_dates[-1], final_val, f"{final_val:.1f}", color=color, 
            fontweight='bold', ha='left', va='center', fontsize=10)
    
    return final_val # Return for AI

def add_holt_winters_forecast(ax, dates, values, future_days=28, color='red'):
    """Draws HW forecast and returns the average predicted value."""
    series = pd.Series(values.values, index=dates).astype(float).asfreq('D').interpolate()
    if len(series) < 14: return None

    # Logic: Use 'add' if zeros exist, else 'mul'
    if (series <= 0).any():
        season_mode, trend_mode = 'add', 'add'
    else:
        season_mode, trend_mode = 'mul', 'add'

    try:
        model = ExponentialSmoothing(
            series, 
            trend=trend_mode, 
            seasonal=season_mode, 
            seasonal_periods=7,
            damped_trend=False
        ).fit()

        forecast = model.forecast(future_days)
        
        plot_dates = [series.index[-1]] + list(forecast.index)
        plot_values = [series.iloc[-1]] + list(forecast.values)
        ax.plot(plot_dates, plot_values, color=color, linestyle='-', linewidth=3, 
                label=f'Seasonal Model (+{future_days} Days)')
        
        return forecast.mean() # Return avg prediction for AI
    except Exception as e:
        print(f"   -> HW Error: {e}")
        return None

def generate_zoom_forecast(history_df):
    """Generates the 7-Day Zoom Chart and returns forecast stats."""
    if history_df.empty: return None, {}

    dates = pd.to_datetime(history_df['Submitted'])
    
    # 1. Forecast VOLUME
    vol_series = pd.Series(history_df['Vol'].values, index=dates).astype(float).asfreq('D').interpolate()
    try:
        mode = 'mul' if (vol_series > 0).all() else 'add'
        vol_model = ExponentialSmoothing(vol_series, trend='add', seasonal=mode, seasonal_periods=7).fit()
        vol_forecast = vol_model.forecast(7)
    except:
        vol_forecast = pd.Series([0]*7)

    # 2. Forecast ERRORS
    err_series = pd.Series(history_df['Errors'].values, index=dates).astype(float).asfreq('D').interpolate()
    try:
        mode_err = 'mul' if (err_series > 0).all() else 'add'
        err_model = ExponentialSmoothing(err_series, trend='add', seasonal=mode_err, seasonal_periods=7).fit()
        err_forecast = err_model.forecast(7)
    except:
        err_forecast = pd.Series([0]*7)

    # 3. Capture Stats for AI
    zoom_stats = {
        "Next_7_Days_Total_Vol": int(vol_forecast.sum()),
        "Next_7_Days_Avg_Vol": int(vol_forecast.mean()),
        "Next_7_Days_Est_Errors": int(err_forecast.sum()),
        "Next_7_Days_Est_Error_Rate": round((err_forecast.sum() / vol_forecast.sum()) * 100, 2) if vol_forecast.sum() > 0 else 0
    }

    # 4. Plotting
    plt.switch_backend('Agg')
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # Volume (Left Axis)
    ax1.plot(vol_forecast.index, vol_forecast.values, color='tab:green', marker='o', linestyle='-', linewidth=3, label='Predicted Volume')
    ax1.set_ylabel("Projected Jobs", color='tab:green', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='tab:green')
    ax1.grid(True, linestyle='--', alpha=0.3)
    for x, y in zip(vol_forecast.index, vol_forecast.values):
        ax1.text(x, y + (y*0.01), f"{int(y)}", color='darkgreen', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Errors (Right Axis)
    ax2 = ax1.twinx()
    ax2.plot(err_forecast.index, err_forecast.values, color='tab:red', marker='x', linestyle='--', linewidth=2, label='Predicted Errors')
    ax2.set_ylabel("Projected Errors", color='tab:red', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    ax2.grid(False)
    for x, y in zip(err_forecast.index, err_forecast.values):
        ax2.text(x, y + (y*0.02), f"{int(y)}", color='darkred', ha='center', va='bottom', fontsize=9, fontweight='bold')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=2)

    ax1.set_title("Predictive Forecast: Next 7 Days (Volume vs Errors)", fontweight='bold', fontsize=16, y=1.08)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%A\n%d-%b'))
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    
    return buf, zoom_stats

def generate_executive_charts(history_df):
    """Generates charts and compiles forecast data for the AI."""
    if history_df.empty: return None, None, None, None, {}

    print("   -> Generating Multi-Model Predictive Charts (Regression + HW)...")
    cutoff_date = pd.to_datetime(config.CURRENT_WEEK_END)
    history_df['Submitted'] = pd.to_datetime(history_df['Submitted']).dt.tz_localize(None)
    history_df = history_df[history_df['Submitted'] <= cutoff_date].copy()
    if history_df.empty: return None, None, None, None, {}

    plt.switch_backend('Agg') 
    buffers = []
    forecast_data = {} # Container for AI data

    # --- 1. SPEED ---
    fig1, ax1 = plt.subplots(figsize=(14, 8))
    ax1.bar(history_df['Submitted'], history_df['Vol'], color='silver', alpha=0.3, label='Daily Vol')
    ax2 = ax1.twinx()
    ax2.plot(history_df['Submitted'], history_df['Speed'], color='tab:blue', alpha=0.3, label='Actual Speed')
    history_df['Speed_Trend'] = history_df['Speed'].rolling(window=7).mean()
    ax2.plot(history_df['Submitted'], history_df['Speed_Trend'], color='navy', linewidth=2, label='7-Day Avg')
    
    # Generate Stats
    final_speed_trend = add_extended_regression(ax2, history_df['Submitted'], history_df['Speed'], future_days=28, color='green', label='Regression Trend')
    avg_speed_hw = add_holt_winters_forecast(ax2, history_df['Submitted'], history_df['Speed'], future_days=28, color='#d62728')
    
    speed_trend_dir, _ = get_trend_stats(history_df['Submitted'], history_df['Speed'])
    forecast_data['Speed_Trend_Direction'] = speed_trend_dir
    forecast_data['Projected_Avg_Speed_Next_Month'] = round(avg_speed_hw, 1) if avg_speed_hw else "N/A"

    ax2.set_ylabel("Automation Time (Sec - Lower is Better)", color='navy', fontweight='bold')
    ax1.set_title("Predicted Speed Forecast: History + 28 Day Projection", fontweight='bold', fontsize=16, y=1.08)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0, 1.05), ncol=2)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    buf1 = io.BytesIO()
    plt.savefig(buf1, format='png', dpi=100)
    buf1.seek(0)
    buffers.append(buf1)
    plt.close(fig1)

    # --- 2. VOLUME ---
    fig2, ax = plt.subplots(figsize=(14, 8))
    ax.plot(history_df['Submitted'], history_df['Vol'], color='tab:green', alpha=0.5, label='Actual Volume')
    add_extended_regression(ax, history_df['Submitted'], history_df['Vol'], future_days=28, color='black', label='Linear Trend')
    avg_vol_hw = add_holt_winters_forecast(ax, history_df['Submitted'], history_df['Vol'], future_days=28, color='orange')
    
    vol_trend_dir, _ = get_trend_stats(history_df['Submitted'], history_df['Vol'])
    forecast_data['Volume_Trend_Direction'] = vol_trend_dir
    forecast_data['Projected_Avg_Daily_Vol_Next_Month'] = int(avg_vol_hw) if avg_vol_hw else "N/A"

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

    # --- 3. RELIABILITY ---
    fig3, ax = plt.subplots(figsize=(14, 8))
    ax.plot(history_df['Submitted'], history_df['ErrorRate'], color='tab:red', alpha=0.5, label='Actual Failure %')
    add_extended_regression(ax, history_df['Submitted'], history_df['ErrorRate'], future_days=28, color='blue', label='Linear Trend')
    avg_err_hw = add_holt_winters_forecast(ax, history_df['Submitted'], history_df['ErrorRate'], future_days=28, color='black')

    err_trend_dir, _ = get_trend_stats(history_df['Submitted'], history_df['ErrorRate'])
    forecast_data['Error_Trend_Direction'] = err_trend_dir
    forecast_data['Projected_Avg_ErrorRate_Next_Month'] = f"{round(avg_err_hw, 2)}%" if avg_err_hw else "N/A"

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

    # --- 4. ZOOM ---
    buf_tactical, zoom_stats = generate_zoom_forecast(history_df)
    forecast_data['Next_7_Days_Tactical'] = zoom_stats

    return buf1, buf2, buf3, buf_tactical, forecast_data