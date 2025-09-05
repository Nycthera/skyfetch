#!/usr/bin/env python3
import argparse
import requests
from datetime import date
from dotenv import load_dotenv
import os
import sys
import geocoder
from lunarcalendar import Converter, Solar
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ======================
# Load environment
# ======================
load_dotenv()
DEFAULT_API_KEY = os.getenv('API_KEY')

console = Console()

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
        console.print(f"[red][Weather fetch failed: {e}][/red]")
        return None

def get_location():
    try:
        res = requests.get('https://ipinfo.io/json', timeout=5)
        res.raise_for_status()
        data = res.json()
        lat, lon = map(float, data.get('loc', '1.29,103.85').split(','))
        return {'city': data.get('city', 'Singapore'), 'country': data.get('country', 'SG'), 'lat': lat, 'lon': lon}
    except:
        try:
            g = geocoder.ip('me')
            if g.ok and g.latlng:
                lat, lon = g.latlng
                return {'city': g.city or 'Unknown', 'country': g.country or 'Unknown', 'lat': lat, 'lon': lon}
        except:
            return {'lat':1.29, 'lon':103.85, 'city':'Singapore', 'country':'SG'}

def fetch_moon_phase(location, api_key):
    today = date.today().isoformat()
    if not api_key:
        console.print("[yellow][Moon fetch skipped: No API key][/yellow]")
        return None
    try:
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location['city']}/{today}/{today}?key={api_key}&includeAstronomy=true"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        return data["days"][0]["moonphase"]
    except Exception as e:
        console.print(f"[red][Moon fetch failed: {e}][/red]")
        return None

def gregorian_to_lunar(date):
    solar = Solar(date.year, date.month, date.day)
    lunar = Converter.Solar2Lunar(solar)
    return f"{lunar.year}-{lunar.month}-{lunar.day}"

def fetch_forecast(lat, lon, days=3):
    try:
        res = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=auto",
            timeout=5
        )
        res.raise_for_status()
        data = res.json()["daily"]

        forecast = []
        for i in range(min(days, len(data["time"]))):
            forecast.append({
                "date": data["time"][i],
                "temp_max": data["temperature_2m_max"][i],
                "temp_min": data["temperature_2m_min"][i],
                "precip": data["precipitation_sum"][i],
                "weathercode": data["weathercode"][i],
            })
        return forecast
    except Exception as e:
        console.print(f"[red][Forecast fetch failed: {e}][/red]")
        return None

# ======================
# Mapping Functions
# ======================
def map_weather_icon(code):
    if code == 0: return WEATHER_ICONS["sunny"]
    if code in [1,2,3]: return WEATHER_ICONS["cloudy"]
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
    parser.add_argument("--lat", type=float, help="Override latitude")
    parser.add_argument("--lon", type=float, help="Override longitude")
    parser.add_argument("--api-key", type=str, help="Visual Crossing API Key (overrides .env)")
    parser.add_argument("--forecast", "-F", action="store_true", help="Show weather forecast")
    parser.add_argument("--forecast-days", "-D", type=int, default=3, help="Number of days for forecast (default: 3)")
    args = parser.parse_args()

    location = get_location()
    if args.lat and args.lon:
        location['lat'], location['lon'] = args.lat, args.lon

    if not any([args.moon, args.weather, args.forecast, args.all]):
        args.all = True

    api_key = args.api_key or DEFAULT_API_KEY

    # ---------------- Weather ----------------
    if args.weather or args.all:
        w = fetch_weather(location['lat'], location['lon'])
        if w:
            icon = map_weather_icon(w["weathercode"])
            console.print(Panel.fit(f"{w['temperature']}°C\n{icon}", title=f"Weather in {location['city']}"))

    # ---------------- Moon ----------------
    if args.moon or args.all:
        m = fetch_moon_phase(location, api_key)
        if m is not None:
            icon = map_moon_icon(m)
            lunar_date = gregorian_to_lunar(date.today())
            console.print(Panel.fit(f"Phase: {m:.2f}\n{icon}\nLunar Date: {lunar_date}", title="Moon"))

   # ---------------- Forecast ----------------
    if args.forecast:
        forecast = fetch_forecast(location['lat'], location['lon'], args.forecast_days)
        if forecast:
            console.print(f"[bold underline]{args.forecast_days}-Day Forecast for {location['city']} ({location['country']})[/bold underline]\n")
            for day in forecast:
                icon = map_weather_icon(day["weathercode"]).strip()
                panel = Panel.fit(
                    f"[cyan]Date:[/] {day['date']}\n"
                    f"[magenta]Temp:[/] {day['temp_min']}°C → {day['temp_max']}°C\n"
                    f"[blue]Precip:[/] {day['precip']}mm\n\n"
                    f"{icon}",
                    title=f"[green]{day['date']}[/green]",
                    border_style="bright_blue"
                )
                console.print(panel)


if __name__ == "__main__":
    main()
