import time
import random

# Transition schedule in seconds for each mode
SCHEDULE = [
    ("OVERCROWDED", 300),  # 5 minutes
    ("CROWDED", 180),      # 3 minutes
    ("AVERAGE", 120),      # 2 minutes
    ("SPARSE", 120),       # 2 minutes
    ("EMPTY", 300)         # 5 minutes
]

# Smoothed transition storage
previous_values = {
    "motion": 0,
    "sound": 45.0,
    "co2": 700.0
}


def simulate_values(mode):
    if mode == "OVERCROWDED":
        motion = random.choices([0, 1], weights=[0.1, 0.9])[0]
        sound = random.gauss(65, 4)
        co2 = random.gauss(1100, 40)

    elif mode == "EMPTY":
        motion = random.choices([0, 1], weights=[0.9, 0.1])[0]
        sound = random.gauss(32, 2)
        co2 = random.gauss(420, 10)

    elif mode == "SPARSE":
        motion = random.choices([0, 1], weights=[0.85, 0.15])[0]
        sound = random.gauss(40, 5)
        co2 = random.gauss(500, 20)

    elif mode == "CROWDED":
        motion = random.choices([0, 1], weights=[0.3, 0.7])[0]
        sound = random.gauss(58, 4)
        co2 = random.gauss(950, 40)

    else:  # AVERAGE
        motion = random.choices([0, 1], weights=[0.6, 0.4])[0]
        sound = random.gauss(45 if motion == 0 else 55, 4)
        co2 = random.gauss(700 if motion == 0 else 850, 40)

    return motion, sound, co2


def smooth(val, prev, alpha=0.2):
    return alpha * val + (1 - alpha) * prev


def generate_fake_sensor_data(current_mode):
    global previous_values

    motion, sound, co2 = simulate_values(current_mode)

    # Smooth the values
    sound = smooth(sound, previous_values["sound"])
    co2 = smooth(co2, previous_values["co2"])

    # Clamp
    sound = min(max(sound, 30.0), 75.0)
    co2 = min(max(co2, 400.0), 1200.0)

    # Store for next round
    previous_values["motion"] = motion
    previous_values["sound"] = sound
    previous_values["co2"] = co2

    return f"M:{motion};S:{round(sound, 1)};C:{round(co2, 1)}"


# Generator main loop
if __name__ == "__main__":
    start = time.time()
    index = 0
    while True:
        # Change mode when schedule advances
        mode, duration = SCHEDULE[index]
        if time.time() - start > duration:
            index = (index + 1) % len(SCHEDULE)
            start = time.time()
            mode, _ = SCHEDULE[index]

        print(generate_fake_sensor_data(mode), flush=True)
        time.sleep(1)
