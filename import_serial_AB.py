import serial
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
from Simulate_Serial import SimulatedSerial

# INIT

USE_REAL_ARDUINO = False

# --- Firebase Setup ---
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://campus-spacescout-default-rtdb.europe-west1.firebasedatabase.app/'
})

room_id = "Room101"
info_ref = db.reference(f"room_info/{room_id}")   # Static info (not touched)
session_ref = db.reference(f"sessions/{room_id}")  # Live data
log_ref = db.reference(f"logs/{room_id}")          # Session log


# --- Arduino Serial Setup ---
if USE_REAL_ARDUINO:
    PORT = 'COM3'
    BAUD_RATE = 9600
    ser = serial.Serial(PORT, BAUD_RATE)
    print(f"Connected to {PORT}, pushing to Firebase...")
else:
    ser = SimulatedSerial(delay=0.25)
    print("Running in simulation mode...")

# --- Session Reset ---
session_ref.set({
    "count": 0,
    "lastEvent": "INIT",
    "lastUpdate": datetime.now().isoformat()
})
log_ref.delete()

# --- Sensor Logic Setup ---
last_A = 0
last_B = 0
last_A_time = 0
last_B_time = 0
last_event_time = 0
DEBOUNCE = 1  # seconds
count = 0

try:
    while True:
        if ser.in_waiting:
            raw = ser.readline().decode('utf-8').strip()
            now = time.time()
            timestamp = datetime.now().isoformat()
            #print(raw)

            # Parse combined format like "A:1;B:0"
            try:
                values = dict(pair.split(":") for pair in raw.split(";"))
                A = int(values.get("A", 0))
                B = int(values.get("B", 0))
                print(f"[DEBUG] A={A}, B={B}, last_A={last_A}, last_B={last_B}")
                print(f"[DEBUG] Time since last_A={now - last_A_time:.3f}s, last_B={now - last_B_time:.3f}s")
            except Exception:
                continue  # skip malformed lines

            if A == 1 and last_B == 1 and (now - last_B_time) < DEBOUNCE and (now - last_event_time) > 1:
                count = max(count - 1, 0)
                print(f"EXIT → {count}")
                session_ref.update({
                    "count": count,
                    "lastEvent": "EXIT",
                    "lastUpdate": timestamp
                })
                log_ref.push({"timestamp": timestamp, "type": "EXIT"})
                last_event_time = now

            elif B == 1 and last_A == 1 and (now - last_A_time) < DEBOUNCE and (now - last_event_time) > 1:
                count += 1
                print(f"ENTER → {count}")
                session_ref.update({
                    "count": count,
                    "lastEvent": "ENTER",
                    "lastUpdate": timestamp
                })
                log_ref.push({"timestamp": timestamp, "type": "ENTER"})
                last_event_time = now

            last_A = A
            last_B = B
            last_A_time = now if A == 1 else last_A_time
            last_B_time = now if B == 1 else last_B_time
            # Dynamic debounce adaption
            average_trigger_gap = (now - last_A_time + now - last_B_time) / 2
            dynamic_debounce = max(0.4, min(1.5, average_trigger_gap * 0.8))
            DEBOUNCE = dynamic_debounce


except KeyboardInterrupt:
    print("Stopped.")
finally:
    ser.close()
