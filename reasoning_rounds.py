import random


REASONING_ROUND_RANGES = ((1, 3), (4, 7), (8, 10))


def draw_reasoning_rounds(num_rounds):
    selected_rounds = []
    for start, end in REASONING_ROUND_RANGES:
        candidates = range(max(1, start), min(num_rounds, end) + 1)
        if candidates:
            selected_rounds.append(random.choice(candidates))
    return sorted(selected_rounds)


def draw_balanced_reasoning_schedules(num_groups, schedule_a, schedule_b):
    if num_groups < 1:
        raise ValueError("At least one group is required.")

    groups_per_schedule = num_groups // 2
    assignments = [tuple(schedule_a)] * groups_per_schedule
    assignments.extend([tuple(schedule_b)] * groups_per_schedule)
    if num_groups % 2:
        assignments.append(tuple(random.choice((schedule_a, schedule_b))))
    random.shuffle(assignments)
    return assignments


def validate_reasoning_schedules(schedules, num_rounds):
    if set(schedules) != {"A", "B"}:
        raise ValueError("Exactly two reasoning schedules, A and B, are required.")

    lengths = set()
    for schedule_id, rounds in schedules.items():
        if not rounds:
            raise ValueError(
                f"Reasoning schedule {schedule_id} must contain at least one round."
            )
        if any(not isinstance(round_number, int) for round_number in rounds):
            raise ValueError(
                f"Reasoning schedule {schedule_id} must use integer round numbers."
            )
        if tuple(rounds) != tuple(sorted(set(rounds))):
            raise ValueError(
                f"Reasoning schedule {schedule_id} must be unique and chronological."
            )
        if rounds[0] < 1 or rounds[-1] > num_rounds:
            raise ValueError(
                f"Reasoning schedule {schedule_id} must fit within "
                f"the configured {num_rounds} rounds."
            )
        lengths.add(len(rounds))

    if len(lengths) != 1:
        raise ValueError(
            "All reasoning schedules must have the same number of rounds "
            "so Phase 4 can present the same number of predictions."
        )
