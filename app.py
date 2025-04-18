import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

API_KEY = "qptnmqsehc5aakyfk99t62gcrudkc7ez"

@st.cache_data(ttl=60)
def get_devices():
    url = "https://aranet.cloud/api/devices"
    headers = {"ApiKey": API_KEY}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        st.error("Failed to fetch devices.")
        return []
    return r.json()

@st.cache_data(ttl=10)
def get_latest_measurement(device_id):
    url = f"https://aranet.cloud/api/devices/{device_id}/latest"
    headers = {"ApiKey": API_KEY}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None
    return r.json()

def color_status(value):
    if value > 100:
        return [0, 200, 0]      # Green = OK
    elif value > 50:
        return [255, 165, 0]    # Orange = Warning
    else:
        return [255, 0, 0]      # Red = Problem

st.set_page_config(page_title="Aranet Weights", layout="wide")
st.title("📦 Aranet Weight Scale Map")

devices = get_devices()
data_rows = []

for device in devices:
    latest = get_latest_measurement(device["id"])
    if not latest:
        continue

    measurement = latest.get("measurement", {})
    value = measurement.get("value", None)
    if value is None:
        continue

    location = device.get("location", {})
    lat, lon = location.get("latitude"), location.get("longitude")

    if lat is None or lon is None:
        continue

    data_rows.append({
        "name": device["name"],
        "value": value,
        "lat": lat,
        "lon": lon,
        "color": color_status(value)
    })

df = pd.DataFrame(data_rows)

if df.empty:
    st.warning("No data available or no devices with location.")
else:
    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(
            latitude=df["lat"].mean(),
            longitude=df["lon"].mean(),
            zoom=12,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[lon, lat]',
                get_fill_color="color",
                get_radius=100,
                pickable=True,
            )
        ],
        tooltip={"text": "{name}: {value}kg"}
    ))

    st.dataframe(df[["name", "value"]])
