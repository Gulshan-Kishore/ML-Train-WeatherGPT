"""
Feature Engineering Module
==========================
Transforms raw meteorological observations into machine learning feature matrices.

Features engineered:
1. temp_range: Diurnal temperature spread (temp_max - temp_min).
2. pressure_diff_std: Deviation from standard sea-level pressure (1013.25 hPa).
3. sin_day & cos_day: Cyclical seasonal encoding for the day of the year.
4. city_code: Numeric categorical mapping for cities.
"""

from typing import Tuple
import numpy as np
import pandas as pd

# The 13 input features used across all 3 Random Forest models
FEATURE_COLUMNS = [
    "temp_avg",
    "temp_max",
    "temp_min",
    "temp_range",           # Diurnal temperature range (max - min)
    "humidity",
    "pressure",
    "pressure_diff_std",    # Deviation from standard 1013.25 hPa
    "wind_speed",
    "precipitation",
    "sin_day",              # Seasonal cycle (sine of day of year)
    "cos_day",              # Seasonal cycle (cosine of day of year)
    "month",
    "city_code"             # Encoded city identifier
]

# Numeric encoding for cities
CITY_MAP = {
    "Delhi": 0,
    "Mumbai": 1,
    "Bengaluru": 2,
    "Bangalore": 2,
    "London": 3,
    "New York": 4,
    "Tokyo": 5,
    "Other / Custom": 6
}


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes domain-specific meteorological features from raw weather data:
    1. Diurnal temperature range (temp_max - temp_min)
    2. Sea-level pressure deviation (pressure - 1013.25 hPa)
    3. Cyclical day-of-year transformations using Sine & Cosine
    4. City code mapping
    """
    df = df.copy()

    # 1. Physical temperature range
    if "temp_range" not in df.columns:
        df["temp_range"] = np.round(df["temp_max"] - df["temp_min"], 2)

    # 2. Barometric pressure deviation from standard atmosphere (1013.25 hPa)
    if "pressure_diff_std" not in df.columns:
        df["pressure_diff_std"] = np.round(df["pressure"] - 1013.25, 2)

    # 3. Calendar dates & seasonal cyclical encoding
    if "date" in df.columns:
        df["date_dt"] = pd.to_datetime(df["date"])
        df["day_of_year"] = df["date_dt"].dt.dayofyear
        df["month"] = df["date_dt"].dt.month
    else:
        if "day_of_year" not in df.columns:
            df["day_of_year"] = 180  # Default to mid-year if date is absent
        if "month" not in df.columns:
            df["month"] = 6

    # Why Sine & Cosine encoding?
    # Day 365 (Dec 31) and Day 1 (Jan 1) are physically 1 day apart,
    # but numerically 364 apart. Sine and Cosine preserve continuous seasonal geometry!
    df["sin_day"] = np.round(np.sin(2 * np.pi * df["day_of_year"] / 365.25), 4)
    df["cos_day"] = np.round(np.cos(2 * np.pi * df["day_of_year"] / 365.25), 4)

    # 4. City code mapping
    if "city" in df.columns:
        df["city_code"] = df["city"].map(lambda c: CITY_MAP.get(c, CITY_MAP["Other / Custom"]))
    elif "city_code" not in df.columns:
        df["city_code"] = CITY_MAP["Other / Custom"]

    return df


def prepare_training_data(csv_path: str) -> Tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Loads raw CSV dataset, applies feature engineering, and returns:
    - X: Feature matrix (13 engineered columns)
    - y_temp: Target for Regression (temp_tomorrow)
    - y_rain: Target for Binary Classification (rain_tomorrow)
    - y_cond: Target for Multi-class Classification (condition_tomorrow)
    """
    raw_df = pd.read_csv(csv_path)
    df = add_engineered_features(raw_df)

    X = df[FEATURE_COLUMNS].copy()
    y_temp = df["temp_tomorrow"].copy()
    y_rain = df["rain_tomorrow"].copy()
    y_cond = df["condition_tomorrow"].copy()

    return X, y_temp, y_rain, y_cond


def build_single_inference_vector(
    temp_avg: float,
    humidity: float,
    pressure: float,
    wind_speed: float = 14.0,
    precipitation: float = 0.0,
    temp_max: float = None,
    temp_min: float = None,
    city: str = "Delhi",
    month: int = 6,
    day_of_year: int = 172
) -> pd.DataFrame:
    """
    Constructs a single-row DataFrame with all 13 features for real-time model prediction.
    Fills in realistic physical defaults if optional parameters are omitted.
    """
    # Estimate diurnal spread if min/max are not provided
    if temp_max is None:
        temp_max = round(temp_avg + 4.5, 1)
    if temp_min is None:
        temp_min = round(temp_avg - 4.5, 1)

    temp_range = round(temp_max - temp_min, 2)
    pressure_diff_std = round(pressure - 1013.25, 2)

    sin_day = round(float(np.sin(2 * np.pi * day_of_year / 365.25)), 4)
    cos_day = round(float(np.cos(2 * np.pi * day_of_year / 365.25)), 4)
    city_code = CITY_MAP.get(city, CITY_MAP["Other / Custom"])

    data_dict = {
        "temp_avg": [float(temp_avg)],
        "temp_max": [float(temp_max)],
        "temp_min": [float(temp_min)],
        "temp_range": [float(temp_range)],
        "humidity": [float(humidity)],
        "pressure": [float(pressure)],
        "pressure_diff_std": [float(pressure_diff_std)],
        "wind_speed": [float(wind_speed)],
        "precipitation": [float(precipitation)],
        "sin_day": [float(sin_day)],
        "cos_day": [float(cos_day)],
        "month": [int(month)],
        "city_code": [int(city_code)]
    }

    return pd.DataFrame(data_dict)[FEATURE_COLUMNS]
