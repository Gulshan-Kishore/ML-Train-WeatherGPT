"""
City Climate Database & Dynamic Resolver
========================================
Provides meteorological baseline profiles for cities across India and the world.
Includes dynamic deterministic fallback for ANY custom city or town, ensuring
WeatherGPT reliably resolves any location offline without an external API.
"""

import re
import hashlib
from typing import Dict, Any, Optional

# Meteorological baseline profiles for major Indian and global cities
# Format: (temp_avg, humidity, pressure, wind_speed, precipitation, month)
CITY_PROFILES: Dict[str, Dict[str, Any]] = {
    # --- Punjab & Northern India ---
    "Jalandhar": {"temp_avg": 25.0, "humidity": 58.0, "pressure": 1011.0, "wind_speed": 12.0, "precipitation": 0.0, "month": 6},
    "Amritsar": {"temp_avg": 24.5, "humidity": 56.0, "pressure": 1011.2, "wind_speed": 11.5, "precipitation": 0.0, "month": 6},
    "Ludhiana": {"temp_avg": 25.5, "humidity": 57.0, "pressure": 1011.0, "wind_speed": 12.0, "precipitation": 0.0, "month": 6},
    "Chandigarh": {"temp_avg": 24.0, "humidity": 55.0, "pressure": 1010.5, "wind_speed": 13.0, "precipitation": 0.0, "month": 6},
    "Patiala": {"temp_avg": 25.0, "humidity": 58.0, "pressure": 1011.0, "wind_speed": 11.0, "precipitation": 0.0, "month": 6},
    "Bathinda": {"temp_avg": 26.5, "humidity": 48.0, "pressure": 1010.0, "wind_speed": 14.0, "precipitation": 0.0, "month": 6},
    "Hoshiarpur": {"temp_avg": 24.0, "humidity": 60.0, "pressure": 1011.5, "wind_speed": 10.5, "precipitation": 0.0, "month": 6},
    "Mohali": {"temp_avg": 24.0, "humidity": 55.0, "pressure": 1010.5, "wind_speed": 12.5, "precipitation": 0.0, "month": 6},

    # --- Delhi NCR & Upper Gangetic Plain ---
    "Delhi": {"temp_avg": 26.5, "humidity": 62.0, "pressure": 1010.5, "wind_speed": 13.0, "precipitation": 0.0, "month": 6},
    "New Delhi": {"temp_avg": 26.5, "humidity": 62.0, "pressure": 1010.5, "wind_speed": 13.0, "precipitation": 0.0, "month": 6},
    "Noida": {"temp_avg": 26.5, "humidity": 61.0, "pressure": 1010.5, "wind_speed": 12.5, "precipitation": 0.0, "month": 6},
    "Gurugram": {"temp_avg": 27.0, "humidity": 58.0, "pressure": 1010.0, "wind_speed": 13.5, "precipitation": 0.0, "month": 6},
    "Faridabad": {"temp_avg": 26.8, "humidity": 60.0, "pressure": 1010.2, "wind_speed": 12.5, "precipitation": 0.0, "month": 6},
    "Ghaziabad": {"temp_avg": 26.5, "humidity": 62.0, "pressure": 1010.5, "wind_speed": 12.0, "precipitation": 0.0, "month": 6},

    # --- Western & Central India ---
    "Mumbai": {"temp_avg": 28.5, "humidity": 78.0, "pressure": 1008.2, "wind_speed": 18.0, "precipitation": 2.5, "month": 7},
    "Pune": {"temp_avg": 25.0, "humidity": 64.0, "pressure": 1011.0, "wind_speed": 14.0, "precipitation": 0.5, "month": 7},
    "Nagpur": {"temp_avg": 28.0, "humidity": 58.0, "pressure": 1009.5, "wind_speed": 13.0, "precipitation": 1.0, "month": 7},
    "Nashik": {"temp_avg": 24.5, "humidity": 66.0, "pressure": 1011.5, "wind_speed": 15.0, "precipitation": 0.8, "month": 7},
    "Ahmedabad": {"temp_avg": 29.0, "humidity": 55.0, "pressure": 1008.5, "wind_speed": 15.0, "precipitation": 0.0, "month": 6},
    "Surat": {"temp_avg": 28.5, "humidity": 74.0, "pressure": 1008.5, "wind_speed": 16.0, "precipitation": 1.5, "month": 7},
    "Vadodara": {"temp_avg": 28.8, "humidity": 60.0, "pressure": 1009.0, "wind_speed": 14.5, "precipitation": 0.2, "month": 6},
    "Jaipur": {"temp_avg": 28.5, "humidity": 45.0, "pressure": 1009.0, "wind_speed": 14.0, "precipitation": 0.0, "month": 6},
    "Jodhpur": {"temp_avg": 30.0, "humidity": 40.0, "pressure": 1008.0, "wind_speed": 15.5, "precipitation": 0.0, "month": 6},
    "Udaipur": {"temp_avg": 26.5, "humidity": 52.0, "pressure": 1010.0, "wind_speed": 13.0, "precipitation": 0.0, "month": 6},
    "Bhopal": {"temp_avg": 26.8, "humidity": 62.0, "pressure": 1010.0, "wind_speed": 13.5, "precipitation": 1.0, "month": 7},
    "Indore": {"temp_avg": 26.0, "humidity": 63.0, "pressure": 1010.5, "wind_speed": 14.0, "precipitation": 0.8, "month": 7},
    "Goa": {"temp_avg": 28.0, "humidity": 82.0, "pressure": 1009.0, "wind_speed": 19.0, "precipitation": 4.0, "month": 7},

    # --- Southern India ---
    "Bengaluru": {"temp_avg": 24.0, "humidity": 68.0, "pressure": 1012.0, "wind_speed": 14.5, "precipitation": 0.5, "month": 8},
    "Bangalore": {"temp_avg": 24.0, "humidity": 68.0, "pressure": 1012.0, "wind_speed": 14.5, "precipitation": 0.5, "month": 8},
    "Chennai": {"temp_avg": 29.5, "humidity": 76.0, "pressure": 1008.5, "wind_speed": 16.5, "precipitation": 1.2, "month": 8},
    "Hyderabad": {"temp_avg": 27.5, "humidity": 64.0, "pressure": 1010.0, "wind_speed": 15.0, "precipitation": 0.8, "month": 7},
    "Kochi": {"temp_avg": 27.5, "humidity": 84.0, "pressure": 1009.5, "wind_speed": 17.0, "precipitation": 5.0, "month": 7},
    "Thiruvananthapuram": {"temp_avg": 27.0, "humidity": 82.0, "pressure": 1010.0, "wind_speed": 16.0, "precipitation": 3.5, "month": 7},
    "Coimbatore": {"temp_avg": 25.5, "humidity": 66.0, "pressure": 1011.5, "wind_speed": 13.5, "precipitation": 0.4, "month": 8},
    "Mysuru": {"temp_avg": 23.5, "humidity": 70.0, "pressure": 1012.5, "wind_speed": 14.0, "precipitation": 0.6, "month": 8},
    "Visakhapatnam": {"temp_avg": 28.5, "humidity": 78.0, "pressure": 1008.8, "wind_speed": 17.0, "precipitation": 1.8, "month": 8},
    "Vijayawada": {"temp_avg": 30.0, "humidity": 72.0, "pressure": 1008.0, "wind_speed": 15.5, "precipitation": 1.2, "month": 8},

    # --- Eastern & Northern Hills ---
    "Kolkata": {"temp_avg": 28.5, "humidity": 79.0, "pressure": 1008.0, "wind_speed": 15.0, "precipitation": 2.2, "month": 7},
    "Patna": {"temp_avg": 27.0, "humidity": 68.0, "pressure": 1009.5, "wind_speed": 12.0, "precipitation": 1.0, "month": 7},
    "Ranchi": {"temp_avg": 24.5, "humidity": 70.0, "pressure": 1011.0, "wind_speed": 13.0, "precipitation": 1.2, "month": 7},
    "Bhubaneswar": {"temp_avg": 28.5, "humidity": 77.0, "pressure": 1008.5, "wind_speed": 16.0, "precipitation": 2.0, "month": 7},
    "Guwahati": {"temp_avg": 26.5, "humidity": 80.0, "pressure": 1009.5, "wind_speed": 11.5, "precipitation": 3.0, "month": 7},
    "Lucknow": {"temp_avg": 27.0, "humidity": 64.0, "pressure": 1010.0, "wind_speed": 12.5, "precipitation": 0.5, "month": 7},
    "Kanpur": {"temp_avg": 27.2, "humidity": 63.0, "pressure": 1010.0, "wind_speed": 12.5, "precipitation": 0.4, "month": 7},
    "Varanasi": {"temp_avg": 27.5, "humidity": 65.0, "pressure": 1009.8, "wind_speed": 12.0, "precipitation": 0.6, "month": 7},
    "Shimla": {"temp_avg": 16.5, "humidity": 65.0, "pressure": 1015.0, "wind_speed": 14.0, "precipitation": 1.0, "month": 7},
    "Manali": {"temp_avg": 14.0, "humidity": 62.0, "pressure": 1016.0, "wind_speed": 12.0, "precipitation": 1.2, "month": 7},
    "Dehradun": {"temp_avg": 23.0, "humidity": 70.0, "pressure": 1011.0, "wind_speed": 11.0, "precipitation": 2.0, "month": 7},
    "Srinagar": {"temp_avg": 17.5, "humidity": 58.0, "pressure": 1014.0, "wind_speed": 10.0, "precipitation": 0.8, "month": 6},
    "Jammu": {"temp_avg": 26.0, "humidity": 60.0, "pressure": 1011.0, "wind_speed": 12.0, "precipitation": 0.5, "month": 6},

    # --- Global Major Cities ---
    "London": {"temp_avg": 12.0, "humidity": 80.0, "pressure": 1014.0, "wind_speed": 17.0, "precipitation": 1.0, "month": 10},
    "New York": {"temp_avg": 15.0, "humidity": 65.0, "pressure": 1013.5, "wind_speed": 16.0, "precipitation": 0.0, "month": 5},
    "Tokyo": {"temp_avg": 17.0, "humidity": 68.0, "pressure": 1012.0, "wind_speed": 12.5, "precipitation": 0.8, "month": 6},
    "Paris": {"temp_avg": 14.5, "humidity": 72.0, "pressure": 1013.5, "wind_speed": 15.0, "precipitation": 0.5, "month": 6},
    "Berlin": {"temp_avg": 13.0, "humidity": 70.0, "pressure": 1014.0, "wind_speed": 16.0, "precipitation": 0.5, "month": 6},
    "Rome": {"temp_avg": 19.0, "humidity": 62.0, "pressure": 1013.0, "wind_speed": 13.0, "precipitation": 0.2, "month": 6},
    "Madrid": {"temp_avg": 21.0, "humidity": 45.0, "pressure": 1012.5, "wind_speed": 14.0, "precipitation": 0.1, "month": 6},
    "Dubai": {"temp_avg": 34.0, "humidity": 48.0, "pressure": 1007.5, "wind_speed": 16.0, "precipitation": 0.0, "month": 7},
    "Singapore": {"temp_avg": 28.0, "humidity": 83.0, "pressure": 1009.0, "wind_speed": 11.0, "precipitation": 3.0, "month": 6},
    "Sydney": {"temp_avg": 18.0, "humidity": 66.0, "pressure": 1016.0, "wind_speed": 18.0, "precipitation": 1.2, "month": 6},
    "Toronto": {"temp_avg": 11.5, "humidity": 68.0, "pressure": 1014.5, "wind_speed": 17.5, "precipitation": 0.8, "month": 5},
    "Chicago": {"temp_avg": 13.5, "humidity": 67.0, "pressure": 1013.5, "wind_speed": 19.0, "precipitation": 0.6, "month": 5},
    "Los Angeles": {"temp_avg": 20.5, "humidity": 62.0, "pressure": 1013.0, "wind_speed": 12.0, "precipitation": 0.0, "month": 6},
    "San Francisco": {"temp_avg": 16.0, "humidity": 75.0, "pressure": 1014.0, "wind_speed": 20.0, "precipitation": 0.0, "month": 7},
    "Bangkok": {"temp_avg": 30.0, "humidity": 76.0, "pressure": 1008.5, "wind_speed": 12.0, "precipitation": 3.5, "month": 7},
    "Hong Kong": {"temp_avg": 27.5, "humidity": 82.0, "pressure": 1008.0, "wind_speed": 18.0, "precipitation": 4.0, "month": 7},
    "Lahore": {"temp_avg": 27.0, "humidity": 55.0, "pressure": 1010.0, "wind_speed": 12.0, "precipitation": 0.2, "month": 6},
    "Karachi": {"temp_avg": 29.5, "humidity": 74.0, "pressure": 1008.0, "wind_speed": 21.0, "precipitation": 0.5, "month": 7},
    "Dhaka": {"temp_avg": 28.5, "humidity": 81.0, "pressure": 1008.0, "wind_speed": 14.0, "precipitation": 3.5, "month": 7},
    "Kathmandu": {"temp_avg": 21.5, "humidity": 75.0, "pressure": 1013.0, "wind_speed": 9.0, "precipitation": 2.5, "month": 7},
    "Colombo": {"temp_avg": 28.0, "humidity": 82.0, "pressure": 1009.5, "wind_speed": 16.0, "precipitation": 3.0, "month": 6}
}

# Fast case-insensitive lookup
_LOWER_CITY_LOOKUP = {k.lower(): k for k in CITY_PROFILES.keys()}


def resolve_city_climate(city_name: str) -> Dict[str, Any]:
    """
    Returns climatological baseline parameters for ANY city or town.
    - If the city is in CITY_PROFILES: returns its verified profile.
    - If unknown: generates a realistic, deterministic baseline so the same
      city always produces identical consistent results.
    """
    clean_name = city_name.strip()
    key_lower = clean_name.lower()

    # 1. Exact or case-insensitive match
    if key_lower in _LOWER_CITY_LOOKUP:
        canonical_name = _LOWER_CITY_LOOKUP[key_lower]
        profile = dict(CITY_PROFILES[canonical_name])
        profile["city"] = canonical_name
        return profile

    # 2. Deterministic Fallback for custom/unlisted cities
    # Hash the city name so repeated calls for the same city return identical values
    city_hash = int(hashlib.md5(key_lower.encode("utf-8")).hexdigest()[:8], 16)

    base_temp = 18.0 + (city_hash % 13) * 1.0          # Range: 18°C - 30°C
    base_humidity = 45.0 + ((city_hash >> 4) % 31) * 1.0  # Range: 45% - 75%
    base_pressure = 1008.0 + ((city_hash >> 8) % 7) * 1.0 # Range: 1008 - 1014 hPa
    base_wind = 9.0 + ((city_hash >> 12) % 10) * 1.0      # Range: 9 - 18 km/h

    return {
        "city": clean_name.title(),
        "temp_avg": round(base_temp, 1),
        "humidity": round(base_humidity, 1),
        "pressure": round(base_pressure, 1),
        "wind_speed": round(base_wind, 1),
        "precipitation": 0.0,
        "month": 6
    }


# Common conversational words that should never be misidentified as city names
STOP_WORDS = {
    "weather", "forecast", "temperature", "temp", "rain", "raining", "humidity", "wind",
    "today", "tomorrow", "yesterday", "now", "please", "what", "is", "the", "in", "at",
    "for", "of", "about", "how", "will", "it", "any", "alerts", "alert", "metrics",
    "accuracy", "model", "show", "tell", "me", "give", "and", "or", "to", "a", "an",
    "can", "you", "does", "this", "work", "without", "api", "offline", "hi", "hello", "hey"
}


def extract_city_from_text(user_text: str) -> Optional[str]:
    """
    Extracts a city name from natural language questions:
    - Direct names: 'Mumbai', 'jalandhar', 'new york'
    - Phrases with prepositions: 'weather in London', 'will it rain in Delhi?'
    - Short inputs: 'Tokyo', 'weather Paris'
    """
    clean_text = user_text.strip()
    lower_text = clean_text.lower()

    # Check 1: Known city mentioned anywhere in the text
    # Sort longest first so 'New Delhi' matches before 'Delhi'
    for c_lower in sorted(_LOWER_CITY_LOOKUP.keys(), key=len, reverse=True):
        pattern = r"\b" + re.escape(c_lower) + r"\b"
        if re.search(pattern, lower_text):
            return _LOWER_CITY_LOOKUP[c_lower]

    # Check 2: Preposition pattern (e.g., 'in Delhi', 'for Mumbai', 'about London')
    prep_match = re.search(r"\b(?:in|for|at|of|about|near)\s+([a-zA-Z\s\-\.\']+)", clean_text, re.IGNORECASE)
    if prep_match:
        candidate = prep_match.group(1).strip()
        # Remove trailing punctuation and time words
        candidate = re.split(r"[\?\.\,\!]|\s+(?:today|tomorrow|yesterday|now|please|if|with)\b", candidate, flags=re.IGNORECASE)[0].strip()
        candidate_words = candidate.split()
        if candidate_words and len(candidate_words) <= 3:
            first_word_lower = candidate_words[0].lower()
            if first_word_lower not in STOP_WORDS:
                return candidate.title()

    # Check 3: Short queries (1 to 3 words) after removing stop words
    tokens = [t for t in re.split(r"[^a-zA-Z]", clean_text) if t]
    non_stop = [t for t in tokens if t.lower() not in STOP_WORDS]

    if 1 <= len(non_stop) <= 3:
        candidate = " ".join(non_stop).strip()
        return candidate.title()

    return None
