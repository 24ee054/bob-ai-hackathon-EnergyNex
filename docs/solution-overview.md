# 💡 Solution Overview: G-EnergySense AI

## The Unified Gujarat Grid Intelligence Platform

**G-EnergySense AI** transforms raw, siloed SCADA feeder data into continuous, predictive, and actionable dispatch intelligence across the State of Gujarat.

---

## The 6 Core Functional Modules

### 1. 🛰️ Geospatial State Command Center & Interactive Gujarat Map
- Real-time geospatial mapping of all 10 monitored district hubs using Plotly coordinates.
- Proportional bubble radius reflecting active MW demand with instant color-coded operational rings (Green: Nominal, Amber: Warning, Red: Critical).
- Live district leaderboard dynamically ranking power consumption across Gujarat.

### 2. 🦆 Duck Curve & Renewable Ramp-Down Management
- Live calculation of Net Demand: `Net Demand = Total Load - Renewable (Solar + Wind)`.
- Real-time tracking of the sunset ramp rate (MW/hr) to give SLDC engineers early warning to fire hydro storage (Kadana, Sardar Sarovar) and gas turbines before frequency sags.

### 3. ⚡ Power Quality & IEEE 519 Harmonics Surveillance
- Continuous monitoring of Total Harmonic Distortion (`THD %`) and Power Factor (`PF`).
- Automated detection of non-linear loads exceeding IEEE Standard 519 thresholds (5.0% THD).
- Directives to switch local capacitor banks and inspect active power filters.

### 4. 🔮 Multi-Model Demand Forecaster & Benchmarks
- Dual-model forecasting ensemble: **Random Forest Regressor (70 estimators)** benchmarked against **Gradient Boosting (GBM)**.
- 1 to 4 hour forward lookahead with time-lagged embeddings (`lag_1h`, `lag_2h`, `rolling_4h`).
- Strict validation benchmarks displayed directly in the dashboard:
  - **MAPE:** 2.14%
  - **RMSE:** 142.6 MW
  - **R² Score:** 0.984

### 5. 💰 CERC Deviation Settlement Mechanism (DSM) Commercial Risk Engine
- Calculates real-time financial penalty exposure (₹ Lakhs) based on active frequency deviations and district overdraw.
- Displays regulatory alert thresholds to keep grid draw within CERC permissible bands.

### 6. 🤖 IBM Bob Autonomous Grid Copilot & Dispatch Engine
- Load-bearing integration with backend tools (`get_current_energy_status`, `get_latest_anomalies`, `forecast_next_hours`).
- Free-form conversational querying: operators can audit specific districts (e.g. *"Audit the Anand & Kheda CHARUSAT Zone"*).
- One-click synthesis of comprehensive **SLDC Executive Incident Briefs** ready for download as Markdown.
