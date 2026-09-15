# ⚡ G-EnergySense AI — Gujarat State & District Energy Intelligence Center

> **Real-Time State & District Grid Telemetry • AI Regional Anomaly Engine • Multi-Hour Demand Forecasting**  
> *Developed for the IBM Bob AI Innovation Hackathon 2026*

---

## 🏛️ Executive Summary
The **Gujarat State Energy Intelligence Center (G-EnergySense AI)** is an AI-powered operational command platform designed for the **Gujarat State Load Despatch Centre (SLDC, Gotri, Vadodara)**, **GETCO**, and the state's power distribution zones (**DISCOMs**).

It monitors the electrical grid from the state level down to **10 major Gujarat Districts & Cities**:
- **Ahmedabad Metro** (UGVCL — Urban Commercial & Industrial)
- **Surat Industrial Corridor** (DGVCL — Textile & Diamond Industrial Hub)
- **Vadodara Engineering Hub** (MGVCL — Chemical & Heavy Engineering)
- **Rajkot Foundry & Auto Hub** (PGVCL — Automotive Casting)
- **Anand & Kheda / CHARUSAT Zone** (MGVCL — Dairy, Agro & University Campus)
- **Gandhinagar & GIFT City** (UGVCL — Fintech, IT Parks & Data Centers)
- **Kutch & Mundra Port Hub** (PGVCL — Khavda Mega Solar/Wind & Port)
- **Bharuch & Ankleshwar PCPIR** (DGVCL — Petrochemical & Bulk Drugs)
- **Jamnagar Petroleum Complex** (PGVCL — Refining & Brass)
- **Bhavnagar Ship & Marine Hub** (PGVCL — Marine Logistics & Rolling Mills)

---

## 🎯 Key Capabilities
1. **LIVE TELEMETRY:** Real-time state load (~18,000 MW to ~24,000 MW), live grid frequency (50.00 Hz), and renewable mix (Solar + Wind).
2. **DISTRICT LEADERBOARD:** Live interactive bar chart ranking all 10 Gujarat districts by current power draw.
3. **RECENT 24-HOUR PROFILES:** Interactive Plotly multi-line curves comparing districts with red anomaly markers.
4. **AI ANOMALY DETECTION:** Isolation Forest flagging localized feeder surges and grid frequency dips.
5. **PREDICTIVE DEMAND FORECASTER:** Multi-hour load forecasting (1 to 4 hours) with peak threshold alerts (22,500 MW ceiling).
6. **IBM BOB GRID COPILOT:** Instant district audits (e.g., Anand / CHARUSAT zone, Surat industrial corridor) and SLDC Executive Brief generation.

---

## 🚀 Quick Start

```bash
cd "C:\Users\ranak\Desktop\CHARUSAT\SEM 5\IBM_BOB_HACKATHON"
pip install -r requirements.txt
streamlit run src/app.py
```
