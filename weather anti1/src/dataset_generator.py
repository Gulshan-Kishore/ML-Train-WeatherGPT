"""
Weather Historical Dataset Generator
====================================
Generates meteorologically realistic daily historical weather data for multiple cities.
Incorporates physical principles:
- Annual seasonal temperature curves (sinusoidal cycles)
- Barometric pressure fluctuations
- Monsoon humidity boost
- Rain generation based on moisture and pressure drops

Run:
    python src/dataset_generator.py
"""

import os
import numpy as np
import pandas as pd

# Fixed seed for reproducible data generation
np.random.seed(42)

# Climate configurations for sample training cities
CITY_PROFILES = {
    "Delhi": {
        "base_temp": 25.0,
        "temp_amplitude": 12.0,      # Hot summers ~38°C, chilly winters ~13°C
        "diurnal_range": 11.0,       # Difference between day max and night min
        "base_humidity": 55.0,
        "monsoon_humidity_boost": 30.0,
        "base_pressure": 1010.0,
        "monsoon_start": 6,          # June
        "monsoon_end": 9,            # September
        "rain_probability_base": 0.08,
        "rain_probability_monsoon": 0.55
    },
    "Mumbai": {
        "base_temp": 28.0,
        "temp_amplitude": 3.0,       # Coastal maritime, steady temperatures
        "diurnal_range": 6.0,
        "base_humidity": 72.0,
        "monsoon_humidity_boost": 20.0,
        "base_pressure": 1008.0,
        "monsoon_start": 6,
        "monsoon_end": 9,
        "rain_probability_base": 0.05,
        "rain_probability_monsoon": 0.70
    },
    "Bengaluru": {
        "base_temp": 24.0,
        "temp_amplitude": 4.5,       # Plateau altitude, pleasant moderate climate
        "diurnal_range": 9.0,
        "base_humidity": 65.0,
        "monsoon_humidity_boost": 22.0,
        "base_pressure": 1012.0,
        "monsoon_start": 5,
        "monsoon_end": 10,
        "rain_probability_base": 0.12,
        "rain_probability_monsoon": 0.50
    },
    "London": {
        "base_temp": 11.5,
        "temp_amplitude": 8.0,       # Cool temperate oceanic
        "diurnal_range": 6.5,
        "base_humidity": 78.0,
        "monsoon_humidity_boost": 5.0,
        "base_pressure": 1015.0,
        "monsoon_start": 10,
        "monsoon_end": 1,
        "rain_probability_base": 0.35,
        "rain_probability_monsoon": 0.45
    },
    "New York": {
        "base_temp": 13.0,
        "temp_amplitude": 14.0,      # Continental (hot summers, freezing winters)
        "diurnal_range": 8.5,
        "base_humidity": 63.0,
        "monsoon_humidity_boost": 8.0,
        "base_pressure": 1014.0,
        "monsoon_start": 4,
        "monsoon_end": 8,
        "rain_probability_base": 0.28,
        "rain_probability_monsoon": 0.36
    }
}


def generate_city_weather(city_name: str, config: dict, start_date: str = "2023-01-01", num_days: int = 1095) -> pd.DataFrame:
    """
    Simulates realistic daily time-series weather observations for one city over `num_days`.
    """
    date_range = pd.date_range(start=start_date, periods=num_days, freq="D")
    records = []

    # Persistence variables for weather anomalies across consecutive days
    prev_temp_anomaly = 0.0
    prev_pressure_anomaly = 0.0

    for date in date_range:
        day_of_year = date.dayofyear
        month = date.month

        # 1. Seasonal Temperature Curve (Sinusoidal cycle)
        phase_shift = 205
        season_factor = -np.cos(2 * np.pi * (day_of_year - (phase_shift - 182.5)) / 365.25)

        # Autoregressive temperature anomaly (heatwaves / cold spells persist for days)
        temp_noise = np.random.normal(0, 1.2)
        temp_anomaly = 0.75 * prev_temp_anomaly + 0.25 * temp_noise
        prev_temp_anomaly = temp_anomaly

        expected_temp = config["base_temp"] + (config["temp_amplitude"] * season_factor) + temp_anomaly

        # 2. Barometric Pressure
        pressure_noise = np.random.normal(0, 2.5)
        pressure_anomaly = 0.70 * prev_pressure_anomaly + 0.30 * pressure_noise
        prev_pressure_anomaly = pressure_anomaly

        expected_pressure = config["base_pressure"] - (season_factor * 3.0) + pressure_anomaly

        # 3. Monsoon & Humidity Dynamics
        if config["monsoon_start"] <= config["monsoon_end"]:
            in_monsoon = config["monsoon_start"] <= month <= config["monsoon_end"]
        else:
            in_monsoon = (month >= config["monsoon_start"]) or (month <= config["monsoon_end"])

        base_h = config["base_humidity"]
        if in_monsoon:
            base_h += config["monsoon_humidity_boost"]

        pressure_deficit = max(0, 1013.25 - expected_pressure)
        humidity = np.clip(base_h + (pressure_deficit * 1.5) + np.random.normal(0, 6.0), 20.0, 99.0)

        # 4. Wind Speed (km/h)
        base_wind = 12.0 + (abs(pressure_anomaly) * 1.8) + np.random.exponential(4.0)
        wind_speed = np.clip(base_wind, 2.0, 65.0)

        # 5. Rain & Precipitation
        rain_prob = config["rain_probability_monsoon"] if in_monsoon else config["rain_probability_base"]
        if humidity > 75.0 and expected_pressure < 1012.0:
            rain_prob = min(0.92, rain_prob + 0.35)
        elif humidity < 45.0:
            rain_prob = max(0.01, rain_prob - 0.20)

        is_rain = 1 if np.random.rand() < rain_prob else 0

        if is_rain:
            precipitation = float(np.round(np.random.gamma(shape=2.5, scale=6.0), 1))
            expected_temp -= np.random.uniform(1.0, 3.5)  # Evaporative cooling
        else:
            precipitation = 0.0

        # Diurnal Max & Min Temperatures
        diurnal_spread = max(3.5, config["diurnal_range"] + np.random.normal(0, 1.2))
        temp_avg = float(np.round(expected_temp, 1))
        temp_max = float(np.round(temp_avg + (diurnal_spread * 0.55), 1))
        temp_min = float(np.round(temp_avg - (diurnal_spread * 0.45), 1))

        # Weather condition category
        if is_rain:
            condition = "Rainy"
        elif humidity > 85.0 and temp_avg < 15.0:
            condition = "Foggy"
        elif humidity > 70.0:
            condition = "Cloudy"
        else:
            condition = "Sunny"

        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "city": city_name,
            "temp_avg": temp_avg,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "humidity": round(float(humidity), 1),
            "pressure": round(float(expected_pressure), 1),
            "wind_speed": round(float(wind_speed), 1),
            "precipitation": precipitation,
            "condition": condition
        })

    df_city = pd.DataFrame(records)

    # 6. Create Supervised Target Variables (Next-Day Weather)
    df_city["temp_tomorrow"] = df_city["temp_avg"].shift(-1)
    df_city["rain_tomorrow"] = (df_city["precipitation"].shift(-1) > 0.5).astype(float)
    df_city["condition_tomorrow"] = df_city["condition"].shift(-1)

    # Drop the final row as it has no next-day target
    df_city = df_city.dropna().copy()
    df_city["rain_tomorrow"] = df_city["rain_tomorrow"].astype(int)

    return df_city


def generate_full_historical_dataset(output_path: str = "data/weather_historical.csv", num_days: int = 1095) -> pd.DataFrame:
    """
    Generates combined 3-year historical dataset across all cities and writes to CSV.
    """
    all_city_dfs = []
    print(f"Generating historical climate data for {len(CITY_PROFILES)} cities ({num_days} days each)...")

    for city, config in CITY_PROFILES.items():
        city_df = generate_city_weather(city, config, start_date="2023-01-01", num_days=num_days)
        all_city_dfs.append(city_df)
        print(f"  ✓ {city}: {len(city_df)} daily observations generated.")

    full_df = pd.concat(all_city_dfs, ignore_index=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    full_df.to_csv(output_path, index=False)
    print(f"Saved dataset to: {output_path} ({len(full_df)} total records)")
    return full_df


if __name__ == "__main__":
    generate_full_historical_dataset()
