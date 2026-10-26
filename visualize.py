
import csv
from collections import Counter

# Read dataset
with open("football_events.csv", "r", newline="") as file:
    events = list(csv.DictReader(file))

if not events:
    print("No events found in football_events.csv")
    raise SystemExit

# Select the match with the most recorded events
match_counts = Counter(event["match_id"] for event in events)
match_id = match_counts.most_common(1)[0][0]

match_events = [
    event for event in events
    if event["match_id"] == match_id
]

match_events.sort(
    key=lambda event: float(event.get("timestamp") or 0)
)

# Count event types
event_counts = Counter(event["event"] for event in match_events)

# Pitch dimensions
width = 720
height = 480
margin = 40

def convert_x(x):
    return margin + (float(x) / 120) * width

def convert_y(y):
    return margin + (float(y) / 80) * height

def get_position(event):
    """Get the event's coordinates safely."""

    x = event.get("start_x") or event.get("x")
    y = event.get("start_y") or event.get("y")

    if x and y:
        return convert_x(x), convert_y(y)

    return None


# Begin SVG
svg = """
<svg xmlns="http://www.w3.org/2000/svg"
     width="800" height="680">

<defs>
    <marker id="passArrow"
            markerWidth="8" markerHeight="8"
            refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L6,3 z" fill="#00e69a"/>
    </marker>

    <marker id="carryArrow"
            markerWidth="8" markerHeight="8"
            refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L6,3 z" fill="#54b9ff"/>
    </marker>
</defs>

<rect width="800" height="680" fill="#17251d"/>

<!-- Football pitch -->
<rect x="40" y="40" width="720" height="480"
      fill="#286b43" stroke="white" stroke-width="2"/>

<!-- Pitch markings -->
<line x1="400" y1="40" x2="400" y2="520"
      stroke="white" stroke-width="2"/>

<circle cx="400" cy="280" r="65"
        fill="none" stroke="white" stroke-width="2"/>

<circle cx="400" cy="280" r="3" fill="white"/>

<rect x="40" y="160" width="110" height="240"
      fill="none" stroke="white" stroke-width="2"/>

<rect x="650" y="160" width="110" height="240"
      fill="none" stroke="white" stroke-width="2"/>

<rect x="40" y="220" width="40" height="120"
      fill="none" stroke="white" stroke-width="2"/>

<rect x="720" y="220" width="40" height="120"
      fill="none" stroke="white" stroke-width="2"/>

<text x="400" y="25" fill="white"
      text-anchor="middle" font-size="16">
    MATCH BALL MOVEMENT AND EVENTS
</text>
"""

# Draw events
for event in match_events:

    event_type = event.get("event", "").lower()
    position = get_position(event)

    # PASS
    if event_type == "pass":

        try:
            x1 = convert_x(event["start_x"])
            y1 = convert_y(event["start_y"])
            x2 = convert_x(event["end_x"])
            y2 = convert_y(event["end_y"])
        except (ValueError, KeyError, TypeError):
            continue

        if event.get("outcome", "").lower() in (
            "intercepted", "unsuccessful"
        ):
            color = "#ff5544"
        else:
            color = "#00e69a"

        svg += f"""
        <line x1="{x1}" y1="{y1}"
              x2="{x2}" y2="{y2}"
              stroke="{color}" stroke-width="3"
              marker-end="url(#passArrow)"/>

        <circle cx="{x1}" cy="{y1}" r="4" fill="white"/>
        """

    # CARRY
    elif event_type == "carry":

        try:
            x1 = convert_x(event["start_x"])
            y1 = convert_y(event["start_y"])
            x2 = convert_x(event["end_x"])
            y2 = convert_y(event["end_y"])
        except (ValueError, KeyError, TypeError):
            continue

        svg += f"""
        <line x1="{x1}" y1="{y1}"
              x2="{x2}" y2="{y2}"
              stroke="#54b9ff" stroke-width="3"
              marker-end="url(#carryArrow)"/>
        """

    # SHOT
    elif event_type == "shot" and position:

        x, y = position

        svg += f"""
        <circle cx="{x}" cy="{y}" r="9"
                fill="none" stroke="#ffd34e"
                stroke-width="3"/>

        <circle cx="{x}" cy="{y}" r="3"
                fill="#ffd34e"/>
        """

    # GOAL
    elif event_type == "goal" and position:

        x, y = position

        svg += f"""
        <circle cx="{x}" cy="{y}" r="11"
                fill="#ffdf00" stroke="white"
                stroke-width="2"/>

        <text x="{x}" y="{y + 4}"
              text-anchor="middle"
              font-size="11" fill="#17251d">G</text>
        """

    # INTERCEPTION
    elif event_type == "interception" and position:

        x, y = position

        svg += f"""
        <path d="M{x-7},{y-7} L{x+7},{y+7}
                 M{x+7},{y-7} L{x-7},{y+7}"
              stroke="#ff5544" stroke-width="4"/>
        """

    # TURNOVER
    elif event_type == "turnover" and position:

        x, y = position

        svg += f"""
        <rect x="{x-6}" y="{y-6}"
              width="12" height="12"
              fill="#d58bff" stroke="white"
              stroke-width="1"/>
        """


# Event statistics
stats = [
    ("Passes", event_counts["pass"], "#00e69a"),
    ("Carries", event_counts["carry"], "#54b9ff"),
    ("Shots", event_counts["shot"], "#ffd34e"),
    ("Goals", event_counts["goal"], "#ffdf00"),
    ("Interceptions", event_counts["interception"], "#ff5544"),
    ("Turnovers", event_counts["turnover"], "#d58bff")
]

svg += """
<rect x="40" y="535" width="720" height="115"
      rx="8" fill="#20352a"/>

<text x="60" y="560" fill="white"
      font-size="15" font-weight="bold">
    MATCH EVENT SUMMARY
</text>
"""

# Draw statistics and legend
positions = [60, 175, 290, 405, 520, 650]

for (label, count, color), x in zip(stats, positions):

    svg += f"""
    <circle cx="{x}" cy="585" r="5" fill="{color}"/>

    <text x="{x + 12}" y="590"
          fill="white" font-size="12">
        {label}: {count}
    </text>
    """

svg += """
</svg>
"""

# Save file
with open("ball_patterns.svg", "w") as file:
    file.write(svg)

print("VISUALIZATION CREATED!")
print("Match:", match_id)
print("Total events:", len(match_events))

for event_type, count in event_counts.items():
    print(f"{event_type}: {count}")

print("File: ball_patterns.svg")
