from otree.api import *
import random
from reasoning_rounds import (
    validate_reasoning_schedules,
)
from settings import DEBUG

class C(BaseConstants):
    NAME_IN_URL = 'phase3'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 5 if DEBUG else 10
    NO_CYCLE_SCHEDULES = (
        {'A': (1, 4), 'B': (1, 3)}
        if DEBUG
        else {'A': (1, 4, 7, 10), 'B': (1, 3, 6, 9)}
    )


class Subsession(BaseSubsession):
    pass


def creating_session(subsession):
    if subsession.round_number == 1:
        validate_reasoning_schedules(
            C.NO_CYCLE_SCHEDULES, C.NUM_ROUNDS
        )
        participants_by_schedule = {'A': [], 'B': []}
        for player in subsession.get_players():
            schedule_id = player.participant.vars[
                'phase2_reasoning_schedule_id'
            ]
            participants_by_schedule[schedule_id].append(
                player.id_in_subsession
            )

        group_matrix = []
        for schedule_id, participant_ids in participants_by_schedule.items():
            if len(participant_ids) % C.PLAYERS_PER_GROUP:
                raise ValueError(
                    "No-cycle matching requires an even number of participants "
                    "in each Basic reasoning schedule."
                )
            random.shuffle(participant_ids)
            group_matrix.extend(
                [
                    participant_ids[index:index + C.PLAYERS_PER_GROUP]
                    for index in range(
                        0, len(participant_ids), C.PLAYERS_PER_GROUP
                    )
                ]
            )
        subsession.set_group_matrix(group_matrix)
        subsession.session.vars['phase3_reasoning_rounds'] = sorted(
            set(C.NO_CYCLE_SCHEDULES['A'])
            | set(C.NO_CYCLE_SCHEDULES['B'])
        )
    else:
        subsession.group_like_round(1)

    for group in subsession.get_groups():
        members = group.get_players()
        schedule_ids = {
            member.participant.vars['phase2_reasoning_schedule_id']
            for member in members
        }
        if len(schedule_ids) != 1:
            raise ValueError(
                "No-cycle groups must match their Basic 11-20 reasoning schedule."
            )

        schedule_id = schedule_ids.pop()
        reasoning_rounds = list(C.NO_CYCLE_SCHEDULES[schedule_id])
        for player in members:
            player.reasoning_schedule_id = schedule_id
            player.is_reasoning_round = (
                subsession.round_number in reasoning_rounds
            )
            player.participant.vars['phase3_reasoning_rounds'] = reasoning_rounds
            player.participant.vars['phase3_reasoning_schedule_id'] = schedule_id


def reasoning_rounds_for(player):
    return player.participant.vars['phase3_reasoning_rounds']


def set_payoffs(group: BaseGroup):
    for player in group.get_players():
        opponent = player.get_others_in_group()[0]
        final_num = (
            player.revised_num
            if player.field_maybe_none('revised_num') is not None
            else player.initial_num
        )
        player.final_num = final_num
        player.opponent_initial_num = opponent.initial_num
        player.opponent_revised_num = opponent.field_maybe_none('revised_num')
        player.is_number_winner = final_num == opponent.initial_num - 1
        player.is_same = final_num == opponent.initial_num
        player.payoff = cu(final_num)
        if player.is_number_winner:
            player.payoff += cu(20)
        elif player.is_same:
            player.payoff += cu(10)

        round_number = player.round_number
        player.participant.vars[f"initial_num_2_{round_number}"] = (
            player.initial_num
        )
        player.participant.vars[f"revised_num_2_{round_number}"] = (
            player.field_maybe_none('revised_num')
        )
        player.participant.vars[f"num_2_{round_number}"] = final_num
        player.participant.vars[f"other_num_2_{round_number}"] = (
            opponent.initial_num
        )
        player.participant.vars[f"other_revised_num_2_{round_number}"] = (
            opponent.field_maybe_none('revised_num')
        )
        player.participant.vars[f"reason_2_{round_number}"] = (
            player.reason
            if round_number in reasoning_rounds_for(player) else None
        )
        player.participant.vars[f"payoff_2_{round_number}"] = player.payoff
        player.participant.vars[f"bonus_2_{round_number}"] = (
            player.is_number_winner
        )
        player.participant.vars[f"phase3_same_number_{round_number}"] = (
            player.is_same
        )
        player.participant.vars['phase3_reasoning_rounds'] = (
            reasoning_rounds_for(player)
        )


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    initial_num = models.IntegerField(
        min=11,
        max=20,
        label="請選擇您的數字：",
    )
    revised_num = models.IntegerField(
        min=11,
        max=20,
        blank=True,
        label="請重新選擇數字：",
    )
    final_num = models.IntegerField(min=11, max=20)
    opponent_initial_num = models.IntegerField(min=11, max=20)
    opponent_revised_num = models.IntegerField(min=11, max=20, blank=True)
    reason = models.LongStringField(
        label="請說明您選擇該數字的理由：",
        initial="",
        rows=3,
    )
    reasoning_schedule_id = models.StringField()
    is_reasoning_round = models.BooleanField(initial=False)
    is_number_winner = models.BooleanField(initial=False)
    is_same = models.BooleanField(initial=False)


##############################################################################

# pages

from otree.api import *


class InstructionPage(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class Phase3StartWaitPage(WaitPage):
    title_text = "請等待其他受試者完成準備"
    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class game(Page):
    form_model = 'player'
    form_fields = ['initial_num']

    @staticmethod
    def vars_for_template(player):
        return {"number_choices": range(11, 21)}


class reasoningWaitPage(WaitPage):
    title_text = "請等待同組受試者完成決策"
    wait_for_all_groups = False

    @staticmethod
    def is_displayed(player):
        return player.round_number in reasoning_rounds_for(player)


class game_with_reason(Page):
    form_model = 'player'
    form_fields = ['revised_num', 'reason']

    @staticmethod
    def is_displayed(player):
        return player.round_number in reasoning_rounds_for(player)

    @staticmethod
    def vars_for_template(player):
        return {"number_choices": range(11, 21)}

    @staticmethod
    def error_message(player, values):
        revised_num = values.get('revised_num')
        if revised_num is not None and revised_num == player.initial_num:
            return "重新選擇的數字不可與原先選擇相同。"

        content = values['reason'].strip()
        if len(content) == 0:
            return "理由欄位不能為空，請輸入您的決策思考過程。"
        if len(set(content)) < 3:
            return "請勿輸入過短、單一，或重複的文字內容。"


class DecisionWaitPage(WaitPage):
    title_text = "請等待同組受試者完成決策"
    wait_for_all_groups = False
    after_all_players_arrive = 'set_payoffs'


class Results(Page):
    @staticmethod
    def vars_for_template(player):
        history = []
        reasoning_rounds = reasoning_rounds_for(player)

        for round_player in player.in_all_rounds():
            history.append({
                'round': round_player.round_number,
                'initial_num': str(round_player.initial_num),
                'revised_num': round_player.field_maybe_none('revised_num'),
                'num': str(round_player.final_num),
                'other_num': round_player.opponent_initial_num,
                'reason': (
                    round_player.reason
                    if round_player.round_number in reasoning_rounds else None
                ),
                'is_current': round_player.round_number == player.round_number,
                'is_reasoning_round': (
                    round_player.round_number in reasoning_rounds
                ),
                'initial_bonus': (
                    round_player.initial_num
                    == round_player.opponent_initial_num - 1
                ),
                'initial_same': (
                    round_player.initial_num
                    == round_player.opponent_initial_num
                ),
                'after_bonus': round_player.is_number_winner,
                'bonus': round_player.is_number_winner,
                'is_same': round_player.is_same,
                'round_payoff': round_player.payoff,
            })

        if player.round_number == C.NUM_ROUNDS:
            round_payoffs = {
                round_number: player.in_round(round_number).payoff
                for round_number in range(1, C.NUM_ROUNDS + 1)
            }
            player.participant.vars["phase3_round_payoffs"] = round_payoffs
            player.participant.vars["phase3_sum_payoffs"] = sum(
                round_payoffs.values()
            )
            player.participant.vars["phase3_history"] = history

        return {'history': history}


class ResultsWaitPage(WaitPage):
    title_text = "請等待同組受試者確認結果"
    wait_for_all_groups = False


class Phase3EndWaitPage(WaitPage):
    title_text = "請等待所有受試者完成第三部分"
    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS


page_sequence = [
    InstructionPage,
    Phase3StartWaitPage,
    game,
    reasoningWaitPage,
    game_with_reason,
    DecisionWaitPage,
    Results,
    ResultsWaitPage,
    Phase3EndWaitPage,
]
