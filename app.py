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
from PIL import Image
import os
import base64

# --- Firebase Setup ---
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://campus-spacescout-default-rtdb.europe-west1.firebasedatabase.app/'
    })

# --- Constants ---
DEFAULT_CENTER = [53.56548784525446, 9.984950800725397]  # Your presentation location

# --- Color Codes ---
def get_crowdiness_color(value):
    if value == -1:
        return "⚫"
    elif value < 0.3:
        return "🟢"
    elif value < 0.6:
        return "🟠"
    else:
        return "🔴"

# --- Page Setup ---
st.set_page_config(page_title="🦉 SpaceScout", layout="centered")
st.title("🗺️ SpaceScout – Live Room Occupancy Map")
st_autorefresh(interval=15 * 1000, key="auto_refresh")

# --- Background Image ---

def set_bg_image_local(img_path):
    with open(img_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
set_bg_image_local("resources/Background.png")


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


# --- Nav Header ---
with st.container():
    st.markdown("#### 🔗 Quick Access")
    col1, col2, col3 = st.columns(3)
    col1.markdown("[🗺️ Map](#interactive-map-view)")
    col2.markdown("[📊 Stats](#session-statistics)")
    col3.markdown("[📂 Raw Data](#raw-historical-data)")


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
st.subheader("📡 Real-Time Room Radar")
st.markdown("Pick a room to scout 👇")

if "room_info_expanded" not in st.session_state:
    st.session_state.room_info_expanded = {}

for room in room_entries:
    color_emoji = get_crowdiness_color(room['crowdiness'])
    crowdiness_label = f"{color_emoji} {room['crowdiness']:.0%}" if room['crowdiness'] != -1 else "⚫ Offline"
    row_style = "color: grey;" if room['crowdiness'] == -1 else ""

    with st.container():
        cols = st.columns([6, 1])
        with cols[0]:
            st.markdown(
                f"<div style='display: flex; justify-content: space-between; align-items: center; {row_style}'>"
                f"<span><strong>{room['name']}</strong> — {room['distance']} km — Crowdiness: {crowdiness_label}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        with cols[1]:
            if st.button("🔍 View", key=f"view_{room['id']}"):
                if st.session_state.room_info_expanded.get(room['id']):
                    # Collapse the currently open room
                    st.session_state.room_info_expanded = {}
                else:
                    # Collapse all and expand only this one
                    st.session_state.room_info_expanded = {room['id']: True}
                    set_selected_room(room['id'])

        # Show room details if selected
        if st.session_state.room_info_expanded.get(room['id']):
            # Room Image
            image_path = f"resources/{room['id']}.jpg"
            if os.path.exists(image_path):
                st.image(image_path, caption=f"{room['name']}", use_column_width=True)
            else:
                st.info("📸 Room image not available.")

            # Capacity + Estimated People
            if "capacity" in rooms_data[room["id"]]:
                capacity = rooms_data[room["id"]]["capacity"]
                if room["crowdiness"] != -1:
                    est_people = int(capacity * room["crowdiness"])
                    st.metric("👥 Estimated People Inside", f"{est_people} / {capacity}")
                else:
                    st.markdown(f"👥 Capacity: **{capacity}** — Room is currently offline.")
            # Details
            def get_status_bar(value):
                if value < 0.3:
                    return "🟩 Low"
                elif value < 0.6:
                    return "🟧 Medium"
                else:
                    return "🟥 High"

            st.markdown(f"**Current Crowdiness Level:** {get_status_bar(room['crowdiness'])}")
            # --- Room Meta Info ---
            room_meta = rooms_data[room["id"]]
            building = room_meta.get("building", "Unknown Building")
            floor = room_meta.get("floor", "Unknown Floor")
            rtype = room_meta.get("type", "Unknown Type")
            st.markdown(f"🏢 **Building**: {building} &nbsp;&nbsp; 🧭 **Floor**: {floor} &nbsp;&nbsp; 🪑 **Type**: {rtype}")

            st.markdown("---")

# Ensure correct selection persists
selected_room = next(r for r in room_entries if r['id'] == st.session_state.selected_room_id)

# --- Build Map ---
m = folium.Map(location=[selected_room["lat"], selected_room["lng"]], zoom_start=19, control_scale=True)
st.markdown("<a name='interactive-map-view'></a>", unsafe_allow_html=True)
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
st.markdown("---")
st.markdown("### 🗺️ Interactive Map View")

folium_static(m, width=1000, height=600)


# --- Historical Session Data Viewer ---
import matplotlib.pyplot as plt

st.markdown("<a name='raw-historical-data'></a>", unsafe_allow_html=True)
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
        
       # Select Box (filter)
        time_filter = st.selectbox("⏱️ Show Data From", ["Last 10 min", "Last 30 min", "All"])
        now = pd.Timestamp.now()
        if time_filter == "Last 10 min":
            df = df[df["timestamp"] >= now - pd.Timedelta(minutes=10)]
        elif time_filter == "Last 30 min":
            df = df[df["timestamp"] >= now - pd.Timedelta(minutes=30)]

        df["crowdiness_percent"] = df["crowdiness_index"]
        df["smoothed_percent"] = df["smoothed"]

        # Session Stats
        st.markdown("<a name='session-statistics'></a>", unsafe_allow_html=True)
        st.markdown("### 📈 Session Statistics")
        col1, col2, col3 = st.columns(3)
        col1.metric("📉 Min", f"{df['crowdiness_index'].min():.0%}")
        col2.metric("📈 Max", f"{df['crowdiness_index'].max():.0%}")
        col3.metric("📊 Avg", f"{df['crowdiness_index'].mean():.0%}")

        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X("time_label:N", title="Time"),
            y=alt.Y("crowdiness_percent:Q", title="Crowdiness", axis=alt.Axis(format=".0%")),
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

