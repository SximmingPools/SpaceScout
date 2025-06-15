import serial

PORT = 'COM3'  
BAUD_RATE = 9600

ser = serial.Serial(PORT, BAUD_RATE)
print(f"Listening on {PORT}...")

try:
    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()
            print(f"Arduino: {line}")
except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    ser.close()
