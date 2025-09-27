import requests
import random
from config import WEATHER_API_KEY, WEATHER_API_URL

class WeatherAPI:
    @staticmethod
    def get_weather(latitude, longitude):
        try:
            params = {"key": WEATHER_API_KEY, "q": f"{latitude},{longitude}"}
            response = requests.get(WEATHER_API_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            temp = data["current"]["temp_c"]
            hum = data["current"]["humidity"]
            desc = data["current"]["condition"]["text"]
            wind = data["current"]["wind_kph"]  # add wind speed
            return temp, hum, desc, wind
        except Exception as e:
            print(f"API failed: {e}, using simulated data.")
            temp = round(random.uniform(15, 35), 2)
            hum = random.randint(30, 90)
            wind = round(random.uniform(0, 20), 2)
            return temp, hum, "Simulated", wind

    @staticmethod
    def get_historical_weather(latitude, longitude, date):
        try:
            url = WEATHER_API_URL.replace("current", "history")
            params = {"key": WEATHER_API_KEY, "q": f"{latitude},{longitude}", "dt": date}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            temp = data["forecast"]["forecastday"][0]["day"]["avgtemp_c"]
            hum = data["forecast"]["forecastday"][0]["day"]["avghumidity"]
            desc = data["forecast"]["forecastday"][0]["day"]["condition"]["text"]
            wind = data["forecast"]["forecastday"][0]["day"]["maxwind_kph"]
            return temp, hum, desc, wind
        except Exception as e:
            print(f"⚠️ Failed to fetch historical data for {date}: {e}")
            import random
            temp = round(random.uniform(15, 35), 2)
            hum = random.randint(30, 90)
            wind = round(random.uniform(0, 20), 2)
            return temp, hum, "Simulated", wind
