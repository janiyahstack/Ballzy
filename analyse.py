
import csv
from collections import Counter

with open("football_events.csv", "r", newline="") as file:
    events = list(csv.DictReader(file))

print("TOTAL EVENTS:", len(events))

print("\nEVENT TYPES:")
print(Counter(event["event"] for event in events))

print("\nSAMPLE ATTACKING PHASES:")

shown = set()

for event in events:
    phase = event["phase_id"]

    if phase not in shown:
        print("\nPHASE:", phase)

        for item in events:
            if item["phase_id"] == phase:
                print(
                    item["event"],
                    item["team"],
                    item["player"],
                    item["outcome"]
                )

        shown.add(phase)

    if len(shown) == 3:
        break
