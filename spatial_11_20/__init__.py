import random

from otree.api import *
from reasoning_rounds import draw_reasoning_rounds


class C(BaseConstants):
    NAME_IN_URL = 'spatial_11_20'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10
    BONUS = 10


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    if subsession.round_number == 1:
        subsession.session.vars['spatial_reasoning_rounds'] = (
            draw_reasoning_rounds(C.NUM_ROUNDS)
        )

    subsession.group_randomly()
    reasoning_rounds = subsession.session.vars['spatial_reasoning_rounds']
    for group in subsession.get_groups():
        target_differences = [1, 5]
        random.shuffle(target_differences)
        for player, target_difference in zip(
            group.get_players(), target_differences
        ):
            player.target_difference = target_difference
            player.is_reasoning_round = (
                subsession.round_number in reasoning_rounds
            )


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    num = models.IntegerField(min=1, max=25, label='請選擇您的數字：')
    revised_num = models.IntegerField(
        min=1, max=25, blank=True, label='請重新選擇您的數字：'
    )
    target_difference = models.IntegerField()
    other_num = models.IntegerField(min=1, max=25)
    bonus = models.BooleanField(initial=False)
    reason = models.LongStringField(
        label='請說明您選擇該數字的理由：', initial='', rows=3
    )
    is_reasoning_round = models.BooleanField(initial=False)


def is_reasoning_round(player: Player) -> bool:
    stored_value = player.field_maybe_none('is_reasoning_round')
    if stored_value is not None:
        return stored_value
    return player.round_number in player.session.vars.get(
        'spatial_reasoning_rounds', []
    )


def set_payoffs(group: Group):
    for player in group.get_players():
        other = player.get_others_in_group()[0]
        player.other_num = other.num
        final_num = (
            player.revised_num
            if player.field_maybe_none('revised_num') is not None
            else player.num
        )
        player.bonus = final_num == other.num - player.target_difference
        player.payoff = cu(final_num)
        if player.bonus:
            player.payoff += cu(C.BONUS)


class InstructionPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return {'bonus_amount': C.BONUS}


class game(Page):
    form_model = 'player'
    form_fields = ['num']

    @staticmethod
    def vars_for_template(player: Player):
        number_rows = [
            list(range(row * 5 + 1, row * 5 + 6)) for row in range(5)
        ]
        return {
            'number_rows': number_rows,
            'target_difference': player.target_difference,
        }


class ReasoningWaitPage(WaitPage):
    title_text = '請等待所有參與者完成本回合選擇'
    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player: Player):
        return is_reasoning_round(player)


class game_with_reason(Page):
    form_model = 'player'
    form_fields = ['revised_num', 'reason']

    @staticmethod
    def is_displayed(player: Player):
        return is_reasoning_round(player)

    @staticmethod
    def vars_for_template(player: Player):
        number_rows = [
            list(range(row * 5 + 1, row * 5 + 6)) for row in range(5)
        ]
        return {'number_rows': number_rows}

    @staticmethod
    def error_message(player: Player, values):
        revised_num = values.get('revised_num')
        if revised_num is not None and revised_num == player.num:
            return '重新選擇的數字不可與原先選擇相同。'

        reason = (values.get('reason') or '').strip()
        if not reason:
            return '請填寫您的決策理由。'
        if len(set(reason)) < 3:
            return '請勿輸入過短、單一，或重複的文字內容。'


class DecisionWaitPage(WaitPage):
    title_text = '請等待配對對手完成選擇'
    wait_for_all_groups = True
    after_all_players_arrive = 'set_payoffs'


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        history = []
        for round_player in player.in_all_rounds():
            if round_player.round_number > player.round_number:
                continue
            revised_num = round_player.field_maybe_none('revised_num')
            final_num = (
                revised_num if revised_num is not None else round_player.num
            )
            history.append({
                'round': round_player.round_number,
                'is_current': round_player.round_number == player.round_number,
                'is_reasoning_round': is_reasoning_round(round_player),
                'initial_num': round_player.num,
                'revised_num': revised_num,
                'num': final_num,
                'other_num': round_player.other_num,
                'target_difference': round_player.target_difference,
                'target_number': (
                    round_player.other_num - round_player.target_difference
                ),
                'bonus': round_player.bonus,
                'round_payoff': round_player.payoff,
                'reason': (
                    round_player.reason
                    if is_reasoning_round(round_player)
                    else None
                ),
            })

        return {
            'bonus_amount': C.BONUS,
            'history': history,
            'cumulative_payoff': sum(
                entry.payoff
                for entry in player.in_all_rounds()
                if entry.round_number <= player.round_number
            ),
        }


class RoundWaitPage(WaitPage):
    title_text = '請等待所有參與者完成本回合'
    wait_for_all_groups = True


page_sequence = [
    InstructionPage,
    game,
    ReasoningWaitPage,
    game_with_reason,
    DecisionWaitPage,
    Results,
    RoundWaitPage,
]
