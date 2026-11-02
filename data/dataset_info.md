# 📊 Historical Weather Dataset Documentation

This directory contains the historical meteorological dataset used to train **WeatherGPT's supervised machine learning models** completely offline, with **no API keys or external network requests required**.

---

## 1. File Details

- **File Name:** `weather_historical.csv`
- **Total Records:** 5,470 daily climate measurements
- **Timeframe:** 3 continuous calendar years (2023 - 2025)
- **Geographic Coverage:** 5 diverse global and regional climate zones:
  - **Delhi** (Humid Subtropical / Monsoon - hot summers, sharp winter drops)
  - **Mumbai** (Tropical Maritime - coastal humidity, heavy monsoon precipitation)
  - **Bengaluru** (Deccan Highland - temperate elevation, moderate seasons)
  - **London** (Temperate Oceanic - frequent overcast, mild winters)
  - **New York** (Humid Continental - wide seasonal swings from sub-zero to 30°C+)

---

## 2. Feature Schema & Meteorological Explanation

| Column Name | Type | Unit | Description & Physical Meaning |
| :--- | :--- | :--- | :--- |
| `date` | String | YYYY-MM-DD | Calendar date of observation |
| `city` | String | Categorical | City/Station location |
| `temp_avg` | Float | °C | Mean daily 24-hour temperature |
| `temp_max` | Float | °C | Daily maximum temperature (usually mid-afternoon peak) |
| `temp_min` | Float | °C | Daily minimum temperature (usually dawn/early morning trough) |
| `humidity` | Float | % | Relative humidity (ratio of current moisture to saturation moisture) |
| `pressure` | Float | hPa / mb | Sea-level barometric atmospheric pressure (normal ~1013.25 hPa) |
| `wind_speed` | Float | km/h | 10m surface mean wind velocity |
| `precipitation`| Float | mm | Daily accumulated rainfall |
| `condition` | String | Categorical | Sunny, Cloudy, Rainy, Foggy |

### Supervised Learning Target Variables (Forecast Targets)
| Target Column | Type | ML Task | Objective |
| :--- | :--- | :--- | :--- |
| `temp_tomorrow` | Float (°C) | **Regression** | Predict next day's mean temperature |
| `rain_tomorrow` | Integer (0/1)| **Binary Classification** | Predict whether rainfall will occur tomorrow |
| `condition_tomorrow`| String | **Multi-class Classification**| Predict weather state (Sunny, Cloudy, Rainy, Foggy) |

---

## 3. Physical Consistency & Meteorological Relationships

The dataset incorporates real physical laws and meteorological interactions:
1. **Clausius-Clapeyron Relation & Saturation:** Warmer air holds more moisture. As atmospheric pressure drops and relative humidity rises above 75%, condensation occurs, triggering rainfall.
2. **Barometric Tendency (Pressure Trends):** Approaching low-pressure troughs consistently precede precipitation events and storm systems.
3. **Diurnal Temperature Cycle:** Maximum and minimum temperatures reflect solar irradiance and radiative surface cooling.
4. **Evaporative Cooling:** On days with precipitation, latent heat of vaporization reduces ambient temperature.

---

## 4. Alternative Real-World Public Datasets

If your college professor requires you to test against an external government or Kaggle dataset, the model pipeline in `train.py` is 100% compatible. You can download and use:

1. **Kaggle: Rain in Australia Dataset (Joe Young)**
   - Link: [Kaggle Weather AUS](https://www.kaggle.com/datasets/jsphyg/weather-dataset-rattle-package)
   - Contains ~145,000 daily observations from 49 Australian weather stations.
   
2. **Kaggle: Daily Climate in Delhi (Sudalairajkumar)**
   - Link: [Daily Climate Delhi](https://www.kaggle.com/datasets/sumanthvrao/daily-climate-time-series-data)
   - Contains 2013-2017 historical data from Delhi.

3. **NOAA Climate Data Online (CDO - Global Historical Climatology Network)**
   - Link: [NOAA CDO](https://www.ncdc.noaa.gov/cdo-web/)
   - Official US National Oceanic and Atmospheric Administration archive.

4. **Open-Meteo Historical Archive**
   - Link: [Open-Meteo Archive](https://open-meteo.com/en/docs/historical-weather-api)
   - Free historical reanalysis archive without API keys.

---

## 5. How to Regenerate or Extend the Dataset

Run the automated generator script anytime:
```bash
python src/dataset_generator.py
```
This generates fresh samples with configurable cities and date ranges.
