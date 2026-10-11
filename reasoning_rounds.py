import random


REASONING_ROUND_RANGES = ((1, 3), (4, 7), (8, 10))


def draw_reasoning_rounds(num_rounds):
    selected_rounds = []
    for start, end in REASONING_ROUND_RANGES:
        candidates = range(max(1, start), min(num_rounds, end) + 1)
        if candidates:
            selected_rounds.append(random.choice(candidates))
    return sorted(selected_rounds)
