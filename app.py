import streamlit as st
from streamlit_autorefresh import st_autorefresh
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import pandas as pd
import json
# --- Firebase Setup ---
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://campus-spacescout-default-rtdb.europe-west1.firebasedatabase.app/'
    })

# --- Page Setup ---
st.set_page_config(page_title="📡 Campus Room Monitor", layout="centered")
st.title("📡 Campus Room Monitor")

# --- Room Selector ---
room_ids_ref = db.reference("sessions")
available_rooms = list(room_ids_ref.get() or {})

if not available_rooms:
    st.warning("No rooms found in database.")
    st.stop()

room_id = st.selectbox("🏠 Select Room", available_rooms)

# --- Data Refs ---
session_ref = db.reference(f"sessions/{room_id}")
info_ref = db.reference(f"room_info/{room_id}")
log_ref = db.reference(f"logs/{room_id}")

# --- Live Updates ---
st_autorefresh(interval=10 * 1000, key="auto-refresh")

# --- Fetch Room Data ---
session_data = session_ref.get()
info_data = info_ref.get()

# --- Room Capacity ---
max_capacity = info_data.get("max_capacity", 10) if info_data else 10

if session_data:
    count = session_data.get("count", 0)
    last_event = session_data.get("lastEvent", "—")
    last_update = session_data.get("lastUpdate", "—").replace("T", " ")[:19]

    # 🟦 Main Card
    st.metric(label="👥 Current Occupancy", value=f"{count} / {max_capacity}")

    # 🔴 Capacity Alert
    if count >= max_capacity:
        st.error("🚫 Room is full!")
    else:
        st.success("✅ Space Available")

    # 📊 Capacity Progress
    st.progress(min(count / max_capacity, 1.0))

    st.write(f"**🕒 Last Event:** {last_event}")
    st.write(f"**📅 Last Updated:** {last_update}")
else:
    st.warning("⚠️ No session data for this room.")
    st.stop()

# --- Event Log & Visualization ---
event_data = log_ref.get()

if event_data:
    events = [
        {"timestamp": v["timestamp"], "type": v["type"]}
        for k, v in event_data.items()
    ]
    df = pd.DataFrame(events)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # Crowdiness over time
    df["count_change"] = df["type"].apply(lambda x: 1 if x == "ENTER" else -1)
    df["count"] = df["count_change"].cumsum()

    st.subheader("📈 Room Usage Over Time")
    st.line_chart(df.set_index("timestamp")["count"])

    # Log-style event table
    st.subheader("📜 Recent Activity Log")
    df_display = df.sort_values("timestamp", ascending=False).head(10)
    df_display["timestamp"] = df_display["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(df_display, use_container_width=True)

else:
    st.info("ℹ️ No activity history available.")
