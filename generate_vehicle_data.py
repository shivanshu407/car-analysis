import pandas as pd
import numpy as np
import os
import random
from datetime import datetime, timedelta

# Configuration
OUTPUT_FOLDER = 'data'
NUM_WEEKS = 15
DATA_POINTS_PER_WEEK = 3600 * 2  # 2 hours of data per week (1 point per second)
START_DATE = datetime(2024, 1, 1, 8, 0, 0)

# Constants for Physics Simulation
IDLE_RPM = 800
MAX_RPM = 7000
GEAR_RATIOS = [3.5, 2.0, 1.4, 1.0, 0.8, 0.6]  # 1st to 6th
FINAL_DRIVE = 3.5
TIRE_RADIUS = 0.3  # meters
MIN_SPEED_FOR_GEAR = [0, 15, 30, 50, 70, 90]  # km/h

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def simulate_trip(duration_seconds, scenario='mixed'):
    """
    Simulates a driving trip.
    scenario: 'city', 'highway', 'mixed', 'aggressive', 'inefficient'
    """
    data = []
    
    # Initial state
    speed = 0  # km/h
    rpm = IDLE_RPM
    throttle = 0  # 0-100
    load = 15  # 0-100
    coolant_temp = 25  # Celsius
    intake_temp = 20
    catalyst_temp = 100
    distance = 0
    
    target_speed = 0
    
    for t in range(duration_seconds):
        # 1. Determine Target Speed based on Scenario
        if t % 60 == 0: # Change target every minute
            if scenario == 'highway':
                target_speed = random.uniform(80, 120)
            elif scenario == 'city':
                target_speed = random.uniform(0, 50)
            elif scenario == 'idle':
                target_speed = 0
            else: # mixed
                target_speed = random.uniform(0, 100)
                
        # 2. Driver Input (Throttle/Brake)
        speed_diff = target_speed - speed
        
        if scenario == 'aggressive':
            accel_factor = 2.0
        else:
            accel_factor = 0.5
            
        if speed_diff > 5:
            throttle = min(100, throttle + 5 * accel_factor)
        elif speed_diff < -5:
            throttle = 0 # Braking
        else:
            throttle = max(0, min(100, throttle + random.uniform(-2, 2))) # Maintain
            
        # 3. Physics Update (Speed)
        if throttle > 0:
            acceleration = (throttle / 10.0) * (1 - (speed / 200)) # Diminishing returns
            speed += acceleration * 0.1 # Delta time
        else:
            speed -= 0.5 # Coasting/Braking friction
            
        speed = max(0, speed)
        
        # 4. Gear Selection & RPM
        gear = 1
        for i, limit in enumerate(MIN_SPEED_FOR_GEAR):
            if speed > limit:
                gear = i + 1
        
        # Anomaly: Wrong Gear (High RPM at low speed)
        if scenario == 'inefficient' and speed > 20 and speed < 50:
            gear = 1 # Force 1st gear
            
        # Calculate RPM
        # RPM = (Speed_m_s * 60 * FinalDrive * GearRatio) / (2 * pi * Radius)
        speed_ms = speed * 1000 / 3600
        if speed < 1:
            rpm = IDLE_RPM + (throttle * 20) # Revving in neutral/stopped
        else:
            ratio = GEAR_RATIOS[gear-1]
            calc_rpm = (speed_ms * 60 * FINAL_DRIVE * ratio) / (2 * 3.14159 * TIRE_RADIUS)
            rpm = max(IDLE_RPM, min(MAX_RPM, calc_rpm))
            
        # 5. Engine Load
        # Load is high when accelerating hard or climbing (random noise)
        base_load = (throttle * 0.8) + (speed * 0.1)
        load = min(100, max(10, base_load + random.uniform(-5, 5)))
        
        # Anomaly: High Load at Low Speed (Lugging)
        if scenario == 'inefficient' and speed > 10 and speed < 30 and gear > 3:
             load = 90
             
        # 6. Temperatures
        # Coolant warms up to ~90
        target_coolant = 90
        if coolant_temp < target_coolant:
            coolant_temp += 0.05 + (rpm/10000)
            
        # Intake temp (ambient + heat soak)
        intake_temp = 20 + (coolant_temp * 0.1) - (speed * 0.05) # Airflow cools it
        intake_temp = max(20, intake_temp)
        
        # Catalyst Temp (depends on load/rpm)
        target_cat = 400 + (rpm * 0.05) + (load * 2)
        catalyst_temp += (target_cat - catalyst_temp) * 0.01
        
        # 7. Distance
        distance += speed_ms # meters per second
        
        # 8. Store Data
        # Mapping to CSV columns
        row = {
            'Time_1s': t, # Relative time in file
            'Driver_ID': 'SimDriver_01',
            'LapID': 1, # Dummy
            'GPS Longitude': 0, # Dummy
            'GPS Latitude': 0, # Dummy
            'GPS Bearing': 0, # Dummy
            'Accelerometer (Total)': 0, # Dummy
            'Accelerometer (X)': 0,
            'Accelerometer (Y)': 0,
            'Accelerometer (Z)': 0,
            'Coolant': round(coolant_temp, 1),
            'RPM': int(rpm),
            'Altitude(GPS)': 100,
            'OBD Speed': round(speed, 1),
            'kff1298': 0, # Unknown column, keeping 0
            'Torque': round(load * 3, 1), # Simulated torque
            'F_M': 0,
            'AuthorisedClass': 'Car',
            # NEW COLUMNS FOR ANALYSIS
            'Throttle_Position': round(throttle, 1),
            'Engine_Load': round(load, 1),
            'Intake_Air_Temp': round(intake_temp, 1),
            'Catalyst_Temperature': round(catalyst_temp, 1),
            'Gear': gear,
            'Trip_Distance_m': round(distance, 1)
        }
        data.append(row)
        
    return pd.DataFrame(data)

def main():
    ensure_dir(OUTPUT_FOLDER)
    
    scenarios = ['city', 'highway', 'mixed', 'aggressive', 'inefficient', 'idle']
    
    for week in range(1, NUM_WEEKS + 1):
        print(f"Generating Week {week}...")
        
        # Pick a dominant scenario for the week or mix them
        week_scenario = random.choice(scenarios)
        
        # Generate data
        df = simulate_trip(DATA_POINTS_PER_WEEK, scenario=week_scenario)
        
        # Add timestamps
        week_start = START_DATE + timedelta(weeks=week-1)
        df['Timestamp'] = [week_start + timedelta(seconds=i) for i in range(len(df))]
        
        # Save
        filename = os.path.join(OUTPUT_FOLDER, f'week_{week}.csv')
        df.to_csv(filename, index=False)
        print(f"Saved {filename}")

if __name__ == "__main__":
    main()
