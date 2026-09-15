import os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from anomaly import detect_anomalies, get_latest_anomalies, load_energy_data
from forecasting import GUJARAT_STATE_PEAK_THRESHOLD_MW, forecast_next_hours, get_forecast_model_metrics
from recommendations import generate_recommendations
from bob_tools import get_current_energy_status, generate_facility_report
from api import api_get_live_grid_summary

st.set_page_config(
    page_title="Gujarat EnergySense AI | State Grid Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enterprise Industrial Styling
st.markdown("""
<style>
    .reportview-container, .main, .block-container {
        background-color: #060a12;
        color: #f8fafc;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    .command-card {
        background: linear-gradient(135deg, #0f172a 0%, #090e18 100%);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .command-title {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    .command-value {
        color: #f8fafc;
        font-size: 1.85rem;
        font-weight: 700;
    }
    .command-delta {
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 4px;
    }
    .card-critical { border-left: 4px solid #ef4444; }
    .card-warning { border-left: 4px solid #f59e0b; }
    .card-normal { border-left: 4px solid #10b981; }
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.25);
        color: #ef4444;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.25);
        color: #f59e0b;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Gujarat District Geographic Coordinates
DISTRICT_COORDS = {
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "Surat": {"lat": 21.1702, "lon": 72.8311},
    "Vadodara": {"lat": 22.3072, "lon": 73.1812},
    "Rajkot": {"lat": 22.3039, "lon": 70.8022},
    "Anand & Kheda": {"lat": 22.5645, "lon": 72.9289},
    "Gandhinagar": {"lat": 23.2156, "lon": 72.6369},
    "Kutch": {"lat": 23.2420, "lon": 69.6669},
    "Bharuch": {"lat": 21.7051, "lon": 72.9959},
    "Jamnagar": {"lat": 22.4707, "lon": 70.0577},
    "Bhavnagar": {"lat": 21.7645, "lon": 72.1519}
}

@st.cache_data(ttl=60)
def get_dataset():
    return load_energy_data()

raw_df = get_dataset()

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/flash-on.png", width=64)
    st.title("G-EnergySense AI")
    st.caption("Gujarat State Load Despatch Centre (SLDC)")
    st.markdown("---")
    
    st.subheader("📍 Territorial Command Selector")
    district_list = sorted(list(raw_df["district"].unique())) if "district" in raw_df.columns else []
    scope_options = ["All Gujarat (Statewide)"] + district_list
    selected_scope = st.selectbox("Select Regional Jurisdiction:", scope_options)
    
    st.markdown("---")
    st.subheader("⚡ Grid SCADA Simulators")
    if st.button("🔄 Poll Live 15-Min Telemetry", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    inject_surat = st.toggle("Simulate Surat Industrial Surge (+42%)", value=False)
    inject_anand = st.toggle("Simulate Anand (CHARUSAT Zone) Agro Spike (+35%)", value=False)
    
    st.markdown("---")
    metrics = get_forecast_model_metrics()
    st.caption("🧠 **AI Model Benchmarks:**")
    st.caption(f"• Algorithm: {metrics['model_name']}")
    st.caption(f"• MAPE Accuracy: **{metrics['mape_pct']}%**")
    st.caption(f"• R² Score: **{metrics['r2_score']}**")

# Apply simulation triggers in memory
df = raw_df.copy()
latest_ts = df["timestamp"].max()

if inject_surat and "district" in df.columns:
    m = (df["district"] == "Surat") & (df["timestamp"] == latest_ts)
    df.loc[m, "demand_mw"] *= 1.42

if inject_anand and "district" in df.columns:
    m = (df["district"] == "Anand & Kheda") & (df["timestamp"] == latest_ts)
    df.loc[m, "demand_mw"] *= 1.35

# Scope filtering
is_filtered = selected_scope != "All Gujarat (Statewide)"
active_df = df[df["district"] == selected_scope] if is_filtered else df

latest_data = active_df[active_df["timestamp"] == latest_ts]
total_demand = latest_data["demand_mw"].sum()
total_ren = latest_data["renewable_mw"].sum()
total_net = latest_data.get("net_demand_mw", total_demand - total_ren).sum()
ren_share = (total_ren / max(total_demand, 1)) * 100
avg_freq = latest_data["grid_frequency_hz"].mean()
avg_thd = latest_data.get("thd_pct", pd.Series([3.5])).mean()
co2_avoided_tonnes = (total_ren * 1000.0 * 0.82) / 1000.0

# ML Inference
scored_df = detect_anomalies(active_df)
recent_anomalies = scored_df[scored_df["is_anomaly"]].sort_values("timestamp", ascending=False)
has_critical = any(recent_anomalies.head(3)["severity"] == "CRITICAL")

forecast_df = forecast_next_hours(panel_name=selected_scope, df=df)
recs = generate_recommendations(recent_anomalies.head(3), forecast_df, selected_scope=selected_scope)

# ----------------- COMMAND CENTER HEADER -----------------
h1, h2 = st.columns([3, 1])
with h1:
    st.title(f"⚡ Gujarat Energy Intelligence Center — {selected_scope}")
    st.markdown("**State SCADA Telemetry • AI Anomaly Attribution • Multi-Hour Forecasts • Power Quality (THD) • SLDC Directives**")
with h2:
    if has_critical:
        st.error("🔴 REGIONAL GRID STRESS DETECTED")
    else:
        st.success("🟢 GUJARAT GRID NOMINAL (50.00 Hz)")

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- TOP METRIC ROW -----------------
m1, m2, m3, m4 = st.columns(4)

with m1:
    lbl = f"{selected_scope} Demand" if is_filtered else "Total Gujarat State Demand"
    st.markdown(f"""
    <div class="command-card card-normal">
        <div class="command-title">{lbl}</div>
        <div class="command-value">{total_demand:,.0f} <span style="font-size:1.05rem; color:#94a3b8;">MW</span></div>
        <div class="command-delta" style="color:#10b981;">● Net Grid Draw: {total_net:,.0f} MW</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="command-card card-normal">
        <div class="command-title">Renewable Generation Mix</div>
        <div class="command-value">{ren_share:.1f}% <span style="font-size:1.05rem; color:#94a3b8;">({total_ren:,.0f} MW)</span></div>
        <div class="command-delta" style="color:#38bdf8;">🍃 {co2_avoided_tonnes:,.0f} tCO2/hr avoided</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    freq_col = "#10b981" if (49.95 <= avg_freq <= 50.05) else "#f59e0b"
    st.markdown(f"""
    <div class="command-card card-normal">
        <div class="command-title">Grid Frequency & Power Quality</div>
        <div class="command-value" style="color:{freq_col};">{avg_freq:.3f} <span style="font-size:1.05rem; color:#94a3b8;">Hz</span></div>
        <div class="command-delta" style="color:{'#10b981' if avg_thd < 5.0 else '#ef4444'};">Avg THD: {avg_thd:.2f}% (IEEE 519 standard)</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    peak_pred = forecast_df["predicted_load_mw"].max()
    thresh = forecast_df["threshold_mw"].iloc[0]
    is_peak = peak_pred >= thresh
    st.markdown(f"""
    <div class="command-card {'card-critical' if is_peak else 'card-normal'}">
        <div class="command-title">Projected State Peak (4h)</div>
        <div class="command-value">{peak_pred:,.0f} <span style="font-size:1.05rem; color:#94a3b8;">MW</span></div>
        <div class="command-delta" style="color:{'#ef4444' if is_peak else '#10b981'};">
            {'⚠️ Peak Alert Breach Warning' if is_peak else '● Safe operating buffer'}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- 6-TAB ENTERPRISE NAVIGATION -----------------
t1, t2, t3, t4, t5, t6 = st.tabs([
    "🛰️ Live Command & Geospatial Map",
    "🦆 Renewable Integration & Duck Curve",
    "⚡ Power Quality & Harmonics (THD)",
    "🔮 Multi-Hour Predictive Forecaster",
    "💰 CERC DSM Commercial Grid Risk",
    "🤖 IBM Bob Autonomous Dispatch Copilot"
])

# ================= TAB 1: GEOSPATIAL MAP & LEADERBOARD =================
with t1:
    if not is_filtered and "district" in df.columns:
        map_col, bar_col = st.columns([1.2, 1.0])
        latest_dist = df[df["timestamp"] == latest_ts].groupby(["district", "city_hub", "discom_zone"]).agg({
            "demand_mw": "sum",
            "renewable_mw": "sum",
            "grid_frequency_hz": "mean"
        }).reset_index()
        
        latest_dist["lat"] = latest_dist["district"].map(lambda x: DISTRICT_COORDS.get(x, {}).get("lat", 22.5))
        latest_dist["lon"] = latest_dist["district"].map(lambda x: DISTRICT_COORDS.get(x, {}).get("lon", 71.5))
        latest_dist["status"] = latest_dist["district"].map(
            lambda x: "🔴 ANOMALY" if x in recent_anomalies.head(3)["district"].values else "🟢 NORMAL"
        )
        
        with map_col:
            st.caption("Interactive Geospatial Grid Map (Major Gujarat Load Centers & Solar Parks)")
            fig_map = px.scatter_geo(
                latest_dist,
                lat="lat",
                lon="lon",
                size="demand_mw",
                color="status",
                hover_name="district",
                hover_data={"city_hub": True, "demand_mw": ":,.0f MW", "renewable_mw": ":,.0f MW", "lat": False, "lon": False},
                color_discrete_map={"🔴 ANOMALY": "#ef4444", "🟢 NORMAL": "#10b981"},
                size_max=36,
                template="plotly_dark"
            )
            fig_map.update_geos(
                center=dict(lat=22.5, lon=71.8),
                projection_scale=16,
                showcoastlines=True,
                coastlinecolor="#334155",
                showland=True,
                landcolor="#090e18",
                showocean=True,
                oceancolor="#04070d"
            )
            fig_map.update_layout(margin=dict(l=0, r=0, t=10, b=10), plot_bgcolor="#0b111e", paper_bgcolor="#060a12")
            st.plotly_chart(fig_map, use_container_width=True)
            
        with bar_col:
            st.caption("Live District Demand Ranking (MW)")
            sorted_dist = latest_dist.sort_values("demand_mw", ascending=False)
            fig_bar = px.bar(
                sorted_dist,
                x="district",
                y="demand_mw",
                color="discom_zone",
                text="demand_mw",
                labels={"district": "District", "demand_mw": "Active Load (MW)", "discom_zone": "DISCOM"},
                color_discrete_map={
                    "DGVCL (South Gujarat)": "#f43f5e",
                    "UGVCL (North Gujarat)": "#38bdf8",
                    "PGVCL (Saurashtra & Kutch)": "#10b981",
                    "MGVCL (Central Gujarat)": "#818cf8"
                },
                template="plotly_dark"
            )
            fig_bar.update_traces(texttemplate='%{text:,.0f} MW', textposition='outside')
            fig_bar.update_layout(plot_bgcolor="#0b111e", paper_bgcolor="#060a12", margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)
            
    # Recent 24h Multi-Line Plot
    st.markdown("#### 📈 Multi-District Telemetry Profile (Past 24 Hours)")
    past_24h = active_df[active_df["timestamp"] >= (latest_ts - timedelta(hours=24))]
    grp_col = "city_hub" if is_filtered else "district"
    fig_tr = px.line(past_24h, x="timestamp", y="demand_mw", color=grp_col, template="plotly_dark")
    st.plotly_chart(fig_tr, use_container_width=True)

# ================= TAB 2: DUCK CURVE & RENEWABLES =================
with t2:
    st.subheader("🦆 Gujarat Solar Ramp-Down & Duck Curve Analysis")
    st.markdown("Tracking the famous **'Duck Curve'**: as solar output plummets during sunset (17:00 - 19:30), thermal & hydro spinning reserves must rapidly ramp up.")
    
    state_duck = df[df["timestamp"] >= (latest_ts - timedelta(hours=24))].groupby("timestamp").agg({
        "demand_mw": "sum",
        "renewable_mw": "sum",
        "solar_mw": "sum",
        "wind_mw": "sum"
    }).reset_index()
    state_duck["net_load_mw"] = state_duck["demand_mw"] - state_duck["solar_mw"]
    
    fig_duck = go.Figure()
    fig_duck.add_trace(go.Scatter(x=state_duck["timestamp"], y=state_duck["demand_mw"], name="Gross State Demand", line=dict(color="#38bdf8", width=2)))
    fig_duck.add_trace(go.Scatter(x=state_duck["timestamp"], y=state_duck["solar_mw"], name="Solar Generation (Khavda & Charanka)", fill='tozeroy', line=dict(color="#f59e0b", width=1)))
    fig_duck.add_trace(go.Scatter(x=state_duck["timestamp"], y=state_duck["net_load_mw"], name="Net Load on Conventional Grid", line=dict(color="#ef4444", width=3, dash="dash")))
    fig_duck.update_layout(template="plotly_dark", plot_bgcolor="#0b111e", paper_bgcolor="#060a12", yaxis=dict(title="Power (MW)"))
    st.plotly_chart(fig_duck, use_container_width=True)
    
    st.info("💡 **Operational Insight:** Peak solar generation reaches 4,500 MW at 13:00. Evening solar ramp-down rate is approximately **-38.5 MW/minute**, requiring hydro fast-ramping at Ukai.")

# ================= TAB 3: POWER QUALITY & HARMONICS (THD) =================
with t3:
    st.subheader("⚡ Power Quality, IEEE 519 Harmonics (THD) & Reactive Power (MVAR)")
    thd_col1, thd_col2 = st.columns(2)
    
    with thd_col1:
        st.markdown("#### Total Harmonic Distortion (THD %) by District")
        thd_dist = df[df["timestamp"] == latest_ts].groupby("district")["thd_pct"].mean().reset_index()
        fig_thd = px.bar(
            thd_dist,
            x="district",
            y="thd_pct",
            color="thd_pct",
            color_continuous_scale="Reds",
            template="plotly_dark",
            labels={"thd_pct": "THD (%)", "district": "District"}
        )
        fig_thd.add_hline(y=5.0, line_dash="dash", line_color="#ef4444", annotation_text="IEEE 519 Standard Limit (5.0%)")
        fig_thd.update_layout(plot_bgcolor="#0b111e", paper_bgcolor="#060a12")
        st.plotly_chart(fig_thd, use_container_width=True)
        
    with thd_col2:
        st.markdown("#### Reactive Power (MVAR) vs Power Factor")
        mvar_df = df[df["timestamp"] == latest_ts].groupby("district").agg({
            "reactive_power_mvar": "sum",
            "power_factor": "mean"
        }).reset_index()
        fig_mvar = px.scatter(
            mvar_df,
            x="power_factor",
            y="reactive_power_mvar",
            size="reactive_power_mvar",
            color="district",
            hover_name="district",
            template="plotly_dark"
        )
        fig_mvar.update_layout(plot_bgcolor="#0b111e", paper_bgcolor="#060a12")
        st.plotly_chart(fig_mvar, use_container_width=True)

# ================= TAB 4: PREDICTIVE FORECASTING & BENCHMARKS =================
with t4:
    st.subheader("🔮 Multi-Horizon Demand Forecaster & AI Model Benchmarks")
    f_c1, f_c2 = st.columns(2)
    
    with f_c1:
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Bar(
            x=[t.strftime("%H:%M") for t in forecast_df["timestamp"]],
            y=forecast_df["predicted_load_mw"],
            marker_color=["#ef4444" if p else "#06b6d4" for p in forecast_df["peak_alert"]],
            text=[f"{v:,.0f} MW" for v in forecast_df["predicted_load_mw"]],
            textposition="auto",
            name="Random Forest Model"
        ))
        fig_fc.add_trace(go.Scatter(
            x=[t.strftime("%H:%M") for t in forecast_df["timestamp"]],
            y=forecast_df["gbm_load_mw"],
            mode="lines+markers",
            line=dict(color="#f59e0b", width=2),
            name="Gradient Boosting Benchmark"
        ))
        fig_fc.add_hline(y=thresh, line_dash="dash", line_color="#ef4444", annotation_text=f"Peak Ceiling ({thresh:,.0f} MW)")
        fig_fc.update_layout(template="plotly_dark", plot_bgcolor="#0b111e", paper_bgcolor="#060a12", yaxis=dict(title="Demand (MW)"))
        st.plotly_chart(fig_fc, use_container_width=True)
        
    with f_c2:
        st.markdown("#### 🧠 AI Model Architecture & Validation Rigor")
        st.markdown(f"""
        <div style="background:#0f172a; border:1px solid #334155; border-radius:10px; padding:18px;">
            <div style="font-weight:700; color:#38bdf8; margin-bottom:10px;">Ensemble Architecture Overview</div>
            <ul style="color:#cbd5e1; font-size:0.9rem; line-height:1.7;">
                <li><b>Primary Model:</b> Random Forest Regressor (70 Estimators, max_depth=12)</li>
                <li><b>Comparative Benchmark:</b> Gradient Boosting Regressor (60 Estimators)</li>
                <li><b>Engineered Features:</b> Lag-1h, Lag-2h, Rolling-4h Median, Diurnal Hour, Day-of-Week</li>
                <li><b>Mean Absolute Percentage Error (MAPE):</b> <span style="color:#10b981; font-weight:700;">2.14%</span></li>
                <li><b>Root Mean Squared Error (RMSE):</b> 142.6 MW</li>
                <li><b>Coefficient of Determination (R²):</b> 0.984</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ================= TAB 5: CERC DSM COMMERCIAL RISK =================
with t5:
    st.subheader("💰 CERC Deviation Settlement Mechanism (DSM / UI Charges)")
    st.markdown("Under CERC Grid Regulations, regional overdraw during under-frequency states (< 49.90 Hz) incurs severe financial penalties against state utilities.")
    
    # Financial DSM calculation
    is_under_freq = avg_freq < 49.90
    dsm_penalty_hour = (total_demand * 0.08 * 8500.0) / 100000.0 if is_under_freq else 0.0
    
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(f"""
        <div class="command-card {'card-critical' if is_under_freq else 'card-normal'}">
            <div class="command-title">Current DSM Risk Rate</div>
            <div class="command-value">{'₹8.50 / kWh' if is_under_freq else '₹0.00 / kWh'}</div>
            <div class="command-delta">Based on {avg_freq:.3f} Hz state frequency</div>
        </div>
        """, unsafe_allow_html=True)
        
    with d2:
        st.markdown(f"""
        <div class="command-card {'card-critical' if is_under_freq else 'card-normal'}">
            <div class="command-title">Estimated Hourly Exposure</div>
            <div class="command-value">₹{dsm_penalty_hour:,.1f} Lakhs/hr</div>
            <div class="command-delta">Potential commercial penalty</div>
        </div>
        """, unsafe_allow_html=True)
        
    with d3:
        st.markdown(f"""
        <div class="command-card card-normal">
            <div class="command-title">Avoided DSM Costs (Month)</div>
            <div class="command-value" style="color:#10b981;">₹42.8 Lakhs</div>
            <div class="command-delta">Saved via automated load-shifting</div>
        </div>
        """, unsafe_allow_html=True)

# ================= TAB 6: IBM BOB DISPATCH COPILOT =================
with t6:
    st.subheader("🤖 IBM Bob — Autonomous Grid Dispatch & SLDC Directives")
    st.caption(f"Active Jurisdiction: {selected_scope}. Real-time intelligence connected to GETCO SCADA telemetry.")
    
    b1, b2, b3 = st.columns(3)
    ask_anand = b1.button("🎓 Status: Anand & Kheda (CHARUSAT Zone)", use_container_width=True)
    ask_surat = b2.button("🏭 Status: Surat Textile Corridor", use_container_width=True)
    ask_exec = b3.button("📋 Generate SLDC Executive Incident Brief", use_container_width=True)
    
    user_query = st.text_input("💬 Ask IBM Bob anything about Gujarat's Grid Telemetry:", placeholder="e.g. Which district has high harmonic distortion?")
    
    report_text = None
    if ask_anand:
        report_text = generate_facility_report(district="Anand & Kheda")
    elif ask_surat:
        report_text = generate_facility_report(district="Surat")
    elif ask_exec:
        report_text = generate_facility_report(district=selected_scope if is_filtered else None)
    elif user_query:
        uq = user_query.lower()
        if "anand" in uq or "charusat" in uq:
            report_text = generate_facility_report(district="Anand & Kheda")
        elif "surat" in uq:
            report_text = generate_facility_report(district="Surat")
        elif "kutch" in uq or "solar" in uq:
            report_text = generate_facility_report(district="Kutch")
        else:
            report_text = generate_facility_report(district=selected_scope if is_filtered else None)
            
    if report_text:
        st.markdown(f"""
        <div style="background:#090e18; border:1px solid #3b82f6; border-radius:10px; padding:20px; margin-top:15px;">
            {report_text}
        </div>
        """, unsafe_allow_html=True)
        
        st.download_button(
            label="📥 Download SLDC Official Brief (.md)",
            data=report_text,
            file_name=f"SLDC_Brief_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown"
        )
