import random

from otree.api import *


class C(BaseConstants):
    NAME_IN_URL = 'spatial_11_20'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 10
    BONUS = 10


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    subsession.group_randomly()
    for group in subsession.get_groups():
        target_differences = [1, 10]
        random.shuffle(target_differences)
        for player, target_difference in zip(
            group.get_players(), target_differences
        ):
            player.target_difference = target_difference


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    num = models.IntegerField(min=1, max=100, label='請選擇您的數字：')
    target_difference = models.IntegerField()
    other_num = models.IntegerField(min=1, max=100)
    bonus = models.BooleanField(initial=False)


def set_payoffs(group: Group):
    for player in group.get_players():
        other = player.get_others_in_group()[0]
        player.other_num = other.num
        player.bonus = player.num == other.num - player.target_difference
        player.payoff = cu(player.num)
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
            list(range(row * 10 + 1, row * 10 + 11)) for row in range(10)
        ]
        return {
            'number_rows': number_rows,
            'target_difference': player.target_difference,
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.payoff = cu(player.num)


class BasePayoff(Page):
    pass


class DecisionWaitPage(WaitPage):
    title_text = '請等待配對對手完成選擇'
    after_all_players_arrive = 'set_payoffs'


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'target_number': player.other_num - player.target_difference,
            'cumulative_payoff': sum(
                p.payoff for p in player.in_all_rounds()
            ),
        }


class RoundWaitPage(WaitPage):
    title_text = '請等待所有參與者完成本回合'
    wait_for_all_groups = True


page_sequence = [
    InstructionPage,
    game,
    BasePayoff,
    DecisionWaitPage,
    Results,
    RoundWaitPage,
]
