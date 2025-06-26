import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import folium_static
import firebase_admin
from firebase_admin import credentials, db
import folium
from geopy.distance import geodesic
import pandas as pd
from streamlit_js_eval import get_geolocation

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
loc = get_geolocation()
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

# --- Room Selection UI ---
selected_room_id = st.selectbox("📋 Select Room", [r["id"] for r in room_entries], format_func=lambda x: next(r['name'] for r in room_entries if r['id'] == x))
selected_room = next(r for r in room_entries if r['id'] == selected_room_id)

# --- Info List ---
st.subheader("📍 Nearby Rooms")
for room in room_entries:
    crowdiness_label = f"{room['crowdiness']:.2f}" if room['crowdiness'] != -1 else "Offline"
    st.markdown(f"**{room['name']}** — {room['distance']} km — Crowdiness: {crowdiness_label}")

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
    <a href='#' onclick=\"window.location.search='?room={room['id']}'\">View Details</a>
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
st.info("📈 Historical data and trends coming soon.")
