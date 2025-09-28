import streamlit as st
import pandas as pd
from supabase_client import SupabaseDB
from weather_api import WeatherAPI
from utils import analyze_and_plot_weather
from datetime import datetime

# --- Initialize DB ---
db = SupabaseDB()

st.set_page_config(page_title="Weather Insight & Analysis", layout="wide")
st.title("🌤 Weather Insight & Analysis System")

# --- Sidebar Menu ---
menu = ["Fetch & Store Today’s Weather", "View Last 7 Days History", "Analyze Weather Trends", "Export History to CSV"]
choice = st.sidebar.selectbox("Select Option", menu)

# --- Fetch & Store ---
if choice == menu[0]:
    st.subheader("Fetch & Store Today's Weather")
    locality_name = st.text_input("Enter locality name")
    
    if st.button("Fetch & Store"):
        if not locality_name.strip():
            st.error("Please enter a locality name")
        else:
            locality = db.get_locality_by_name(locality_name.strip())
            
            if not locality:
                coords = db.get_coordinates_from_api(locality_name.strip())
                if coords:
                    db.insert_locality(locality_name.strip(), coords["latitude"], coords["longitude"])
                    locality = db.get_locality_by_name(locality_name.strip())
                    st.success(f"Added new locality: {locality_name}")
                else:
                    st.error("Could not fetch locality. Aborting.")
                    st.stop()
            
            st.success(f"Found locality: {locality['locality_name']} (ID: {locality['locality_id']})")
            
            try:
                temp, hum, desc, wind = WeatherAPI.get_weather(locality["latitude"], locality["longitude"])
            except Exception as e:
                st.warning(f"Error fetching weather: {e}")
                temp, hum, desc, wind = None, None, None, None
            
            db.insert_weather(locality_id=locality["locality_id"], temperature=temp,
                              humidity=hum, description=desc, wind_speed=wind)
            
            st.write(f"🌡 Temperature: {temp}°C | 💧 Humidity: {hum}% | 💨 Wind: {wind} kph | Condition: {desc}")
            st.success("Weather data stored successfully!")

# --- View History ---
elif choice == menu[1]:
    st.subheader("View Last N Days History")
    locality_name = st.text_input("Enter locality name")
    days = st.number_input("Enter number of past days", min_value=1, max_value=30, value=7, step=1)
    
    if st.button("View History"):
        locality = db.get_locality_by_name(locality_name.strip())
        if not locality:
            st.error("Locality not found")
        else:
            records = db.get_last_n_days(locality["locality_id"], days=days)
            if not records:
                st.warning("No records found")
            else:
                # Format dates
                for r in records:
                    if isinstance(r["measurement_date"], str):
                        r["measurement_date"] = r["measurement_date"].split("T")[0]
                
                df = pd.DataFrame(records)
                st.dataframe(df)

# --- Analyze Trends ---
elif choice == menu[2]:
    st.subheader("Analyze Weather Trends")
    locality_name = st.text_input("Enter locality name")
    
    if st.button("Analyze"):
        locality = db.get_locality_by_name(locality_name.strip())
        if not locality:
            st.error("Locality not found")
        else:
            records = db.get_last_n_days(locality["locality_id"], days=7)
            if not records:
                st.warning("No records found")
            else:
                import pandas as pd

                df = pd.DataFrame(records)

                # --- Fix measurement_date ---
                df["measurement_date"] = pd.to_datetime(df["measurement_date"], errors="coerce")

                # --- Keep only the latest record per date ---
                df = df.sort_values("measurement_date").drop_duplicates(
                    subset="measurement_date", keep="last"
                )

                # --- Ensure continuous 7-day range ---
                start_date = df["measurement_date"].min()
                full_range = pd.date_range(start=start_date, periods=7, freq="D")
                
                # Merge to fill missing dates
                full_df = pd.DataFrame({"measurement_date": full_range})
                df = full_df.merge(df, on="measurement_date", how="left")

                # Forward/backward fill for missing data
                for col in ["temperature", "humidity", "description", "wind_speed", "locality_id", "weather_id"]:
                    if col in df.columns:
                        df[col] = df[col].ffill().bfill()

                # --- Call analysis & plotting function ---
                analyze_and_plot_weather(df.to_dict(orient="records"), locality["locality_name"])

                st.success("Analysis complete! Check the plots above.")


# --- Export CSV ---
elif choice == menu[3]:
    st.subheader("Export History to CSV")
    locality_name = st.text_input("Enter locality name")
    days = st.number_input("Number of past days to export", min_value=1, max_value=30, value=7, step=1)
    
    if st.button("Export CSV"):
        locality = db.get_locality_by_name(locality_name.strip())
        if not locality:
            st.error("Locality not found")
        else:
            records = db.get_last_n_days(locality["locality_id"], days=days)
            if not records:
                st.warning("No records found")
            else:
                df = pd.DataFrame(records)
                df["measurement_date"] = pd.to_datetime(df["measurement_date"], errors="coerce")
                df["measurement_date"] = df["measurement_date"].dt.strftime("%Y-%m-%d")

                # Columns for summary (exclude IDs and description)
                numeric_cols = ["temperature", "humidity", "wind_speed"]

                avg_row = df[numeric_cols].mean()
                avg_row["measurement_date"] = "Average"

                min_row = df[numeric_cols].min()
                min_row["measurement_date"] = "Minimum"

                max_row = df[numeric_cols].max()
                max_row["measurement_date"] = "Maximum"

                # Add empty description + IDs for clarity
                for row in [avg_row, min_row, max_row]:
                    row["description"] = ""
                    row["weather_id"] = ""
                    row["locality_id"] = ""

                df = pd.concat([df, pd.DataFrame([avg_row, min_row, max_row])], ignore_index=True)

                # Prepare for download
                filename = f"{locality['locality_name']}_history.csv"
                csv_data = df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
                st.success(f"✅ Exported {len(records)} records + summary")

