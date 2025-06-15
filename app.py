import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import pandas as pd
import json

# --- Firebase Setup ---
if not firebase_admin._apps:
   # for local: cred = credentials.Certificate("serviceAccountKey.json")
    cred = credentials.Certificate(dict(st.secrets["firebase"]))


    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://campus-spacescout-default-rtdb.europe-west1.firebasedatabase.app/'
    })

room_id = "Room101"
room_ref = db.reference(f"rooms/{room_id}")
room_data = room_ref.get()

# Simulated static room capacity (customize as needed)
max_capacity = 10

# --- Streamlit Layout ---
st.set_page_config(page_title="Campus Room Monitor", layout="centered")
st.title(f"📡 Room Status: {room_id}")

if room_data:
    count = room_data.get("count", 0)
    last_event = room_data.get("lastEvent", "—")
    last_update = room_data.get("lastUpdate", "—").replace("T", " ")[:19]

    # 🟦 Main Card
    st.metric(label="👥 Current Occupancy", value=f"{count} / {max_capacity}")

    # 🔴 Warning if over capacity
    if count >= max_capacity:
        st.error("⚠️ Room is full!")
    else:
        st.success("✅ Space Available")

    # 📊 Progress Bar
    st.progress(min(count / max_capacity, 1.0))

    st.write(f"**Last Event:** {last_event}")
    st.write(f"**Last Updated:** {last_update}")

else:
    st.warning("No data available for this room.")
    st.stop()

# --- OPTIONAL: ENTER / EXIT Timeline (from local CSV log or Firebase log if used) ---
# If you didn't store logs in Firebase, comment this section out or use CSV backup
events_ref = db.reference(f"events/{room_id}")
event_data = events_ref.get()

if event_data:
    # Convert to DataFrame
    events = [
        {"timestamp": v["timestamp"], "type": v["type"]}
        for k, v in event_data.items()
    ]
    df = pd.DataFrame(events)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp", ascending=False)

    # Display most recent events
    st.subheader("📜 Recent Activity")
    st.dataframe(df.head(10), use_container_width=True)

    # Plot ENTER/EXIT events over time
    df["count_change"] = df["type"].apply(lambda x: 1 if x == "ENTER" else -1)
    df["count"] = df["count_change"].cumsum()

    st.line_chart(df.set_index("timestamp")["count"])

else:
    st.info("No activity history available.")
