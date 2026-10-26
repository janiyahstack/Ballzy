
import random
import math
import csv
import os

# ==========================================
# 1. CONFIGURATION
# ==========================================

PITCH_WIDTH = 120
PITCH_HEIGHT = 80
DT = 0.2

PASS_SPEED = 25
INTERCEPTION_RADIUS = 4

OUTPUT_FILE = "football_events.csv"

SHOT_ZONE_DISTANCE = 28
SHOT_ATTEMPT_CHANCE = 0.035
GOAL_CHANCE = 0.25


# ==========================================
# 2. PLAYER INITIAL POSITIONS
# ==========================================

FORMATION = {
    "GK":  [(5, 40)],
    "DEF": [(25, 15), (20, 32), (20, 48), (25, 65)],
    "MID": [(45, 22), (40, 40), (45, 58)],
    "FWD": [(65, 15), (70, 40), (65, 65)]
}


# ==========================================
# 3. PLAYER CREATION
# ==========================================

def create_team(team_name, direction):
    players = []

    for role, positions in FORMATION.items():
        for index, position in enumerate(positions):
            x, y = position

            if direction == "left":
                x = PITCH_WIDTH - x
                y = PITCH_HEIGHT - y

            players.append({
                "id": f"{team_name}_{role}_{index + 1}",
                "team": team_name,
                "role": role,
                "x": float(x),
                "y": float(y),
                "speed": random.uniform(3, 6),
                "target_x": float(x),
                "target_y": float(y)
            })

    return players


# ==========================================
# 4. EVENT RECORDING
# ==========================================

def make_event(match_id, phase_id, event_type, team, timestamp,
               player="", passer="", receiver="", opponent_passer="",
               start_x="", start_y="", end_x="", end_y="",
               x="", y="", outcome=""):

    return {
        "match_id": match_id,
        "phase_id": phase_id,
        "event": event_type,
        "team": team,
        "player": player,
        "passer": passer,
        "receiver": receiver,
        "opponent_passer": opponent_passer,
        "start_x": start_x,
        "start_y": start_y,
        "end_x": end_x,
        "end_y": end_y,
        "x": x,
        "y": y,
        "outcome": outcome,
        "timestamp": timestamp
    }


# ==========================================
# 5. CREATE THE BALL AND PHASE
# ==========================================

def create_ball(owner):
    return {
        "x": owner["x"],
        "y": owner["y"],
        "owner": owner["id"],
        "team": owner["team"],
        "target": None,
        "passer": None,
        "pass_start_x": None,
        "pass_start_y": None,
        "carry_start_x": owner["x"],
        "carry_start_y": owner["y"],
        "phase_number": 1
    }


def current_phase_id(match_id, ball):
    return f"{match_id}_PHASE_{ball['phase_number']:03d}"


def begin_new_phase(ball, owner):
    ball["phase_number"] += 1
    ball["owner"] = owner["id"]
    ball["team"] = owner["team"]
    ball["target"] = None
    ball["passer"] = None
    ball["x"] = owner["x"]
    ball["y"] = owner["y"]
    ball["carry_start_x"] = owner["x"]
    ball["carry_start_y"] = owner["y"]


# ==========================================
# 6. MOVEMENT CALCULATIONS
# ==========================================

def move_towards(player, target_x, target_y):
    dx = target_x - player["x"]
    dy = target_y - player["y"]

    distance = math.hypot(dx, dy)

    if distance == 0:
        return

    max_distance = player["speed"] * DT

    if distance <= max_distance:
        player["x"] = target_x
        player["y"] = target_y

    else:
        player["x"] += (dx / distance) * max_distance
        player["y"] += (dy / distance) * max_distance

    player["x"] = max(0, min(PITCH_WIDTH, player["x"]))
    player["y"] = max(0, min(PITCH_HEIGHT, player["y"]))


# ==========================================
# 7. ATTACKING MOVEMENT
# ==========================================

def attacking_movement(players, ball):
    carrier = next(
        p for p in players
        if p["id"] == ball["owner"]
    )

    direction = 1 if carrier["team"] == "A" else -1

    for player in players:
        if player["id"] == carrier["id"]:
            continue

        if player["role"] == "FWD":
            target_x = ball["x"] + direction * random.uniform(5, 15)
            target_y = ball["y"] + random.uniform(-15, 15)

        elif player["role"] == "MID":
            target_x = ball["x"] - direction * random.uniform(5, 15)
            target_y = ball["y"] + random.uniform(-15, 15)

        elif player["role"] == "DEF":
            target_x = ball["x"] - direction * random.uniform(15, 25)
            target_y = ball["y"] + random.uniform(-10, 10)

        else:
            continue

        target_x = max(0, min(PITCH_WIDTH, target_x))
        target_y = max(0, min(PITCH_HEIGHT, target_y))

        player["target_x"] = target_x
        player["target_y"] = target_y

        move_towards(player, target_x, target_y)


# ==========================================
# 8. DEFENSIVE MOVEMENT
# ==========================================

def defensive_movement(players, ball):
    defenders = sorted(
        players,
        key=lambda p: math.dist(
            (p["x"], p["y"]),
            (ball["x"], ball["y"])
        )
    )

    for index, player in enumerate(defenders):
        if index < 2:
            target_x = ball["x"]
            target_y = ball["y"]

        else:
            target_x = ball["x"] + (
                10 if player["team"] == "B" else -10
            )

            target_y = player["y"] + random.uniform(-2, 2)

        target_x = max(0, min(PITCH_WIDTH, target_x))
        target_y = max(0, min(PITCH_HEIGHT, target_y))

        player["target_x"] = target_x
        player["target_y"] = target_y

        move_towards(player, target_x, target_y)


# ==========================================
# 9. CARRY RECORDING
# ==========================================

def record_carry(ball, carrier, events, match_id, timestamp):
    start_x = ball["carry_start_x"]
    start_y = ball["carry_start_y"]

    end_x = carrier["x"]
    end_y = carrier["y"]

    distance = math.dist(
        (start_x, start_y),
        (end_x, end_y)
    )

    if distance >= 1:
        events.append(make_event(
            match_id=match_id,
            phase_id=current_phase_id(match_id, ball),
            event_type="carry",
            team=carrier["team"],
            player=carrier["id"],
            start_x=round(start_x, 2),
            start_y=round(start_y, 2),
            end_x=round(end_x, 2),
            end_y=round(end_y, 2),
            outcome="completed",
            timestamp=timestamp
        ))

    ball["carry_start_x"] = end_x
    ball["carry_start_y"] = end_y


# ==========================================
# 10. SELECT A PASS RECEIVER
# ==========================================

def choose_pass_receiver(players, carrier):
    teammates = [
        p for p in players
        if p["team"] == carrier["team"]
        and p["id"] != carrier["id"]
    ]

    if not teammates:
        return None

    direction = 1 if carrier["team"] == "A" else -1

    def pass_score(player):
        distance = math.dist(
            (carrier["x"], carrier["y"]),
            (player["x"], player["y"])
        )

        forward_progress = (
            player["x"] - carrier["x"]
        ) * direction

        return distance - max(0, forward_progress) * 0.3

    ranked = sorted(teammates, key=pass_score)

    return random.choice(ranked[:3])


# ==========================================
# 11. START A PASS
# ==========================================

def start_pass(ball, players, events, match_id, timestamp):
    carrier = next(
        p for p in players
        if p["id"] == ball["owner"]
    )

    receiver = choose_pass_receiver(players, carrier)

    if receiver is None:
        return False

    record_carry(
        ball, carrier, events, match_id, timestamp
    )

    ball["passer"] = carrier["id"]
    ball["target"] = receiver["id"]

    ball["pass_start_x"] = carrier["x"]
    ball["pass_start_y"] = carrier["y"]

    ball["x"] = carrier["x"]
    ball["y"] = carrier["y"]

    ball["owner"] = None

    return True


# ==========================================
# 12. UPDATE THE BALL
# ==========================================

def update_ball(ball, players, events, timestamp, match_id):
    if ball["owner"] is not None:
        owner = next(
            p for p in players
            if p["id"] == ball["owner"]
        )

        ball["x"] = owner["x"]
        ball["y"] = owner["y"]

        return

    receiver = next(
        p for p in players
        if p["id"] == ball["target"]
    )

    dx = receiver["x"] - ball["x"]
    dy = receiver["y"] - ball["y"]

    distance = math.hypot(dx, dy)
    max_distance = PASS_SPEED * DT

    if distance <= max_distance:
        ball["x"] = receiver["x"]
        ball["y"] = receiver["y"]

        ball["owner"] = receiver["id"]
        ball["team"] = receiver["team"]

        events.append(make_event(
            match_id,
            current_phase_id(match_id, ball),
            "pass",
            receiver["team"],
            timestamp,
            passer=ball["passer"],
            receiver=receiver["id"],
            start_x=round(ball["pass_start_x"], 2),
            start_y=round(ball["pass_start_y"], 2),
            end_x=round(ball["x"], 2),
            end_y=round(ball["y"], 2),
            outcome="successful"
        ))

        ball["target"] = None
        ball["passer"] = None

        ball["carry_start_x"] = receiver["x"]
        ball["carry_start_y"] = receiver["y"]

    elif distance > 0:
        ball["x"] += (dx / distance) * max_distance
        ball["y"] += (dy / distance) * max_distance


# ==========================================
# 13. CHECK FOR INTERCEPTIONS
# ==========================================

def check_interception(ball, players, events, timestamp, match_id):
    if ball["owner"] is not None:
        return False

    opponents = [
        p for p in players
        if p["team"] != ball["team"]
    ]

    for defender in opponents:
        distance = math.dist(
            (defender["x"], defender["y"]),
            (ball["x"], ball["y"])
        )

        if distance <= INTERCEPTION_RADIUS:
            previous_team = ball["team"]
            previous_passer = ball["passer"]

            old_phase = current_phase_id(match_id, ball)

            events.append(make_event(
                match_id,
                old_phase,
                "pass",
                previous_team,
                timestamp,
                passer=previous_passer,
                receiver=ball["target"],
                start_x=round(ball["pass_start_x"], 2),
                start_y=round(ball["pass_start_y"], 2),
                end_x=round(ball["x"], 2),
                end_y=round(ball["y"], 2),
                outcome="intercepted"
            ))

            events.append(make_event(
                match_id,
                old_phase,
                "interception",
                defender["team"],
                timestamp,
                player=defender["id"],
                opponent_passer=previous_passer,
                x=round(defender["x"], 2),
                y=round(defender["y"], 2),
                outcome="successful"
            ))

            events.append(make_event(
                match_id,
                old_phase,
                "turnover",
                previous_team,
                timestamp,
                player=defender["id"],
                x=round(defender["x"], 2),
                y=round(defender["y"], 2),
                outcome="intercepted"
            ))

            begin_new_phase(ball, defender)

            return True

    return False


# ==========================================
# 14. SHOTS AND GOALS
# ==========================================

def is_in_shooting_zone(carrier):
    if carrier["team"] == "A":
        distance_to_goal = PITCH_WIDTH - carrier["x"]

    else:
        distance_to_goal = carrier["x"]

    return distance_to_goal <= SHOT_ZONE_DISTANCE


def attempt_shot(ball, carrier, events, match_id, timestamp):
    record_carry(
        ball, carrier, events, match_id, timestamp
    )

    phase_id = current_phase_id(match_id, ball)
    attacking_team = carrier["team"]

    if random.random() < GOAL_CHANCE:
        outcome = "goal"

    elif random.random() < 0.6:
        outcome = "saved"

    else:
        outcome = "missed"

    events.append(make_event(
        match_id,
        phase_id,
        "shot",
        attacking_team,
        timestamp,
        player=carrier["id"],
        x=round(carrier["x"], 2),
        y=round(carrier["y"], 2),
        outcome=outcome
    ))

    if outcome == "goal":
        events.append(make_event(
            match_id,
            phase_id,
            "goal",
            attacking_team,
            timestamp,
            player=carrier["id"],
            x=round(carrier["x"], 2),
            y=round(carrier["y"], 2),
            outcome="scored"
        ))

    return outcome


# ==========================================
# 15. INITIALIZE THE ENVIRONMENT
# ==========================================

def initialize_environment():
    team_a = create_team("A", "right")
    team_b = create_team("B", "left")

    players = team_a + team_b

    carrier = next(
        p for p in team_a
        if p["role"] == "FWD"
        and p["y"] == 40
    )

    ball = create_ball(carrier)

    return players, ball


# ==========================================
# 16. RUN ONE MATCH
# ==========================================

def run_simulation(duration=30, match_id="MATCH_001"):
    players, ball = initialize_environment()

    events = []

    steps = int(duration / DT)

    for step in range(steps):
        timestamp = round(step * DT, 2)

        team_a = [
            p for p in players
            if p["team"] == "A"
        ]

        team_b = [
            p for p in players
            if p["team"] == "B"
        ]

        if ball["owner"] is not None:
            attacking_team = (
                team_a if ball["team"] == "A" else team_b
            )

            defending_team = (
                team_b if ball["team"] == "A" else team_a
            )

            attacking_movement(attacking_team, ball)

            carrier = next(
                p for p in attacking_team
                if p["id"] == ball["owner"]
            )

            direction = 1 if ball["team"] == "A" else -1

            carrier["x"] += (
                direction * carrier["speed"] * DT
            )

            carrier["x"] = max(
                0,
                min(PITCH_WIDTH, carrier["x"])
            )

            defensive_movement(defending_team, ball)

            ball["x"] = carrier["x"]
            ball["y"] = carrier["y"]

            # Check for a shot before the scheduled pass.
            if (
                is_in_shooting_zone(carrier)
                and random.random() < SHOT_ATTEMPT_CHANCE
            ):
                attempt_shot(
                    ball, carrier, events, match_id, timestamp
                )

                # End the attacking phase and restart possession
                # with the nearest opponent.
                opposing_team = (
                    team_b if carrier["team"] == "A" else team_a
                )

                restart_player = min(
                    opposing_team,
                    key=lambda p: math.dist(
                        (p["x"], p["y"]),
                        (carrier["x"], carrier["y"])
                    )
                )

                begin_new_phase(ball, restart_player)

                continue

            # Attempt a pass every four seconds.
            if (
                step > 0
                and step % 20 == 0
                and ball["owner"] is not None
            ):
                start_pass(
                    ball, players, events, match_id, timestamp
                )

        else:
            # Defenders continue moving while the ball travels.
            defending_team = (
                team_b if ball["team"] == "A" else team_a
            )

            defensive_movement(defending_team, ball)

        update_ball(
            ball, players, events, timestamp, match_id
        )

        check_interception(
            ball, players, events, timestamp, match_id
        )

    # Record any carry still in progress at the end.
    if ball["owner"] is not None:
        carrier = next(
            p for p in players
            if p["id"] == ball["owner"]
        )

        record_carry(
            ball, carrier, events, match_id,
            round(duration, 2)
        )

    return events


# ==========================================
# 17. GENERATE MULTIPLE MATCHES
# ==========================================

def generate_matches(number_of_matches=50, duration=30):
    all_events = []

    print("GENERATING SYNTHETIC MATCHES")
    print("--------------------------------")

    for match_number in range(1, number_of_matches + 1):
        match_id = f"MATCH_{match_number:03d}"

        random.seed(1000 + match_number)

        match_events = run_simulation(
            duration=duration,
            match_id=match_id
        )

        all_events.extend(match_events)

        counts = {}

        for event in match_events:
            counts[event["event"]] = (
                counts.get(event["event"], 0) + 1
            )

        print(
            f"{match_id}: "
            f"{counts.get('pass', 0)} passes, "
            f"{counts.get('carry', 0)} carries, "
            f"{counts.get('shot', 0)} shots, "
            f"{counts.get('goal', 0)} goals, "
            f"{counts.get('turnover', 0)} turnovers"
        )

    return all_events


# ==========================================
# 18. EXPORT EVENTS TO CSV
# ==========================================

def save_events_to_csv(events):
    if not events:
        print("No events were generated.")
        return

    fieldnames = [
        "match_id",
        "phase_id",
        "event",
        "team",
        "player",
        "passer",
        "receiver",
        "opponent_passer",
        "start_x",
        "start_y",
        "end_x",
        "end_y",
        "x",
        "y",
        "outcome",
        "timestamp"
    ]

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        OUTPUT_FILE
    )

    with open(
        output_path,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(events)

    print(f"\nEvents saved to: {output_path}")


# ==========================================
# 19. EXECUTE
# ==========================================

if __name__ == "__main__":
    number_of_matches = 50

    all_events = generate_matches(
        number_of_matches=number_of_matches,
        duration=30
    )

    save_events_to_csv(all_events)

    print("\nDATASET SUMMARY")
    print("--------------------------------")

    print("Total matches:", number_of_matches)
    print("Total events:", len(all_events))

    for event_type in [
        "pass",
        "carry",
        "interception",
        "shot",
        "goal",
        "turnover"
    ]:
        count = sum(
            1 for event in all_events
            if event["event"] == event_type
        )

        print(f"{event_type.title()} events: {count}")
