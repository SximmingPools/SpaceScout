import serial
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://campus-spacescout-default-rtdb.europe-west1.firebasedatabase.app/'
})

room_id = "Room101"
room_ref = db.reference(f"rooms/{room_id}")

# Arduino setup
PORT = 'COM3'
BAUD_RATE = 9600
ser = serial.Serial(PORT, BAUD_RATE)

print(f"Connected to {PORT}, pushing to Firebase...")

# Logic
last_A = 0
last_B = 0
last_A_time = 0
last_B_time = 0
DEBOUNCE = 0.5  # seconds
count = 0

# 🔄 Reset room data on script start
room_ref.set({
    "count": 0,
    "lastEvent": "INIT",
    "lastUpdate": datetime.now().isoformat()
})

try:
    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()
            now = time.time()
            timestamp = datetime.now().isoformat()
            print(line)

            if line.startswith("A:"):
                val = int(line.split(":")[1])
                if val == 1 and last_B == 1 and (now - last_B_time) < DEBOUNCE:
                    count = max(count - 1, 0)  # prevent negative count
                    print(f"EXIT → {count}")
                    room_ref.update({
                        "count": count,
                        "lastEvent": "EXIT",
                        "lastUpdate": timestamp
                    })
                last_A = val
                last_A_time = now

            elif line.startswith("B:"):
                val = int(line.split(":")[1])
                if val == 1 and last_A == 1 and (now - last_A_time) < DEBOUNCE:
                    count += 1
                    print(f"ENTER → {count}")
                    room_ref.update({
                        "count": count,
                        "lastEvent": "ENTER",
                        "lastUpdate": timestamp
                    })
                last_B = val
                last_B_time = now

except KeyboardInterrupt:
    print("Stopped.")
finally:
    ser.close()
