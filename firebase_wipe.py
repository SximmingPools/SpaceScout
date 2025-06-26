import firebase_admin
from firebase_admin import credentials, db

# Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://campus-spacescout-default-rtdb.europe-west1.firebasedatabase.app/'
})

# Wipe old data
print("🔥 Wiping Firebase...")

for path in ["rooms", "sessions", "live_data", "logs"]:
    db.reference(path).delete()
    print(f"Deleted: {path}/")

# Insert sample rooms
print("📦 Inserting sample rooms...")

sample_rooms = {
    "room01": {
        "room_name": "Digital Innovation Lab",
        "building": "Campus West",
        "capacity": 20,
        "floor": 3,
        "type": "seminar",
        "location": {"lat": 53.5665, "lng": 9.9846}
    },
    "room02": {
        "room_name": "Library Silent Zone",
        "building": "Central Library",
        "capacity": 50,
        "floor": 2,
        "type": "study",
        "location": {"lat": 53.5672, "lng": 9.9839}
    },
    "room03": {
        "room_name": "West Wing Seminar Room",
        "building": "Campus West",
        "capacity": 15,
        "floor": 1,
        "type": "seminar",
        "location": {"lat": 53.5668, "lng": 9.9852}
    }
}

db.reference("rooms").set(sample_rooms)

print("✅ Firebase reset complete with 3 sample rooms.")
