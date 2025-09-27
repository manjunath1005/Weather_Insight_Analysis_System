from supabase_client import SupabaseDB
from weather_api import WeatherAPI
from utils import analyze_and_plot_weather
import datetime
from datetime import datetime, timedelta
import pandas as pd

class WeatherApp:
    def __init__(self):
        self.db = SupabaseDB()

    def fetch_and_store(self):
        name = input("Enter locality name: ").strip()
        locality = self.db.get_locality_by_name(name)

        # Step 1: If locality not in DB, fetch coordinates from API
        if not locality:
            print(f"ℹ️ Locality '{name}' not found in DB. Trying to fetch from API...")
            coords = self.db.get_coordinates_from_api(name)
            if coords:
                self.db.insert_locality(name, coords["latitude"], coords["longitude"])
                locality = self.db.get_locality_by_name(name)
                print(f"✅ Added new locality: {name}")
            else:
                print("❌ Could not fetch locality. Aborting.")
                return

        print(f"✅ Found locality: {locality['locality_name']} (City ID: {locality['locality_id']})")

        # Step 2: Fetch weather for the locality
        try:
            temperature, humidity, condition, wind = WeatherAPI.get_weather(
                locality["latitude"], locality["longitude"]
            )
            print(f"🌤️ {condition} | 🌡️ {temperature}°C | 💨 {wind} kmph |💧 {humidity}%")
        except Exception as e:
            print(f"⚠️ Error fetching weather: {e}")
            temperature, humidity, condition, wind = None, None, None, None

        # Step 3: Insert weather data into DB (include wind_speed)
        self.db.insert_weather(
            locality_id=locality["locality_id"],
            temperature=temperature,
            humidity=humidity,
            description=condition,
            wind_speed=wind
        )

        print("Weather data stored successfully.")

    def view_history(self):
        name = input("Enter locality name: ").strip()
        locality = self.db.get_locality_by_name(name)

        if not locality:
            print("❌ Locality not found.")
            return

        days_input = input("Enter number of past days to view: ").strip()
        days = int(days_input) if days_input.isdigit() else 7

        data = self.db.get_last_n_days(locality["locality_id"], days=days)
        print(f"Last {days} days history for {locality['locality_name']}:")

        for row in data:
            # convert to datetime if it's string
            date_val = row["measurement_date"]
            if isinstance(date_val, str):
                try:
                    date_val = datetime.fromisoformat(date_val)
                except ValueError:
                    # fallback: just keep as string
                    date_val = date_val.split("T")[0]
            
            print(f"{date_val if isinstance(date_val, str) else date_val.strftime('%Y-%m-%d %H:%M')} | "
                f"{row['temperature']}°C | {row['humidity']}% | {row['wind_speed']} kmph | {row['description']}")

    def analyze_trends(self):
        name = input("Enter locality name: ").strip()
        locality = self.db.get_locality_by_name(name)

        if not locality:
            print("❌ Locality not found.")
            return

        records = self.db.get_last_n_days(locality["locality_id"], days=7)
        analyze_and_plot_weather(records, locality["locality_name"])

    def export_csv(self):
        name = input("Enter locality name: ").strip()
        locality = self.db.get_locality_by_name(name)

        if not locality:
            print("❌ Locality not found.")
            return

        days_input = input("Enter number of past days to export (default 7): ").strip()
        days = int(days_input) if days_input.isdigit() else 7

        filename = f"{locality['locality_name']}_history.csv"

        # Fetch records
        records = self.db.get_last_n_days(locality["locality_id"], days=days)
        if not records:
            print("❌ No records found to export.")
            return

        df = pd.DataFrame(records)

        # Clean date format
        df["measurement_date"] = pd.to_datetime(df["measurement_date"], errors="coerce")
        df["measurement_date"] = df["measurement_date"].dt.strftime("%Y-%m-%d")

        # summary rows
        avg_row = df.mean(numeric_only=True)
        avg_row["measurement_date"] = "Average"

        min_row = df.min(numeric_only=True)
        min_row["measurement_date"] = "Minimum"

        max_row = df.max(numeric_only=True)
        max_row["measurement_date"] = "Maximum"

        # Keep description empty for summary rows
        for row in [avg_row, min_row, max_row]:
            row["description"] = ""

        df = pd.concat([df, pd.DataFrame([avg_row, min_row, max_row])], ignore_index=True)

        df.to_csv(filename, index=False)
        print(f"📂 Exported {len(records)} records + summary → {filename}")

    def run(self):
        while True:
            print("\n=== Weather Insight & Analysis System ===")
            print("1. Fetch & Store Today’s Weather")
            print("2. View Last 7 Days History")
            print("3. Analyze Weather Trends")
            print("4. Export History to CSV")
            print("5. Exit")

            choice = input("Enter choice: ").strip()

            if choice == "1":
                self.fetch_and_store()
            elif choice == "2":
                self.view_history()
            elif choice == "3":
                self.analyze_trends()
            elif choice == "4":
                self.export_csv()
            elif choice == "5":
                print("👋 Exiting...")
                break
            else:
                print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    app = WeatherApp()
    app.run()

