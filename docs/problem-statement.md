# 🎯 Problem Statement: Gujarat Grid Load Management & District Feeder Stability

## 1. Background & Operational Scale
The State of Gujarat has one of India's largest and most technologically intricate electrical power grids. Under the administrative supervision of the **Gujarat Energy Transmission Corporation Limited (GETCO)** and the operational oversight of the **Gujarat State Load Despatch Centre (SLDC, Gotri, Vadodara)**, the grid manages:
- **Peak State Demand:** In excess of 21,500 MW - 24,000 MW during peak summer and agricultural seasons.
- **Geographic Span:** 33 administrative districts serviced by 4 regional state power distribution companies (**DISCOMs**):
  - **UGVCL (Uttar Gujarat Vij Company Ltd):** North Gujarat agriculture, Ahmedabad peri-urban, and Gandhinagar GIFT City.
  - **DGVCL (Dakshin Gujarat Vij Company Ltd):** The intense industrial corridor of Surat, Bharuch, Dahej, and Ankleshwar PCPIR.
  - **MGVCL (Madhya Gujarat Vij Company Ltd):** Vadodara engineering & chemicals, Anand & Kheda agricultural and dairy processing (Amul) zone.
  - **PGVCL (Paschim Gujarat Vij Company Ltd):** Saurashtra auto foundries (Rajkot), Jamnagar petroleum refining, Bhavnagar marine rolling mills, and Kutch mega-port infrastructure.
- **Renewable Energy Integration:** Gujarat is India's leading renewable hub, hosting the **Charanka Solar Park (790+ MW)** and the world's largest **Khavda Renewable Energy Park (30+ GW planned)** in Kutch.

---

## 2. Core Operational Challenges

### Challenge 1: The "Duck Curve" & Evening Solar Ramp-Down
During daytime hours (09:00 - 16:00), solar generation injects up to 6,500+ MW into the transmission network, depressing conventional thermal baseload demand. However, between 17:30 and 19:30, as solar radiance drops to zero just as domestic and commercial lighting peaks, the grid experiences a steep ramp-up rate exceeding **1,200 MW per hour**. SLDC operators struggle to manually balance spinning reserves in real time.

### Challenge 2: Unannounced Industrial Feeder Surges & Power Quality Breaches
In heavy industrial districts like Surat (textiles/diamonds) and Bharuch (chemicals/petroleum), synchronized switching of induction furnaces, arc melters, and non-linear drives introduces severe harmonic distortion (**IEEE 519 Total Harmonic Distortion > 5%**) and active load surges exceeding +35% above expected seasonal baselines.

### Challenge 3: CERC Deviation Settlement Mechanism (DSM) Financial Penalties
Under Central Electricity Regulatory Commission (CERC) DSM regulations, overdrawing from the National Grid when grid frequency drops below 49.90 Hz attracts punitive penalty tariffs reaching up to ₹12.50 per kWh. A 200 MW unpredicted deviation can cost DISCOMs millions of rupees within a single 15-minute time block.

### Challenge 4: Operational Data Silos & Slow Dispatch Decisions
Existing SCADA systems display thousands of isolated telemetry readings without contextual intelligence. When a frequency dip occurs, grid engineers must manually cross-reference 66kV feeder logs, identify which district is overdrawing, and telephone local substations, wasting critical minutes.

---

## 3. The Objective of G-EnergySense AI
To bridge this gap by delivering an **autonomous, end-to-end operational intelligence copilot** that:
1. Aggregates multi-district telemetry into an intuitive, real-time command cockpit.
2. Identifies anomalous feeder spikes instantly with automated physical root-cause attribution.
3. Predicts upcoming 1 to 4 hour state and district peak ceiling breaches using machine learning.
4. Generates automated, actionable SLDC dispatch directives.
5. Provides an interactive conversational AI interface via **IBM Bob Copilot** for instant executive briefs and feeder health audits.
