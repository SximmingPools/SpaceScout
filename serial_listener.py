import subprocess
import sys
import pandas as pd
import time
from datetime import datetime
from collections import deque

# Rolling buffer (5 minutes at 1Hz = 300 entries)
BUFFER_SECONDS = 300
READ_INTERVAL = 1
AGGREGATE_EVERY = 10  # seconds

motion_buffer = deque(maxlen=BUFFER_SECONDS)
sound_buffer = deque(maxlen=BUFFER_SECONDS)
co2_buffer = deque(maxlen=BUFFER_SECONDS)

def parse_line(line):
    try:
        parts = line.strip().split(";")
        m = int(parts[0].split(":")[1])
        s = float(parts[1].split(":")[1])
        c = float(parts[2].split(":")[1])
        return m, s, c
    except:
        return None

def estimate_crowdiness(motion_rate, avg_sound, avg_co2):
    # Normalize all to 0–1
    m_norm = motion_rate
    s_norm = (avg_sound - 30) / (75 - 30)  # 30–75 dB
    c_norm = (avg_co2 - 400) / (1200 - 400)  # 400–1200 ppm

    # Weighted average (tweak weights if needed)
    return round((0.4 * m_norm + 0.3 * s_norm + 0.3 * c_norm), 3)

def main():
    # Launch the simulation script
    process = subprocess.Popen([sys.executable, "simulate_serial.py"], stdout=subprocess.PIPE, text=True)

    last_aggregation = time.time()
    dataset = []

    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break

            parsed = parse_line(line)
            if parsed:
                m, s, c = parsed
                motion_buffer.append(m)
                sound_buffer.append(s)
                co2_buffer.append(c)

            now = time.time()
            if now - last_aggregation >= AGGREGATE_EVERY and len(motion_buffer) >= 10:
                motion_rate = sum(motion_buffer) / len(motion_buffer)
                avg_sound = sum(sound_buffer) / len(sound_buffer)
                avg_co2 = sum(co2_buffer) / len(co2_buffer)
                crowdiness = estimate_crowdiness(motion_rate, avg_sound, avg_co2)

                row = {
                    "timestamp": datetime.now().isoformat(),
                    "motion_rate": round(motion_rate, 3),
                    "avg_sound": round(avg_sound, 1),
                    "avg_co2": round(avg_co2, 1),
                    "crowdiness_index": crowdiness
                }
                dataset.append(row)
                print(row)
                last_aggregation = now

    except KeyboardInterrupt:
        print("Stopped. Appending to CSV...")
        
        #   Save collected dataset (append if file exists)
        csv_file = "crowdiness_dataset.csv"
        try:
            df_existing = pd.read_csv(csv_file)
            df_combined = pd.concat([df_existing, pd.DataFrame(dataset)], ignore_index=True)
        except FileNotFoundError:
            df_combined = pd.DataFrame(dataset)

        df_combined.to_csv(csv_file, index=False)
        print(f"✅ Appended {len(dataset)} rows. Total rows now: {len(df_combined)}")


if __name__ == "__main__":
    main()
