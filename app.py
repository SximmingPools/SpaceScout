import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import folium_static
import firebase_admin
from firebase_admin import credentials, db
import folium
from geopy.distance import geodesic
import geocoder

# --- Firebase Setup ---
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://campus-spacescout-default-rtdb.europe-west1.firebasedatabase.app/'
    })

# --- Page Setup ---
st.set_page_config(page_title="🦉 SpaceScout", layout="wide")
st.title("🗺️ SpaceScout – Live Room Occupancy Map")

# --- Auto-refresh ---
st_autorefresh(interval=15 * 1000, key="auto_refresh")

# --- User GPS Location ---
try:
    g = geocoder.ip("me")
    user_latlng = g.latlng or [53.5665, 9.9846]
except:
    user_latlng = [53.5665, 9.9846]  # fallback

# --- Firebase References ---
rooms_ref = db.reference("rooms")
live_ref = db.reference("live_data")

rooms_data = rooms_ref.get() or {}
live_data = live_ref.get() or {}

# --- Map Init ---
m = folium.Map(location=user_latlng, zoom_start=17, control_scale=True)

# --- Add User Location ---
folium.Marker(
    location=user_latlng,
    popup="📍 You Are Here",
    icon=folium.Icon(color="blue", icon="user")
).add_to(m)

# --- Room Pins ---
for room_id, room in rooms_data.items():
    name = room.get("room_name", room_id)
    coords = room.get("location", {})
    lat, lng = coords.get("lat"), coords.get("lng")

    if not lat or not lng:
        continue

    # Get live status
    crowd = live_data.get(room_id, {}).get("crowdiness_index", None)
    status = "Offline"
    color = "gray"

    if crowd is not None:
        status = f"Crowdiness: {crowd:.2f}"
        if crowd < 0.3:
            color = "green"
        elif crowd < 0.6:
            color = "orange"
        else:
            color = "red"

    popup_html = f"""
    <b>{name}</b><br>
    <i>{status}</i><br>
    <a href="#{room_id}">View Details</a>
    """

    folium.Marker(
        location=[lat, lng],
        popup=folium.Popup(popup_html, max_width=250),
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

# --- Display Map ---
folium_static(m, width=1000, height=600)

st.markdown("---")

# --- Room Details Selector ---
selected = st.selectbox("📋 Select Room to View History", list(rooms_data.keys()))
st.subheader(f"📊 Historical Data for: {rooms_data[selected]['room_name']}")

# Optionally pull session history for selected room here...
st.info("🚧 Historical chart coming next.")
