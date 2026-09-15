# ⚡ G-EnergySense AI — Gujarat State & District Energy Intelligence Center

> **Real-Time State & District Grid Telemetry • AI Alert Engine • Multi-Hour Demand Forecasting**  
> *Developed for the IBM Bob AI Innovation Hackathon 2026*

---

## 🚀 1-Click Quick Run

To start the application, simply run:

```bash
python run.py
```
*(On Windows, you can also just double-click **`start.bat`**)*

This will automatically:
1. Verify the database and telemetry records.
2. Start the local server on `http://127.0.0.1:8000/`.
3. **Automatically open the dashboard in your web browser!**

---

## 🎤 2-Minute Hackathon Demo Script (What to Show Judges)

| Step | Time | What to Click / Show | What to Say |
|---|---|---|---|
| **1. The Problem** | 30s | Show the Top 4 Metric Cards | *"Gujarat's electrical grid handles ~20,000 MW every single day. Balancing solar power with massive industrial demand across districts like Surat and Ahmedabad is a critical challenge."* |
| **2. District Map & Rankings** | 30s | Click on the Gujarat Map markers (e.g. Anand / CHARUSAT, Surat, Vadodara) | *"Here is our live SCADA map and district leaderboard. We track all 10 major hubs in real time, from dairy & education in Anand to heavy industry in Surat."* |
| **3. AI Alert Engine** | 30s | Point to the Active Alerts & Recommendations card | *"Our AI automatically flags abnormal power surges before transformers blow out and provides instant dispatch recommendations."* |
| **4. IBM Bob Copilot** | 30s | Click the button `📍 Check Anand & CHARUSAT Zone` or `📋 Generate 1-Minute Executive Summary` | *"Operators can talk to IBM Bob AI Copilot in plain English to audit any district or export a clean executive incident brief in 1 click."* |

---

## 🎯 What Does G-EnergySense AI Do?

1. **⚡ Live State Telemetry:** Shows total power demand (~18,000 to ~22,000 MW), clean solar/wind share, and grid stability (50.00 Hz).
2. **🗺️ 10-District Gujarat Map:** Interactive geographic map showing power draw in Ahmedabad, Surat, Vadodara, Rajkot, Anand (CHARUSAT Zone), Gandhinagar (GIFT City), Kutch, Bharuch, Jamnagar, and Bhavnagar.
3. **🏆 District Leaderboard:** Real-time ranking of which districts are consuming the most power.
4. **🔮 4-Hour Demand Forecaster:** Predicts electricity consumption for the next 4 hours to help prevent blackouts.
5. **🚨 Smart Alerts & Recommendations:** Flags surges and suggests corrective actions in plain English.
6. **🤖 IBM Bob AI Assistant:** Chatbot that answers questions about Gujarat's power grid and generates downloadable summary briefs.

---

## 🧪 Automated Testing

Run the automated test suite anytime:
```bash
python manage.py test
```

---

## 🏛️ Regional Grid Coverage (10 Monitored Hubs)
- **Ahmedabad Metro** (Commercial & Metro Load)
- **Surat Industrial** (Textile & Diamond Power Hub)
- **Vadodara Engineering** (Chemical & Engineering Hub)
- **Rajkot Auto Hub** (Automotive & Foundry)
- **Anand & Kheda** (CHARUSAT University Zone, Agro & Dairy)
- **Gandhinagar & GIFT City** (Fintech & Data Centers)
- **Kutch & Mundra** (Khavda Mega Solar/Wind & Port)
- **Bharuch & Ankleshwar** (Petrochemicals)
- **Jamnagar Petroleum** (Refineries)
- **Bhavnagar Ship & Marine** (Marine Logistics & Rolling Mills)
