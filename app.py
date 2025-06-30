import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import folium_static
import firebase_admin
from firebase_admin import credentials, db
import folium
from geopy.distance import geodesic
import pandas as pd
from streamlit_js_eval import streamlit_js_eval
import altair as alt

# --- Firebase Setup ---
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://campus-spacescout-default-rtdb.europe-west1.firebasedatabase.app/'
    })

# --- Constants ---
DEFAULT_CENTER = [53.56548784525446, 9.984950800725397]  # Your presentation location

# --- Page Setup ---
st.set_page_config(page_title="🦉 SpaceScout", layout="wide")
st.title("🗺️ SpaceScout – Live Room Occupancy Map")
st_autorefresh(interval=15 * 1000, key="auto_refresh")

# --- Get user location from browser ---
loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition((pos) => { return { latitude: pos.coords.latitude, longitude: pos.coords.longitude }; })", key="get_user_location")
if loc and loc.get("latitude") and loc.get("longitude"):
    user_latlng = [loc["latitude"], loc["longitude"]]
else:
    user_latlng = DEFAULT_CENTER

# --- Firebase Refs ---
rooms_ref = db.reference("rooms")
live_ref = db.reference("live_data")
rooms_data = rooms_ref.get() or {}
live_data = live_ref.get() or {}

# --- Build room list with metadata ---
room_entries = []
for room_id, room in rooms_data.items():
    name = room.get("room_name", room_id)
    coords = room.get("location", {})
    lat, lng = coords.get("lat"), coords.get("lng")
    if not lat or not lng:
        continue

    crowd = live_data.get(room_id, {}).get("crowdiness_index")
    dist_km = round(geodesic(user_latlng, [lat, lng]).km, 2)

    room_entries.append({
        "id": room_id,
        "name": name,
        "lat": lat,
        "lng": lng,
        "crowdiness": crowd if crowd is not None else -1,
        "distance": dist_km
    })

# --- Sort by crowdiness then distance ---
room_entries.sort(key=lambda x: (x['crowdiness'] if x['crowdiness'] != -1 else 999, x['distance']))

# --- Room Selection Logic ---
if "selected_room_id" not in st.session_state:
    st.session_state.selected_room_id = room_entries[0]["id"] if room_entries else None

# --- Update selection based on button click ---
def set_selected_room(room_id):
    st.session_state.selected_room_id = room_id

# --- Room Selection UI ---
st.subheader("📍 Nearby Rooms")
for room in room_entries:
    crowdiness_label = f"{room['crowdiness']:.2f}" if room['crowdiness'] != -1 else "Offline"
    with st.container():
        cols = st.columns([6, 1])
        with cols[0]:
            st.markdown(
                f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
                f"<span><strong>{room['name']}</strong> — {room['distance']} km — Crowdiness: {crowdiness_label}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        with cols[1]:
            if st.button("View", key=f"view_{room['id']}"):
                set_selected_room(room['id'])

selected_room = next(r for r in room_entries if r['id'] == st.session_state.selected_room_id)

# --- Build Map ---
m = folium.Map(location=[selected_room["lat"], selected_room["lng"]], zoom_start=19, control_scale=True)

# User marker
folium.Marker(
    location=user_latlng,
    popup="📍 You Are Here",
    icon=folium.Icon(color="blue", icon="user")
).add_to(m)

# Room markers
for room in room_entries:
    color = "gray"
    if room['crowdiness'] != -1:
        if room['crowdiness'] < 0.3:
            color = "green"
        elif room['crowdiness'] < 0.6:
            color = "orange"
        else:
            color = "red"

    popup_html = f"""
    <b>{room['name']}</b><br>
    Distance: {room['distance']} km<br>
    Crowdiness: {room['crowdiness'] if room['crowdiness'] != -1 else 'Offline'}<br>
    """

    folium.Marker(
        location=[room['lat'], room['lng']],
        popup=folium.Popup(popup_html, max_width=250),
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

# --- Show Map ---
folium_static(m, width=1000, height=600)

# --- Room Data Section ---
st.subheader(f"📊 Details for: {selected_room['name']}")

# --- Historical Session Data Viewer ---
import matplotlib.pyplot as plt

session_ref = db.reference(f"sessions/{selected_room['id']}")
sessions = session_ref.get() or {}

if sessions:
    latest_key = sorted(sessions.keys())[-1]
    data = sessions[latest_key].get("data", {})

    if data:
        df = pd.DataFrame(data.values())
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["time_label"] = df["timestamp"].dt.strftime("%H:%M:%S")

        df = df.sort_values("timestamp")
        df["smoothed"] = df["crowdiness_index"].rolling(window=3, min_periods=1).mean()
        st.markdown("### ⏳ Crowdiness Over Time")

        st.markdown("### ⏳ Crowdiness Over Time")

        df["crowdiness_percent"] = df["crowdiness_index"] * 100
        df["smoothed_percent"] = df["smoothed"] * 100

        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X("time_label:N", title="Time"),
            y=alt.Y("crowdiness_percent:Q", title="Crowdiness", axis=alt.Axis(format="%")),
            tooltip=[
                alt.Tooltip("time_label:N", title="Time"),
                alt.Tooltip("crowdiness_percent:Q", title="Crowdiness", format=".1f"),
                alt.Tooltip("smoothed_percent:Q", title="Smoothed", format=".1f")
            ]
        ).properties(width=700, height=300)

        st.altair_chart(chart, use_container_width=True)

        with st.expander("📂 Raw Historical Data", expanded=False):
            st.dataframe(df[["timestamp", "motion_rate", "avg_sound", "avg_co2", "crowdiness_index"]])
    else:
        st.warning("⚠️ No session data found for this room.")
else:
    st.warning("⚠️ No session history available.")

