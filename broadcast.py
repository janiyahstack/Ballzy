
import csv
import json
from collections import defaultdict, Counter

# 1. LOAD THE DATASET

with open("football_events.csv", "r", newline="") as file:
    events = list(csv.DictReader(file))

# 2. GROUP EVENTS INTO ATTACKING PHASES

phases = defaultdict(list)

for event in events:
    key = (event["match_id"], event["phase_id"])
    phases[key].append(event)

for phase in phases.values():
    phase.sort(key=lambda e: float(e.get("timestamp") or 0))


# 3. HELPER FUNCTIONS

def movement_sequence(phase, stop_event):
    movements = []

    for event in phase:
        if event["event"] == stop_event:
            break

        if event["event"] in ("carry", "pass"):
            movements.append(event["event"])

    return movements


def last_movement(phase, stop_events):
    for event in reversed(phase):
        if event["event"] in ("carry", "pass"):
            return event["event"]

        if event["event"] in stop_events:
            return None

    return None


# 4. ANALYSE SHOT PHASES AND DEFENSIVE DISRUPTIONS

shot_patterns = Counter()
defensive_preceding_movements = Counter()

shot_phases = 0
goal_phases = 0
disrupted_phases = 0

for phase in phases.values():

    event_types = [e["event"] for e in phase]

    # Attacking opportunities
    if "shot" in event_types:
        shot_phases += 1

        movements = movement_sequence(phase, "shot")

        for i in range(len(movements) - 1):
            pair = movements[i] + " -> " + movements[i + 1]
            shot_patterns[pair] += 1

    if "goal" in event_types:
        goal_phases += 1

    # Defensive disruptions
    disruption = next(
        (
            e for e in phase
            if e["event"] in ("interception", "turnover")
        ),
        None
    )

    if disruption:
        disrupted_phases += 1

        previous = last_movement(
            phase,
            {"interception", "turnover"}
        )

        if previous:
            defensive_preceding_movements[previous] += 1


# 5. GENERATE BROADCAST EXPLANATIONS

most_common_shot_pattern = shot_patterns.most_common(1)
most_common_defensive_movement = (
    defensive_preceding_movements.most_common(1)
)

if most_common_shot_pattern:
    pattern, count = most_common_shot_pattern[0]

    shot_explanation = (
        f"The sequence {pattern} appeared {count} times "
        "in attacking phases that reached a shot. "
        "It is a recurring attacking sequence in this simulation."
    )
else:
    shot_explanation = (
        "There were not enough recorded movement pairs "
        "before shots to identify a recurring pattern."
    )

if most_common_defensive_movement:
    movement, count = most_common_defensive_movement[0]

    defensive_explanation = (
        f"A {movement} was the last recorded attacking movement "
        f"before a defensive disruption in {count} phases. "
        "This is worth examining as a possible defensive trigger."
    )
else:
    defensive_explanation = (
        "No preceding attacking movements could be identified "
        "for defensive disruptions."
    )


# 6. CREATE THE REPORT

report = {
    "dataset": {
        "total_events": len(events),
        "total_phases": len(phases),
        "shot_phases": shot_phases,
        "goal_phases": goal_phases,
        "defensively_disrupted_phases": disrupted_phases
    },

    "shot_movement_patterns": dict(shot_patterns),

    "movements_before_defensive_disruptions": (
        dict(defensive_preceding_movements)
    ),

    "broadcast_explanations": {
        "attacking_pattern": shot_explanation,
        "defensive_reaction": defensive_explanation
    }
}


# 7. DISPLAY AND SAVE

print("\n===== FOOTBALL INTELLIGENCE REPORT =====")

print("\nDATASET SUMMARY:")
for key, value in report["dataset"].items():
    print(f"{key}: {value}")

print("\nMOVEMENT PAIRS BEFORE SHOTS:")
for pattern, count in shot_patterns.most_common(5):
    print(f"{pattern}: {count}")

print("\nMOVEMENTS BEFORE DEFENSIVE DISRUPTIONS:")
for movement, count in defensive_preceding_movements.most_common():
    print(f"{movement}: {count}")

print("\nBROADCAST EXPLANATIONS:")
print("\nATTACKING:", shot_explanation)
print("\nDEFENDING:", defensive_explanation)

with open("broadcast_report.json", "w") as file:
    json.dump(report, file, indent=4)

print("\nReport saved to broadcast_report.json")
