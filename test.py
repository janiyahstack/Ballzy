import random

current_position = (30,25)
events = []

for _ in range(5):
    event_type = random.choices(["pass", "carry"])
    if event_type == "pass":
     dx = random.randint( -15, 15)
     dy = random.randint(-10, 10)
    else:
       dx = random.randint(-5, 5)
       dy = random.randint(-4, 4)
    destination = (max(0, min(120, current_position[0] + dx)), max(0, min(80, current_position[1] + dy)))
    event = {
        "type": event_type,
        "start": current_position,
        "end": destination
    }
    events.append(event)
current_position = destination
print(events)