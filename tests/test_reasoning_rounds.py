import unittest
from collections import Counter
from types import SimpleNamespace
from unittest.mock import patch

import phase2
import phase3
import phase4
from otree.api import WaitPage
from phase4 import (
    basic_source_round_for_prediction,
    eligible_prediction_targets,
    prediction_rounds_p2_for,
)
from phase2 import reasoningWaitPage as BasicReasoningWaitPage
from phase3 import reasoningWaitPage as NoCycleReasoningWaitPage
from reasoning_rounds import (
    draw_balanced_reasoning_schedules,
    validate_reasoning_schedules,
)
from settings import DEBUG


class BalancedReasoningScheduleTests(unittest.TestCase):
    def test_debug_round_counts_cover_all_reasoning_schedules(self):
        expected_basic_rounds = 5 if DEBUG else 15
        expected_no_cycle_rounds = 5 if DEBUG else 10
        self.assertEqual(phase2.C.NUM_ROUNDS, expected_basic_rounds)
        self.assertEqual(phase3.C.NUM_ROUNDS, expected_no_cycle_rounds)
        self.assertEqual(phase4.ai_processing.C.NUM_ROUNDS, 5 if DEBUG else 15)
        self.assertEqual(phase4.C.NUM_ROUNDS, 5 if DEBUG else 15)
        self.assertEqual(
            phase2.C.REASONING_SCHEDULES,
            ((1, 3), (1, 4))
            if DEBUG
            else ((1, 3, 8, 13), (1, 4, 9, 14)),
        )
        self.assertEqual(
            phase3.C.NO_CYCLE_SCHEDULES,
            {'A': (1, 4), 'B': (1, 3)}
            if DEBUG
            else {'A': (1, 4, 7, 10), 'B': (1, 3, 6, 9)},
        )
        self.assertEqual(
            len(phase2.C.REASONING_SCHEDULES[0]),
            len(phase2.C.REASONING_SCHEDULES[1]),
        )
        self.assertEqual(
            len(phase3.C.NO_CYCLE_SCHEDULES["A"]),
            len(phase3.C.NO_CYCLE_SCHEDULES["B"]),
        )
        for schedule in phase2.C.REASONING_SCHEDULES:
            self.assertLessEqual(max(schedule), phase2.C.NUM_ROUNDS)
        self.assertLessEqual(
            max(phase3.C.NO_CYCLE_SCHEDULES["A"]), phase3.C.NUM_ROUNDS
        )
        self.assertLessEqual(
            max(phase3.C.NO_CYCLE_SCHEDULES["B"]), phase3.C.NUM_ROUNDS
        )

    def test_rejects_mismatched_schedule_lengths(self):
        with self.assertRaisesRegex(ValueError, "same number of rounds"):
            validate_reasoning_schedules(
                {"A": (1, 3, 8, 13), "B": (1, 4, 9)},
                15,
            )

    def test_assigns_exactly_half_of_groups_to_each_schedule(self):
        schedule_a = (1, 3, 8, 13)
        schedule_b = (1, 4, 9, 14)

        assignments = draw_balanced_reasoning_schedules(
            6, schedule_a, schedule_b
        )

        self.assertEqual(len(assignments), 6)
        self.assertEqual(Counter(assignments), {schedule_a: 3, schedule_b: 3})

    def test_assigns_odd_group_counts_with_at_most_one_group_difference(self):
        schedule_a = (1, 3)
        schedule_b = (1, 4)

        for num_groups in (1, 3, 5):
            with self.subTest(num_groups=num_groups):
                assignments = draw_balanced_reasoning_schedules(
                    num_groups, schedule_a, schedule_b
                )
                counts = Counter(assignments)

                self.assertEqual(len(assignments), num_groups)
                self.assertLessEqual(
                    abs(counts[schedule_a] - counts[schedule_b]), 1
                )
                self.assertEqual(
                    sorted((counts[schedule_a], counts[schedule_b])),
                    [num_groups // 2, (num_groups + 1) // 2],
                )

    def test_prediction_ordinals_align_across_basic_schedules(self):
        for schedule in (
            [1, 3, 8, 13],
            [1, 4, 9, 14],
        ):
            player = SimpleNamespace(
                participant=SimpleNamespace(
                    vars={"phase2_reasoning_rounds": schedule}
                )
            )
            prediction_rounds = prediction_rounds_p2_for(player)
            self.assertEqual(prediction_rounds, [1, 2, 3, 4])
            self.assertEqual(
                [
                    basic_source_round_for_prediction(player, ordinal)
                    for ordinal in prediction_rounds
                ],
                schedule,
            )


class ReasoningScheduleBarrierTests(unittest.TestCase):
    def test_phase_wait_pages_only_block_the_fixed_pair(self):
        for app_module in (phase2, phase3):
            for wait_page_name in (
                "reasoningWaitPage",
                "DecisionWaitPage",
                "ResultsWaitPage",
            ):
                wait_page = getattr(app_module, wait_page_name)
                self.assertTrue(issubclass(wait_page, WaitPage))
                self.assertFalse(wait_page.wait_for_all_groups)

    def test_part_end_wait_pages_block_all_participants_only_on_final_round(self):
        for app_module, wait_page_name in (
            (phase2, "Phase2EndWaitPage"),
            (phase3, "Phase3EndWaitPage"),
        ):
            wait_page = getattr(app_module, wait_page_name)
            self.assertTrue(issubclass(wait_page, WaitPage))
            self.assertTrue(wait_page.wait_for_all_groups)
            self.assertTrue(
                wait_page.is_displayed(
                    SimpleNamespace(round_number=app_module.C.NUM_ROUNDS)
                )
            )
            self.assertFalse(
                wait_page.is_displayed(SimpleNamespace(round_number=1))
            )

    def test_no_cycle_matching_allows_odd_basic_group_counts_per_schedule(self):
        class FakeGroup:
            def __init__(self, players):
                self.players = players

            def get_players(self):
                return self.players

        class FakeSubsession:
            def __init__(self, players):
                self.round_number = 1
                self.session = SimpleNamespace(vars={})
                self.players_by_id = {
                    player.id_in_subsession: player for player in players
                }
                self.groups = []

            def get_players(self):
                return list(self.players_by_id.values())

            def set_group_matrix(self, group_matrix):
                self.groups = [
                    FakeGroup(
                        [self.players_by_id[player_id] for player_id in member_ids]
                    )
                    for member_ids in group_matrix
                ]

            def get_groups(self):
                return self.groups

        players = []
        for schedule_id, ids in (("A", range(1, 7)), ("B", range(7, 9))):
            for player_id in ids:
                players.append(
                    SimpleNamespace(
                        id_in_subsession=player_id,
                        participant=SimpleNamespace(
                            vars={
                                "phase2_reasoning_schedule_id": schedule_id
                            }
                        ),
                    )
                )
        subsession = FakeSubsession(players)

        def rotate(values):
            values.append(values.pop(0))

        with patch("phase3.random.shuffle", side_effect=rotate):
            phase3.creating_session(subsession)

        self.assertEqual(len(subsession.groups), 4)
        for group in subsession.groups:
            members = group.get_players()
            self.assertEqual(len(members), 2)
            self.assertEqual(
                len({
                    member.participant.vars["phase2_reasoning_schedule_id"]
                    for member in members
                }),
                1,
            )
        self.assertEqual(
            {
                frozenset(player.id_in_subsession for player in group.get_players())
                for group in subsession.groups
            },
            {
                frozenset((2, 3)),
                frozenset((4, 5)),
                frozenset((6, 1)),
                frozenset((7, 8)),
            },
        )


class PredictionTargetTests(unittest.TestCase):
    def test_selects_valid_same_schedule_target_from_entire_subsession(self):
        def candidate(subsession_id, schedule_id, rounds, entry):
            return SimpleNamespace(
                id_in_subsession=subsession_id,
                participant=SimpleNamespace(
                    vars={
                        "phase2_reasoning_schedule_id": schedule_id,
                        "phase2_reasoning_rounds": rounds,
                        "phase2_history": [entry] if entry else [],
                    }
                ),
            )

        player = candidate(
            1, "A", [1, 3, 8, 13], {"round": 1}
        )
        valid_target = candidate(
            2,
            "A",
            [1, 3, 8, 13],
            {"round": 8, "human_reason": "human", "gpt_reason": "AI"},
        )
        incomplete_same_schedule = candidate(
            3,
            "A",
            [1, 3, 8, 13],
            {"round": 8, "human_reason": "human"},
        )
        other_schedule = candidate(
            4,
            "B",
            [1, 4, 9, 14],
            {"round": 9, "human_reason": "human", "gpt_reason": "AI"},
        )
        player.subsession = SimpleNamespace(
            get_players=lambda: [
                player,
                valid_target,
                incomplete_same_schedule,
                other_schedule,
            ]
        )

        targets = eligible_prediction_targets(player, 3)

        self.assertEqual(targets, [(valid_target, 8)])


if __name__ == "__main__":
    unittest.main()
