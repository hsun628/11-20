# models

from otree.api import *
from settings import DEBUG
# from settings import num_participant

class C(BaseConstants):
    NAME_IN_URL = 'phase2'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 3 if DEBUG else 10
    reasoning_rounds = [1, 3] if DEBUG else [1, 4, 7, 10]

class Subsession(BaseSubsession):
    pass

def creating_session(subsession):
    subsession.group_randomly()

import random

class Group(BaseGroup):
    pass

def set_payoffs(group: Group): # because we use wait_for_all_groups
    for p in group.get_players():
        other = p.get_others_in_group()[0]
        p.other_num = other.num

        if p.num == other.num - 1:
            p.bonus = True

        p.payoff = cu(p.num)
        if p.bonus == True:
            p.payoff += cu(20) 

        p.participant.vars[f"num_{p.round_number}"] = p.num
        p.participant.vars[f"other_num_{p.round_number}"] = other.num
        p.participant.vars[f"reason_{p.round_number}"] = p.reason if p.round_number in C.reasoning_rounds else None
        p.participant.vars[f"bonus_{p.round_number}"] = p.bonus

class Player(BasePlayer):
    num = models.IntegerField(
        min = 11,
        max = 20,
        label = "請選擇您的數字：",
    )
    other_num = models.IntegerField(
        min = 11,
        max = 20,
    )
    reason = models.LongStringField(
        label = "請說明您選擇該數字的理由：",
        initial = ""
    )
    bonus = models.BooleanField(
        initial = False
    )

##############################################################################

# pages

from otree.api import *

class InstructionPage(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

class Phase2StartWaitPage(WaitPage):
    title_text = "請等待其他受試者完成準備"

    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

class game(Page):
    form_model = 'player'
    form_fields = ['num']

class reasoning_roundsWaitPage(WaitPage):
    title_text = "請等待所有受試者完成決策"
    
    wait_for_all_groups = True # wait for all groups before revealing reasoning rounds

    @staticmethod
    def is_displayed(player):
        return player.round_number in C.reasoning_rounds

class reasoning(Page):
    form_model = 'player'
    form_fields = ['reason']

    @staticmethod
    def is_displayed(player):
        return player.round_number in C.reasoning_rounds
    
    # block forbidden inputs
    @staticmethod
    def error_message(player, values):
        content = values['reason'].strip() # .strip removes leading/trailing blankspace

        if len(content) == 0: # block empty input
            return "理由欄位不能為空，請輸入您的決策思考過程。"

        if len(set(content)) < 3 and len(content) > 0: # block too short, single-word, or repetitive inputs
            return "請勿輸入過短、單一，或重複的文字內容。"
        

class DecisionWaitPage(WaitPage):
    title_text = "請等待所有受試者完成決策"

    wait_for_all_groups = True
    after_all_players_arrive = 'set_payoffs'

class Results(Page):
    @staticmethod
    def vars_for_template(player):
        player_history = player.in_all_rounds()
        history = []

        for p in player_history:
            history.append({
                'round': p.round_number,
                'num': f"{player.in_round(p.round_number).num}",
                "other_num": f"{player.in_round(p.round_number).other_num}",
                "reason": player.in_round(p.round_number).reason if p.round_number in C.reasoning_rounds else None,
                'is_current': p.round_number == player.round_number,
                'is_reasoning_round': p.round_number in C.reasoning_rounds,
                'bonus': player.in_round(p.round_number).bonus,
                'round_payoff': player.in_round(p.round_number).payoff
            })

        if player.round_number == C.NUM_ROUNDS:
            round_payoffs = {r: player.in_round(r).payoff for r in range(1, C.NUM_ROUNDS + 1)}
            sum_payoffs = sum(round_payoffs.values())

            player.participant.vars["phase2_round_payoffs"] = round_payoffs
            player.participant.vars["phase2_sum_payoffs"] = sum_payoffs
            player.participant.vars["phase2_history"] = history
            
        return {
            'history': history
        }
    

class ResultsWaitPage(WaitPage):
    title_text = "請等待所有受試者確認結果"

    wait_for_all_groups = True

page_sequence = [
    InstructionPage, 
    Phase2StartWaitPage,
    game, 
    reasoning_roundsWaitPage,
    reasoning,
    DecisionWaitPage,
    Results,
    ResultsWaitPage
]
