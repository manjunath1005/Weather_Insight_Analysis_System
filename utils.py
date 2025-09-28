import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

def analyze_and_plot_weather(records, locality_name):
    if not records:
        st.warning("❌ No records found for analysis.")
        return

    # --- Extract data ---
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

    # --- Print Analysis in Streamlit ---
    st.subheader(f"Weather Analysis (last {len(records)} records) for {locality_name}")
    st.markdown(f"🌡️ **Temperature** → Avg: {avg_temp:.2f}°C | Min: {min_temp}°C | Max: {max_temp}°C | Trend: {trend}")
    st.markdown(f"💧 **Humidity** → Avg: {avg_hum:.2f}% | Min: {min_hum}% | Max: {max_hum}% | Comfort: {comfort}")
    st.markdown(f"💨 **Wind Speed** → Avg: {avg_wind:.2f} kmph | Min: {min_wind} kmph | Max: {max_wind} kmph | StdDev: {std_wind:.2f} | Category: {wind_cat}")
    st.markdown(f"☔ **Rain Days** → {rain_days}/{len(records)} days had rain")

    # --- Plot Graph ---
    fig, ax = plt.subplots(figsize=(10,6))
    
    ax.plot(dates, temps, marker='o', label="Temperature (°C)")
    ax.plot(dates, hums, marker='s', label="Humidity (%)")
    ax.plot(dates, winds, marker='^', label="Wind Speed (kmph)")

    # Annotate each point with its value
    for i, (t, h, w) in enumerate(zip(temps, hums, winds)):
        ax.text(dates[i], t, f"{t:.1f}", ha='center', va='bottom', fontsize=8)
        ax.text(dates[i], h, f"{h:.1f}", ha='center', va='bottom', fontsize=8)
        ax.text(dates[i], w, f"{w:.1f}", ha='center', va='bottom', fontsize=8)

    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=30)
    ax.set_xlabel("Date")
    ax.set_ylabel("Values")
    ax.set_title(f"Weather Trends for {locality_name}")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()

    # Display in Streamlit
    st.pyplot(fig)
