import serial
import csv
from datetime import datetime

PORT = 'COM3'   # Update if needed
BAUD_RATE = 9600
OUTPUT_FILE = 'motion_log.csv'

# Connect to Arduino
ser = serial.Serial(PORT, BAUD_RATE)
print(f"Connected to {PORT}, logging to {OUTPUT_FILE}...")

# Open CSV file and write headers
with open(OUTPUT_FILE, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "MotionState"])

    try:
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] {line}")
                writer.writerow([timestamp, line])
    except KeyboardInterrupt:
        file.flush()
        print("\nStopped logging.")
    finally:
        ser.close()
j