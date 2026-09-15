# EnergyNex — Grid Load Optimisation & Renewable Energy Advisor

> **IBM Bob AI Innovation Hackathon Project (Challenge U2 & Master Challenge)**  
> *Tagline: Clean Energy Optimisation & Real-Time Grid Load Intelligence.*

**EnergyNex** (powered by the **GridOpt AI** decision engine) is a production-quality AI decision support platform for facility managers and utility grid operators. It unifies smart energy telemetry monitoring with real-time grid load forecasting, renewable performance anomaly detection, root cause SHAP attribution, load-balancing work orders, and integrated operator optimisation briefs.

$$\text{DEMAND DATA} \rightarrow \text{AI FORECAST} \rightarrow \text{DEMAND SPIKE} \rightarrow \text{GRID RISK} \rightarrow \text{LOAD BALANCING} \rightarrow \text{RENEWABLE ANOMALY} \rightarrow \text{ROOT CAUSE} \rightarrow \text{CURTAILMENT PLAN} \rightarrow \text{AI BRIEF}$$

---

## ⚡ Key Features (Challenge U2)

1. **Operations Overview & KPI Dashboard**
   - Live SCADA telemetry tracking Current Load (`8.42 GW`), Forecast Peak (`10.15 GW` ⚠ `+20.5%`), Renewable Output (`5.87 GW`), Curtailment (`420 MW`), Renewable Utilisation (`91.4%`), Active Anomalies (`3`), and Grid Stress (`HIGH`).

2. **Random Forest Demand Forecasting**
   - Predicts 24-hour grid load curves and triggers automated demand spike risk alerts at peak hours (e.g. `10.15 GW` at `18:00 UTC`, `+16.0%` surge).

3. **AI Load-Balancing Recommendation Engine**
   - Recommends actionable load shifts: `Shift 350 MW Flexible Industrial Load`, `Reduce 120 MW EV Charging`, and `Dispatch Unconstrained Clean Energy`.

4. **Renewable Performance & Isolation Forest Anomaly Detection**
   - Monitors Solar & Wind farms (Solar Farm A, Solar Farm B, Solar Farm C, Wind Farm A, Wind Farm B, Wind Farm C).
   - Flagged Anomaly: `Solar Farm A` (Actual: `94 MW` vs Expected: `120 MW`, **-21.7% Deviation** -> 🔴 `UNDERPERFORMING`).

5. **Explainable AI Root Cause Analysis Engine**
   - Feature attribution breakdown per asset: `Low Solar Irradiance` (52%), `High Ambient Temp` (23%), `Inverter Degradation` (18%), `Panel Soiling` (7%).

6. **Renewable Curtailment Minimisation Plan**
   - Strategy absorbing `300 MW` clean energy into flexible industrial demand, lowering curtailment from `420 MW` to `120 MW` (**71.4% Curtailment Reduction**).

7. **Interactive Optimisation Scenario Simulator**
   - Real state-changing simulation toggle ("Before" vs "After AI Actions").

8. **Integrated AI Operator Optimisation Brief Generator**
   - Dynamic report generator combining forecast, underperforming assets, root causes, load balancing actions, and curtailment plan into a single operational brief.

9. **IBM Bob AI Copilot**
   - Data-aware natural language operator copilot capable of answering queries regarding demand surges, solar underperformance, root causes, curtailment plans, and operator briefs (`http://localhost:3000/copilot`).

10. **Executive & Weekly Grid Reliability Reports**
    - Comprehensive Daily, Weekly, Monthly, and Yearly regulatory reporting engine with SAIDI/SAIFI indexes and downloadable Markdown briefs.

---

## 🛠️ Technology Stack & Architecture

* **Frontend UI:** React 18, Vite 5, TypeScript, Tailwind CSS, Recharts, Lucide Icons (`http://localhost:3000`)
* **Backend API:** Python FastAPI, Uvicorn (`http://localhost:8000`)
* **AI & Data Pipeline:** Scikit-Learn (`RandomForestRegressor`, `IsolationForest`), Pandas, NumPy

---

## 🚀 How to Run

### 1. Run Python FastAPI Backend & AI Pipeline
```powershell
$env:PYTHONPATH="."; uvicorn src.ai.backend:app --host 0.0.0.0 --port 8000
```

### 2. Run React Vite Operator Control Center
```powershell
npm run dev
```

Open **`http://localhost:3000`** in your browser.
