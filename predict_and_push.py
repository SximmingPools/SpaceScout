import time
import subprocess
import joblib
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from collections import deque
from datetime import datetime
import uuid

# CONFIG — change this as needed
ROOM_ID = "room01"  # 🔁 Match with one of the static sample rooms
SESSION_ID = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"  # Unique session per run

# Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://campus-spacescout-default-rtdb.europe-west1.firebasedatabase.app/'
})

# Load AI model
model = joblib.load("owl_model.pkl")

# Init rolling buffer
motion_buffer = deque(maxlen=300)
sound_buffer = deque(maxlen=300)
co2_buffer = deque(maxlen=300)

# Firebase references
session_root = db.reference(f"sessions/{ROOM_ID}/{SESSION_ID}")
live_data_ref = db.reference(f"live_data/{ROOM_ID}")

# Write session metadata
session_root.update({
    "room_id": ROOM_ID,
    "started_at": datetime.now().isoformat()
})

# Start fake serial stream (or real later)
process = subprocess.Popen(["python", "simulate_serial.py"], stdout=subprocess.PIPE, text=True)

def parse_line(line):
    try:
        parts = line.strip().split(";")
        m = int(parts[0].split(":")[1])
        s = float(parts[1].split(":")[1])
        c = float(parts[2].split(":")[1])
        return m, s, c
    except:
        return None

def predict_crowdiness(motion_rate, avg_sound, avg_co2):
    X = pd.DataFrame([{
        "motion_rate": motion_rate,
        "avg_sound": avg_sound,
        "avg_co2": avg_co2
    }])
    return round(float(model.predict(X)[0]), 3)

# --- Main loop ---
last_push = time.time()

try:
    while True:
        line = process.stdout.readline()
        parsed = parse_line(line)
        if parsed:
            m, s, c = parsed
            motion_buffer.append(m)
            sound_buffer.append(s)
            co2_buffer.append(c)

        now = time.time()
        if now - last_push >= 10 and len(motion_buffer) >= 10:
            motion_rate = sum(motion_buffer) / len(motion_buffer)
            avg_sound = sum(sound_buffer) / len(sound_buffer)
            avg_co2 = sum(co2_buffer) / len(co2_buffer)
            crowdiness = predict_crowdiness(motion_rate, avg_sound, avg_co2)

            data_point = {
                "motion_rate": round(motion_rate, 3),
                "avg_sound": round(avg_sound, 1),
                "avg_co2": round(avg_co2, 1),
                "crowdiness_index": crowdiness,
                "timestamp": datetime.now().isoformat()
            }

            # Save in session log
            timestamp_key = datetime.now().strftime("%Y%m%d%H%M%S")
            session_root.child("data").child(timestamp_key).set(data_point)

            # Update live data
            live_data_ref.set(data_point)

            print(f"🔥 Pushed to Firebase: {data_point}")
            last_push = now

except KeyboardInterrupt:
    print("🛑 Session interrupted.")
    session_root.update({
        "ended_at": datetime.now().isoformat()
    })
