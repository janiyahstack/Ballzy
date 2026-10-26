import csv
from collections import Counter

with open("football_events.csv", "r", newline="") as file:
    events = list(csv.DictReader(file))

print("TOTAL EVENTS:", len(events))

print("\nEVENT TYPES:")
print(Counter(event["event"] for event in events))

print("\nPASS OUTCOMES:")
print(Counter(
    event["outcome"]
    for event in events
    if event["event"] == "pass"
))

print("\nFIRST 10 EVENTS:")
for event in events[:10]:
    print(event)