from config import get_supabase_client
from datetime import datetime, timedelta
import pandas as pd
from  weather_api import WeatherAPI
from config import WEATHER_API_KEY, WEATHER_API_URL
import requests
import statistics

class SupabaseDB:
    def __init__(self):
        self.client = get_supabase_client()
    
    # Insert weather record
    def insert_weather(self, locality_id, temperature, humidity, description, wind_speed=None, measurement_date=None):
        if not measurement_date:
            measurement_date = datetime.now().isoformat()
        wind_speed = float(wind_speed) if wind_speed is not None else None
        self.client.table("weather_data").insert({
            "locality_id": locality_id,
            "temperature": temperature,
            "humidity": humidity,
            "description": description,
            "wind_speed": wind_speed,
            "measurement_date": measurement_date
        }).execute()

    # Get last n days weather
    def get_last_n_days(self, locality_id, days=7):
        locality = self.get_locality_by_id(locality_id)
        if not locality:
            return []

        cutoff = (datetime.now() - timedelta(days=days-1)).date()
        result = (
            self.client.table("weather_data")
            .select("*")
            .eq("locality_id", locality_id)
            .gte("measurement_date", cutoff.isoformat())
            .order("measurement_date", desc=False)
            .execute()
        )
        records = result.data
        existing_dates = {r["measurement_date"][:10]: r for r in records}

        full_records = []
        for i in range(days):
            day = (datetime.now() - timedelta(days=days-1-i)).date().isoformat()
            if day in existing_dates:
                full_records.append(existing_dates[day])
            else:
                # Fetch historical from API
                temp, hum, desc, wind = WeatherAPI.get_historical_weather(locality["latitude"], locality["longitude"], day)
                self.insert_weather(locality_id, temp, hum, desc, wind_speed=wind, measurement_date=day)
                full_records.append({
                    "measurement_date": day,
                    "temperature": temp,
                    "humidity": hum,
                    "description": desc,
                    "wind_speed": float(wind)
                })
        return full_records

    # Analyze trends
    def analyze_weather(self, locality_id, days=7):
        records = self.get_last_n_days(locality_id, days)
        if not records:
            return None

        temps = [r["temperature"] for r in records if r["temperature"] is not None]
        hums = [r["humidity"] for r in records if r["humidity"] is not None]
        conditions = [r["description"] for r in records if r.get("description")]
        winds = []
        for r in records:
            w = r.get("wind_speed")
            if w is None:
                continue
            try:
                winds.append(float(w))
            except (ValueError, TypeError):
                # skip values that can't be converted
                continue

        analysis = {
            "records": len(records),
            # Temperature
            "temp_avg": round(sum(temps)/len(temps), 2) if temps else None,
            "temp_min": min(temps) if temps else None,
            "temp_max": max(temps) if temps else None,
            "temp_range": round(max(temps)-min(temps), 2) if temps else None,
            "temp_std": round(statistics.stdev(temps), 2) if len(temps) > 1 else 0,
            "temp_trend": "Increasing" if temps[-1] > temps[0] else "Decreasing" if temps[-1] < temps[0] else "Stable",
            # Humidity
            "hum_avg": round(sum(hums)/len(hums), 2) if hums else None,
            "hum_min": min(hums) if hums else None,
            "hum_max": max(hums) if hums else None,
            "hum_range": round(max(hums)-min(hums), 2) if hums else None,
            "hum_std": round(statistics.stdev(hums), 2) if len(hums) > 1 else 0,
            # Wind
            "wind_avg": round(sum(winds)/len(winds), 2) if winds else None,
            "wind_min": min(winds) if winds else None,
            "wind_max": max(winds) if winds else None,
            "wind_std": round(statistics.stdev(winds), 2) if len(winds) > 1 else 0,
            # Conditions
            "most_common_condition": max(set(conditions), key=conditions.count) if conditions else None,
            "condition_counts": {c: conditions.count(c) for c in set(conditions)} if conditions else {},
            # Extremes
            "extreme_temp_days": [r["measurement_date"] for r in records if r["temperature"] is not None and (r["temperature"] > 35 or r["temperature"] < 5)],
            "extreme_hum_days": [r["measurement_date"] for r in records if r["humidity"] is not None and (r["humidity"] > 90 or r["humidity"] < 20)]
        }

        return analysis


    # Export to CSV
    def export_csv(self, locality_id, days=7, filename="weather_history.csv"):
        records = self.get_last_n_days(locality_id, days)
        if not records:
            print("No records to export.")
            return
        df = pd.DataFrame(records)
        df.to_csv(filename, index=False)
        print(f"Exported {len(records)} records → {filename}")

    # Get locality by name
    def get_locality_by_name(self, name: str):
        result = (
            self.client.table("localities")
            .select("*")
            .ilike("locality_name", f"%{name}%")
            .execute()
        )
        data = result.data
        return data[0] if data else None

    def insert_locality(self, name, latitude, longitude):
        """Insert a new locality into the database."""
        self.client.table("localities").insert({
            "locality_name": name,
            "latitude": latitude,
            "longitude": longitude
        }).execute()

    def get_coordinates_from_api(self, name):
        """Fetch coordinates for a city using WeatherAPI."""
        try:
            params = {"key": WEATHER_API_KEY, "q": name}
            response = requests.get(WEATHER_API_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            lat = data["location"]["lat"]
            lon = data["location"]["lon"]
            return {"latitude": lat, "longitude": lon}
        except Exception as e:
            print(f"⚠️ Failed to get coordinates for '{name}': {e}")
            return None
        
    def get_locality_by_id(self, locality_id):
        result = self.client.table("localities").select("*").eq("locality_id", locality_id).execute()
        return result.data[0] if result.data else None