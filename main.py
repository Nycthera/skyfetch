#!/usr/bin/env python3
import argparse
import requests
from datetime import date
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()
DEFAULT_API_KEY = os.getenv('API_KEY')  # .env should have API_KEY=your_key_here

# ======================
# ASCII Weather Icons
# ======================
WEATHER_ICONS = {
    "sunny": """
          |
          |   .
   `.  *  |     .'
     `. ._|_* .'  .
   . * .'   `.  *
-------|     |-------
   .  *`.___.' *  .
      .'  |* `.  *
    .' *  |  . `.
        . |
          | jgs
""",
    "cloudy": """
     .--.    
  .-(    ).  
 (___.__)__)
""",
    "rain": """
 , // ,,/ ,.// ,/ ,// / /, // ,/, /, // ,/,
 /, .-'   `-. ,// ////, // ,/,/, // ///
""",
    "snow": """
    *  .  *
  . _\\/ \\/_ .
   \\  \\ /  / 
  -==>: X :<==-
""",
    "storm": """
   .-.
  (   )
 (___)
  ⚡⚡⚡
"""
}

# ======================
# ASCII Moon Phases
# ======================
MOON_ICONS = {
    "new": """
     *****     
   *********   
  ***********  
  ***********  
   *********   
     *****     
""",
    "first_quarter": """
     *****     
   ***     *   
  ***      *   
  ***      *   
   ***     *   
     *****     
""",
    "full": """
     *****     
   *******     
  *********    
  *********    
   *******     
     *****     
""",
    "last_quarter": """
     *****     
   *     ***   
  *      ***   
  *      ***   
   *     ***   
     *****     
"""
}

# ======================
# Fetch Functions
# ======================
def fetch_weather(lat=1.29, lon=103.85):
    try:
        res = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true",
            timeout=5
        )
        res.raise_for_status()
        return res.json()["current_weather"]
    except Exception as e:
        print(f"[Weather fetch failed: {e}]")
        return None

def get_location():
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json()
        lat, lon = map(float, data.get('loc', '1.29,103.85').split(','))
        return {
            'city': data.get('city', 'Singapore'),
            'country': data.get('country', 'SG'),
            'lat': lat,
            'lon': lon
        }
    except Exception as e:
        print(f"[Location fetch failed: {e}]")
        return {'lat': 1.29, 'lon': 103.85, 'city': 'Singapore', 'country': 'SG'}

def fetch_moon_phase(location, api_key):
    today = date.today().isoformat()
    if not api_key:
        print("[Moon fetch failed: No API key provided]")
        return None
    try:
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location['city']}/{today}/{today}?key={api_key}&includeAstronomy=true"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        return data["days"][0]["moonphase"]  # 0–1
    except Exception as e:
        print(f"[Moon fetch failed: {e}]")
        return None

# ======================
# Mapping Functions
# ======================
def map_weather_icon(code):
    if code == 0: return WEATHER_ICONS["sunny"]
    if code in [1, 2, 3]: return WEATHER_ICONS["cloudy"]
    if 51 <= code <= 67 or 80 <= code <= 82: return WEATHER_ICONS["rain"]
    if 71 <= code <= 77 or 85 <= code <= 86: return WEATHER_ICONS["snow"]
    if 95 <= code <= 99: return WEATHER_ICONS["storm"]
    return WEATHER_ICONS["cloudy"]

def map_moon_icon(phase):
    if phase < 0.125 or phase > 0.875: return MOON_ICONS["new"]
    elif 0.125 <= phase < 0.375: return MOON_ICONS["first_quarter"]
    elif 0.375 <= phase < 0.625: return MOON_ICONS["full"]
    elif 0.625 <= phase < 0.875: return MOON_ICONS["last_quarter"]
    return MOON_ICONS["new"]

# ======================
# Main CLI
# ======================
def main():
    parser = argparse.ArgumentParser(description="Weather & Moon ASCII Tool")
    parser.add_argument("--moon", action="store_true", help="Show moon phase")
    parser.add_argument("--weather", action="store_true", help="Show weather")
    parser.add_argument("--all", action="store_true", help="Show all info")
    parser.add_argument("--api-key", type=str, help="Visual Crossing API Key (overrides .env)")
    args = parser.parse_args()

    # If no flags are provided, default to --all
    if not any([args.moon, args.weather, args.all]):
        args.all = True

    api_key = args.api_key or DEFAULT_API_KEY
    if not api_key and (args.moon or args.all):
        print("Error: You must provide a Visual Crossing API key either via --api-key or .env")
        sys.exit(1)

    location = get_location()

    if args.weather or args.all:
        w = fetch_weather(location['lat'], location['lon'])
        if w:
            icon = map_weather_icon(w["weathercode"])
            print(f"\nWeather in {location['city']}: {w['temperature']}°C\n{icon}")

    if args.moon or args.all:
        m = fetch_moon_phase(location, api_key)
        if m is not None:
            icon = map_moon_icon(m)
            print(f"\nMoon Phase ({m:.2f}):\n{icon}")

if __name__ == "__main__":
    main()
