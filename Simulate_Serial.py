import time
import random

class SimulatedSerial:
    def __init__(self, delay=0.2):
        self.delay = delay
        self.state = {"A": 0, "B": 0}
        self.sticky_timer = {"A": 0, "B": 0}

    def readline(self):
        time.sleep(self.delay)

        for sensor in ["A", "B"]:
            # If sensor is active and timer is still running, keep it at 1
            if self.state[sensor] == 1 and self.sticky_timer[sensor] > 0:
                self.sticky_timer[sensor] -= 1
                continue

            roll = random.random()

            if self.state[sensor] == 0:
                # If A is active, increase the chance for B to simulate "ENTRY"
                if sensor == "B" and self.state["A"] == 1:
                    chance_to_trigger = 0.5
                else:
                    chance_to_trigger = 0.2

                if roll < chance_to_trigger:
                    self.state[sensor] = 1
                    self.sticky_timer[sensor] = random.randint(1, 3)

            else:
                # 30% chance to go back to 0
                if roll < 0.3:
                    self.state[sensor] = 0

        line = f"A:{self.state['A']};B:{self.state['B']}\n"
        return line.encode("utf-8")

    @property
    def in_waiting(self):
        return True

    def close(self):
        print("Simulated serial connection closed.")
