import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import glob

# Page Config
st.set_page_config(page_title="Vehicle Data Analysis", layout="wide")

# Title
st.title("🚗 Vehicle Data Analysis Dashboard")
st.markdown("Analysis of 15 weeks of driving data based on 7 key parameters.")

# Data Loading
@st.cache_data
def load_data():
    all_files = glob.glob(os.path.join("data", "*.csv"))
    df_list = []
    for filename in all_files:
        df = pd.read_csv(filename)
        week_name = os.path.basename(filename).replace(".csv", "").replace("_", " ").title()
        df['Week'] = week_name
        df_list.append(df)
    
    if not df_list:
        return pd.DataFrame()
        
    return pd.concat(df_list, ignore_index=True)

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if df.empty:
    st.warning("No data found in 'data' folder. Please run the generation script first.")
    st.stop()

# Sidebar
st.sidebar.header("Filter Data")
week_options = ["All Weeks"] + sorted(df['Week'].unique().tolist(), key=lambda x: int(x.split()[-1]))
selected_week = st.sidebar.selectbox("Select Week", week_options)

if selected_week != "All Weeks":
    filtered_df = df[df['Week'] == selected_week]
else:
    filtered_df = df

# Metrics
st.sidebar.subheader("Quick Stats")
total_distance_km = filtered_df['Trip_Distance_m'].max() / 1000
st.sidebar.metric("Total Distance", f"{total_distance_km:.2f} km")
st.sidebar.metric("Max Speed", f"{filtered_df['OBD Speed'].max()} km/h")
st.sidebar.metric("Avg RPM", f"{int(filtered_df['RPM'].mean())}")

# --- Fuel Consumption Calculation ---
# Estimation based on MAF (Mass Air Flow)
# MAF (g/s) = (Displacement (L) * RPM / 120) * AirDensity (kg/m3) * VolumetricEff * (Load/100)
# Fuel (g/s) = MAF / AFR (14.7)
# Fuel (L/h) = (Fuel (g/s) / FuelDensity (0.74 kg/L)) * 3600

DISPLACEMENT = 1.6 # Liters
AIR_DENSITY = 1.225
VOL_EFF = 0.85
AFR = 14.7
FUEL_DENSITY = 0.74

def calculate_fuel(row):
    rpm = row['RPM']
    load = row['Engine_Load']
    
    maf = (DISPLACEMENT * rpm / 120) * AIR_DENSITY * VOL_EFF * (load / 100)
    fuel_g_s = maf / AFR
    fuel_l_h = (fuel_g_s / (FUEL_DENSITY * 1000)) * 3600
    return fuel_l_h

filtered_df['Fuel_Flow_L_h'] = filtered_df.apply(calculate_fuel, axis=1)

# Avoid division by zero for Mileage
filtered_df['Mileage_km_L'] = filtered_df.apply(
    lambda x: x['OBD Speed'] / x['Fuel_Flow_L_h'] if x['Fuel_Flow_L_h'] > 0 and x['OBD Speed'] > 1 else 0, 
    axis=1
)

# Calculate Average Mileage for the selected period
total_fuel_consumed = (filtered_df['Fuel_Flow_L_h'] * 1/3600).sum() # L/h * h (1s steps)
if total_fuel_consumed > 0:
    avg_mileage = total_distance_km / total_fuel_consumed
else:
    avg_mileage = 0

st.sidebar.metric("Avg Mileage", f"{avg_mileage:.2f} km/L")
st.sidebar.metric("Total Fuel", f"{total_fuel_consumed:.2f} L")

# --- Analysis Sections ---

# 0. Mileage Analysis
st.header("0️⃣ Fuel Efficiency Analysis")
st.markdown(f"**Average Mileage:** {avg_mileage:.2f} km/L")
fig0 = px.scatter(filtered_df[filtered_df['Mileage_km_L'] < 50], x="OBD Speed", y="Mileage_km_L", 
                  color="Gear", title="Instant Mileage (km/L) vs Speed")
st.plotly_chart(fig0, use_container_width=True)


# 1. Speed vs RPM
st.header("1️⃣ Speed vs RPM")
st.markdown("**Purpose:** Check gear efficiency. Linear lines indicate gears.")
fig1 = px.scatter(filtered_df, x="OBD Speed", y="RPM", color="Gear", 
                  title="Speed vs RPM (Colored by Gear)", opacity=0.5)
st.plotly_chart(fig1, use_container_width=True)

# 2. Throttle Position vs RPM
st.header("2️⃣ Throttle Position vs RPM")
st.markdown("**Purpose:** Study acceleration behavior. High throttle at low RPM can indicate lugging.")
fig2 = px.density_heatmap(filtered_df, x="RPM", y="Throttle_Position", 
                          title="Throttle Position vs RPM Density", nbinsx=30, nbinsy=30)
st.plotly_chart(fig2, use_container_width=True)

# 3. Engine Load vs Speed
st.header("3️⃣ Engine Load vs Speed")
st.markdown("**Purpose:** Analyze engine stress. High load at low speed is stressful.")
fig3 = px.scatter(filtered_df, x="OBD Speed", y="Engine_Load", color="Gear",
                  title="Engine Load vs Speed", opacity=0.5)
st.plotly_chart(fig3, use_container_width=True)

# 4. Idle Time vs RPM
st.header("4️⃣ Idle Time vs RPM")
st.markdown("**Purpose:** Detect unnecessary idling.")
idle_df = filtered_df[filtered_df['OBD Speed'] < 1]
fig4 = px.histogram(idle_df, x="RPM", title="RPM Distribution during Idle (Speed < 1 km/h)")
st.plotly_chart(fig4, use_container_width=True)

# 5. Catalyst Temperature vs Speed
st.header("5️⃣ Catalyst Temperature vs Speed")
st.markdown("**Purpose:** Monitor emission system performance.")
fig5 = px.scatter(filtered_df, x="OBD Speed", y="Catalyst_Temperature", 
                  title="Catalyst Temperature vs Speed", color="Engine_Load")
st.plotly_chart(fig5, use_container_width=True)

# 6. Intake Air Temperature vs RPM
st.header("6️⃣ Intake Air Temperature vs RPM")
st.markdown("**Purpose:** Shows air–fuel efficiency context.")
fig6 = px.scatter(filtered_df, x="RPM", y="Intake_Air_Temp", 
                  title="Intake Air Temperature vs RPM", opacity=0.5)
st.plotly_chart(fig6, use_container_width=True)

# 7. Vehicle Speed vs Distance/Trip Time
st.header("7️⃣ Vehicle Speed vs Distance/Trip Time")
st.markdown("**Purpose:** Shows driving consistency and trip profile.")
# For this plot, if "All Weeks" is selected, it might be too messy, so we limit or aggregate
if selected_week == "All Weeks":
    st.info("Select a specific week to see detailed time-series data.")
    # Show a sample or aggregate
    daily_avg = df.groupby('Week')['OBD Speed'].mean().reset_index()
    fig7 = px.bar(daily_avg, x='Week', y='OBD Speed', title="Average Speed per Week")
else:
    fig7 = px.line(filtered_df, x="Time_1s", y="OBD Speed", title=f"Speed Profile - {selected_week}")
st.plotly_chart(fig7, use_container_width=True)

st.success("Dashboard Loaded Successfully!")
