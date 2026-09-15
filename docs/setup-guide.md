# Setup & Execution Guide

1. Clone or open the repository.
2. Install requirements: `pip install -r requirements.txt`.
3. Verify test runs:
   - Generate data: `python src/data/generate_gujarat_data.py`
   - Test anomalies: `python src/anomaly.py`
   - Test forecast: `python src/forecasting.py`
   - Test Bob tools: `python src/bob_tools.py`
4. Launch the dashboard: `streamlit run src/app.py`.
