import matplotlib.pyplot as plt
import mplcursors
import numpy as np

def analyze_and_plot_weather(records, locality_name):
    if not records:
        print("❌ No records found for analysis.")
        return

    temps = [r["temperature"] for r in records]
    hums = [r["humidity"] for r in records]
    winds = [float(r["wind_speed"]) for r in records]
    descs = [r["description"] for r in records]
    dates = [
        r["measurement_date"].strftime("%Y-%m-%d") 
        if hasattr(r["measurement_date"], "strftime") 
        else str(r["measurement_date"]).split("T")[0]  # remove timestamp if string
        for r in records
    ]

    # --- Basic stats ---
    avg_temp, min_temp, max_temp = np.mean(temps), np.min(temps), np.max(temps)
    avg_hum, min_hum, max_hum = np.mean(hums), np.min(hums), np.max(hums)
    avg_wind, min_wind, max_wind = np.mean(winds), np.min(winds), np.max(winds)
    std_wind = np.std(winds)

    # --- Advanced Analysis ---
    slope = np.polyfit(range(len(temps)), temps, 1)[0]
    trend = "Warming" if slope > 0 else "Cooling" if slope < 0 else "Stable"

    comfort = "Dry" if avg_hum < 40 else "Comfortable" if avg_hum <= 60 else "Humid"
    wind_cat = "Calm" if avg_wind < 10 else "Moderate" if avg_wind <= 20 else "Windy"
    rain_days = sum(1 for d in descs if "rain" in d.lower())

    # --- Print Analysis ---
    print(f"\nWeather Analysis (last {len(records)} records):")
    print(f"🌡️ Temperature → Avg: {avg_temp:.2f}°C | Min: {min_temp}°C | Max: {max_temp}°C | Trend: {trend}")
    print(f"💧 Humidity    → Avg: {avg_hum:.2f}% (Min: {min_hum}%, Max: {max_hum}%) | Comfort: {comfort}")
    print(f"💨 Wind Speed  → Avg: {avg_wind:.2f} kmph | Min: {min_wind} kmph | Max: {max_wind} kmph | StdDev: {std_wind:.2f} | Category: {wind_cat}")
    print(f"☔ Rain Days   → {rain_days}/{len(records)} days had rain")

    # --- Plot Graph ---
    plt.figure(figsize=(10,6))
    plt.plot(dates, temps, marker='o', label="Temperature (°C)")
    plt.plot(dates, hums, marker='s', label="Humidity (%)")
    plt.plot(dates, winds, marker='^', label="Wind Speed (kmph)")
    plt.xticks(rotation=30)
    plt.xlabel("Date")
    plt.ylabel("Values")
    plt.title(f"Weather Trends for {locality_name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    mplcursors.cursor(hover=True)
    plt.show()