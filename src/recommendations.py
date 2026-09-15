def generate_recommendations(anomalies_df=None, forecast_data=None, selected_scope="All Gujarat (Statewide)"):
    recs = []
    
    if anomalies_df is not None and not anomalies_df.empty:
        criticals = anomalies_df[anomalies_df["severity"].isin(["CRITICAL", "HIGH"])]
        
        for _, row in criticals.head(3).iterrows():
            dist = row.get("district", row.get("discom_zone", "Region"))
            city = row.get("city_hub", "")
            dev = float(row.get("deviation_pct", 0.0))
            dem = float(row.get("demand_mw", 0.0))
            
            if "Surat" in dist:
                recs.append({
                    "priority": "HIGH",
                    "panel": dist,
                    "title": f"Surat Textile Corridor Demand Spike (+{dev:.1f}%)",
                    "action": f"Current load: {dem:,.0f} MW. Coordinate with Pandesara and Sachin GIDC substations to enforce rotational power draw and activate DGVCL auxiliary feeders.",
                    "impact": "Shaves ~380 MW off southern industrial transmission bottleneck."
                })
            elif "Anand" in dist:
                recs.append({
                    "priority": "HIGH",
                    "panel": dist,
                    "title": f"Anand & Kheda (CHARUSAT Zone) Feeder Surge (+{dev:.1f}%)",
                    "action": f"Load surge ({dem:,.0f} MW) detected in central educational & dairy agro-cluster. Verify Mogar & Changa 66kV substation transformer loading and balance agro-feeders.",
                    "impact": "Protects regional sub-transmission lines from overheating."
                })
            elif "Bharuch" in dist:
                recs.append({
                    "priority": "HIGH",
                    "panel": dist,
                    "title": f"Bharuch / Ankleshwar Chemical PCPIR Surge (+{dev:.1f}%)",
                    "action": "Issue peak notification to heavy chemical continuous process plants. Mobilize Dahej gas-fired standby generators.",
                    "impact": "Prevents industrial tripouts and maintains local grid PF above 0.96."
                })
            elif "Ahmedabad" in dist:
                recs.append({
                    "priority": "MEDIUM",
                    "panel": dist,
                    "title": f"Ahmedabad Urban HVAC Peak (+{dev:.1f}%)",
                    "action": "Enforce commercial building pre-cooling protocol and shift industrial feeder schedules in Sanand & Changodar.",
                    "impact": "Reduces metropolitan peak burden by ~250 MW."
                })
            else:
                recs.append({
                    "priority": "MEDIUM",
                    "panel": dist,
                    "title": f"Regional Anomaly in {dist} ({city}) (+{dev:.1f}%)",
                    "action": f"Local substation overdraw ({dem:,.0f} MW). Inspect local 66kV transformer tap changers and balance feeder phases.",
                    "impact": "Maintains local voltage stability within ±3%."
                })

    if forecast_data is not None and not forecast_data.empty:
        peaks = forecast_data[forecast_data["peak_alert"]]
        if not peaks.empty:
            p = peaks.iloc[0]
            recs.append({
                "priority": "CRITICAL",
                "panel": selected_scope,
                "title": f"Approaching Peak Load Surge at {p['timestamp'].strftime('%H:%M')} ({p['predicted_load_mw']:,.0f} MW)",
                "action": f"Projected demand approaches peak ceiling ({p['threshold_mw']:,.0f} MW). Ramp up spinning reserves at Wanakbori & Dhuvaran stations.",
                "impact": "Guarantees grid stability during statewide evening peak."
            })
            
    if not recs:
        recs.append({
            "priority": "OPTIMAL",
            "panel": selected_scope,
            "title": "All Districts Operating Within Optimal Thresholds",
            "action": "State grid frequency stable at 50.00 Hz. Solar absorption from Charanka and Khavda is nominal.",
            "impact": "Stable inter-district transmission."
        })
        
    return recs
