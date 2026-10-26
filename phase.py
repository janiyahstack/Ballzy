import sys
sys.stdout.reconfigure(encoding="utf-8")
import csv
from collections import Counter, defaultdict

# --------------------------------
# 1. LOAD AND GROUP THE DATA
# --------------------------------

with open("football_events.csv", "r", newline="") as file:
    events = list(csv.DictReader(file))

phases = defaultdict(list)

for event in events:
    key = (event["match_id"], event["phase_id"])
    phases[key].append(event)

for phase in phases.values():
    phase.sort(key=lambda e: float(e["timestamp"] or 0))


# --------------------------------
# 2. HELPER FUNCTIONS
# --------------------------------

def get_movement(phase):
    return [
        event["event"]
        for event in phase
        if event["event"] in ("carry", "pass")
    ]


def get_attacking_team(phase):
    # Use the team responsible for the first
    # recorded carry or pass.
    for event in phase:
        if event["event"] in ("carry", "pass"):
            return event["team"]

    return None


def get_outcome(phase):
    event_types = [event["event"] for event in phase]

    if "goal" in event_types:
        return "goal"
    elif "shot" in event_types:
        return "shot"
    elif "turnover" in event_types:
        return "turnover"
    elif "interception" in event_types:
        return "interception"
    else:
        return "other"


def get_zone(event):
    # Use the recorded x-coordinate to identify
    # the area where a defensive event occurred.
    x = event.get("x") or event.get("start_x")

    if not x:
        return "unknown"

    x = float(x)

    if x < 40:
        return "defensive third"
    elif x < 80:
        return "middle third"
    else:
        return "attacking third"


# --------------------------------
# 3. GOAL ONE: BALL MOVEMENT
# --------------------------------

all_sequences = Counter()
all_pairs = Counter()

for phase in phases.values():

    movement = get_movement(phase)

    if movement:
        all_sequences[" → ".join(movement)] += 1

    # Count consecutive pairs of actions.
    for i in range(len(movement) - 1):
        pair = f"{movement[i]} → {movement[i + 1]}"
        all_pairs[pair] += 1


print("\n========== 1. BALL MOVEMENT ==========")

print("\nMOST COMMON MOVEMENT SEQUENCES:")

for sequence, count in all_sequences.most_common(10):
    print(f"{sequence}: {count} phases")

print("\nMOST COMMON CONSECUTIVE ACTION PAIRS:")

for pair, count in all_pairs.most_common(10):
    print(f"{pair}: {count} occurrences")


# --------------------------------
# 4. GOAL TWO: DEFENSIVE REACTIONS
# --------------------------------

defensive_events = []
defensive_zones = Counter()
defensive_context = Counter()

for phase_id, phase in phases.items():

    movement = get_movement(phase)

    for event in phase:

        if event["event"] in ("interception", "turnover"):

            defensive_events.append(event)

            defensive_zones[
                (event["event"], get_zone(event))
            ] += 1

            if movement:
                defensive_context[
                    (event["event"], movement[-1])
                ] += 1


print("\n========== 2. DEFENSIVE REACTIONS ==========")

print("\nDEFENSIVE EVENT COUNTS:")

print(Counter(
    event["event"] for event in defensive_events
))

print("\nWHERE DEFENSIVE EVENTS OCCURRED:")

for (event_type, zone), count in defensive_zones.most_common():
    print(f"{event_type} in {zone}: {count}")

print("\nMOVEMENT BEFORE DEFENSIVE EVENTS:")

for (event_type, movement), count in defensive_context.most_common():
    print(f"{movement} before {event_type}: {count}")


# --------------------------------
# 5. GOAL THREE: ATTACKING OPPORTUNITIES
# --------------------------------

phase_outcomes = Counter()
movement_by_outcome = defaultdict(Counter)

for phase_id, phase in phases.items():

    outcome = get_outcome(phase)
    movement = get_movement(phase)

    phase_outcomes[outcome] += 1

    # Count action pairs within each outcome group.
    for i in range(len(movement) - 1):
        pair = f"{movement[i]} → {movement[i + 1]}"
        movement_by_outcome[outcome][pair] += 1


print("\n========== 3. ATTACKING OPPORTUNITIES ==========")

print("\nPHASE OUTCOMES:")

for outcome, count in phase_outcomes.most_common():
    print(f"{outcome}: {count} phases")

for outcome in ("shot", "goal", "turnover"):

    print(f"\nCOMMON MOVEMENT PAIRS IN {outcome.upper()} PHASES:")

    for pair, count in movement_by_outcome[outcome].most_common(5):
        print(f"{pair}: {count}")


# --------------------------------
# 6. DATASET SUMMARY
# --------------------------------

print("\n========== DATASET SUMMARY ==========")

print("Total recorded events:", len(events))
print("Total attacking phases:", len(phases))
print("Total defensive events:", len(defensive_events))

print("\nANALYSIS COMPLETE!")
