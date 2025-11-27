# Vehicle Data Analysis Dashboard

Interactive dashboard to analyze vehicle telemetry data.

## Features
- **Speed vs RPM**: Analyze gear efficiency.
- **Throttle vs RPM**: Study acceleration behavior.
- **Engine Load**: Monitor engine stress.
- **Fuel Efficiency**: Calculate mileage (km/L).

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the dashboard:
   ```bash
   streamlit run dashboard.py
   ```

## Data Generation
Run `python generate_vehicle_data.py` to generate new random data for 15 weeks.

## Deployment
**Recommended:** Deploy on [Streamlit Community Cloud](https://streamlit.io/cloud).
1. Sign up/Login to Streamlit Cloud.
2. Connect your GitHub account.
3. Select this repository (`shivanshu407/car-analysis`).
4. Set the "Main file path" to `dashboard.py`.
5. Click **Deploy**.

*Note: Vercel is not recommended for Streamlit apps as they require a persistent WebSocket connection, which Vercel's serverless architecture does not support natively.*
