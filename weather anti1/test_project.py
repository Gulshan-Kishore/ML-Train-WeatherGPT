"""
WeatherGPT Automated Verification & Smoke Test
==============================================
Validates dataset integrity, feature engineering calculations,
training pipeline, model metrics, and boundary case inferences.

Run:
    python test_project.py
"""

import os
import unittest
import pandas as pd

from src.features import build_single_inference_vector, FEATURE_COLUMNS
from src.predictor import WeatherPredictor, parse_weather_intent
from src.city_database import extract_city_from_text, resolve_city_climate
from train import train_and_evaluate


class TestWeatherGPT(unittest.TestCase):

    def test_01_dataset_exists_and_valid(self):
        """Verify historical dataset presence and required columns."""
        csv_path = "data/weather_historical.csv"
        self.assertTrue(os.path.exists(csv_path), f"Dataset {csv_path} missing!")
        df = pd.read_csv(csv_path)
        self.assertGreater(len(df), 1000, "Dataset should have at least 1,000 rows")

        required_cols = ["date", "city", "temp_avg", "humidity", "pressure", "precipitation", "rain_tomorrow"]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Column {col} missing in dataset")
            self.assertEqual(df[col].isnull().sum(), 0, f"Column {col} contains unexpected nulls")

    def test_02_feature_engineering(self):
        """Verify feature engineering calculations and vector shape."""
        vec = build_single_inference_vector(
            temp_avg=28.0,
            humidity=85.0,
            pressure=1004.0,
            wind_speed=18.0,
            city="Delhi",
            month=7,
            day_of_year=200
        )
        self.assertEqual(vec.shape, (1, len(FEATURE_COLUMNS)))
        # Check cyclical encoding bounds [-1, 1]
        self.assertTrue(-1.0 <= vec["sin_day"].iloc[0] <= 1.0)
        self.assertTrue(-1.0 <= vec["cos_day"].iloc[0] <= 1.0)
        # Check pressure deviation
        self.assertAlmostEqual(vec["pressure_diff_std"].iloc[0], 1004.0 - 1013.25, places=2)

    def test_03_model_training_and_metrics(self):
        """Verify training output, metrics bounds, and saved files."""
        model_path = "models/weather_model.pkl"
        metrics_path = "models/metrics.json"

        bundle, metrics = train_and_evaluate(model_output_path=model_path)

        self.assertTrue(os.path.exists(model_path))
        self.assertTrue(os.path.exists(metrics_path))

        # Check performance thresholds
        r2 = metrics["temperature_regression"]["r2_score"]
        mae = metrics["temperature_regression"]["mae"]
        acc = metrics["rain_classification"]["accuracy"]

        self.assertGreater(r2, 0.80, f"R2 score ({r2}) should be > 0.80")
        self.assertLess(mae, 3.0, f"MAE ({mae}) should be under 3.0°C")
        self.assertGreater(acc, 0.65, f"Rain classification accuracy ({acc}) should be > 65%")

    def test_04_inference_boundary_cases(self):
        """Verify prediction logic against known physical conditions."""
        predictor = WeatherPredictor("models/weather_model.pkl")

        # Case A: Monsoon storm conditions (High humidity 92%, low pressure 998 hPa)
        storm_pred = predictor.predict(
            temp_avg=30.0,
            humidity=92.0,
            pressure=998.0,
            wind_speed=25.0,
            precipitation=15.0,
            city="Mumbai",
            month=7
        )
        self.assertGreaterEqual(storm_pred["rain_probability"], 50.0, "Storm conditions should trigger high rain probability")

        # Case B: Clear dry winter conditions (Low humidity 25%, high pressure 1022 hPa)
        dry_pred = predictor.predict(
            temp_avg=12.0,
            humidity=25.0,
            pressure=1022.0,
            wind_speed=8.0,
            precipitation=0.0,
            city="Delhi",
            month=1
        )
        self.assertLess(dry_pred["rain_probability"], 40.0, "Clear dry conditions should have low rain probability")

    def test_05_nlp_intent_parser(self):
        """Verify chatbot query understanding."""
        q1 = parse_weather_intent("Will it rain tomorrow in Delhi?")
        self.assertEqual(q1["city"], "Delhi")
        self.assertEqual(q1["type"], "prediction_query")

        q2 = parse_weather_intent("What is the model accuracy and MAE?")
        self.assertEqual(q2["type"], "metrics_query")

        q3 = parse_weather_intent("How does this weather model work without API?")
        self.assertEqual(q3["type"], "educational_faq")

    def test_06_city_recognition(self):
        """Verify city name extraction and baseline resolution."""
        # Test extraction of custom and listed cities
        self.assertEqual(extract_city_from_text("jalandhar"), "Jalandhar")
        self.assertEqual(extract_city_from_text("weather in amritsar"), "Amritsar")
        self.assertEqual(extract_city_from_text("what about Paris?"), "Paris")
        self.assertEqual(extract_city_from_text("Kolkata temperature"), "Kolkata")

        # Returns None when no city is mentioned
        self.assertIsNone(extract_city_from_text("will it rain today?"))

        # Verify resolution provides physical bounds
        j_prof = resolve_city_climate("Jalandhar")
        self.assertEqual(j_prof["city"], "Jalandhar")
        self.assertTrue(10.0 <= j_prof["temp_avg"] <= 45.0)
        self.assertTrue(20.0 <= j_prof["humidity"] <= 100.0)

        # Verify custom/unknown town resolution
        custom_prof = resolve_city_climate("Phagwara")
        self.assertEqual(custom_prof["city"], "Phagwara")
        self.assertTrue(10.0 <= custom_prof["temp_avg"] <= 45.0)


if __name__ == "__main__":
    unittest.main()
