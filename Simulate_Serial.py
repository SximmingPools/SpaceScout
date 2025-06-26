import time
import random

# Choose between: "OVERCROWDED", "AVERAGE", "EMPTY", "CROWDED", "SPARSE"
MODE = "CROWDED"

def generate_fake_sensor_data():
    if MODE == "OVERCROWDED":
        motion = random.choices([0, 1], weights=[0.1, 0.9])[0]
        sound = round(random.gauss(65, 4), 1)
        co2 = round(random.gauss(1100, 40), 1)

    elif MODE == "EMPTY":
        motion = random.choices([0, 1], weights=[0.9, 0.1])[0]
        sound = round(random.gauss(32, 2), 1)
        co2 = round(random.gauss(420, 10), 1)

    elif MODE == "SPARSE":
        motion = random.choices([0, 1], weights=[0.85, 0.15])[0]
        sound = round(random.gauss(36, 3), 1)
        co2 = round(random.gauss(480, 20), 1)

    elif MODE == "CROWDED":
        motion = random.choices([0, 1], weights=[0.3, 0.7])[0]
        sound = round(random.gauss(58, 4), 1)
        co2 = round(random.gauss(950, 40), 1)

    else:  # AVERAGE
        motion = random.choices([0, 1], weights=[0.6, 0.4])[0]
        sound = round(random.gauss(45 if motion == 0 else 55, 4), 1)
        co2 = round(random.gauss(700 if motion == 0 else 850, 40), 1)

    # Clamp values
    sound = min(max(sound, 30.0), 75.0)
    co2 = min(max(co2, 400.0), 1200.0)

    return f"M:{motion};S:{sound};C:{co2}"

if __name__ == "__main__":
    while True:
        line = generate_fake_sensor_data()
        print(line, flush=True)
        time.sleep(1)
