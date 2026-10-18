# models

from otree.api import *
from settings import DEBUG
from reasoning_rounds import draw_reasoning_rounds
# from settings import num_participant

class C(BaseConstants):
    NAME_IN_URL = 'phase2'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 3 if DEBUG else 10
class Subsession(BaseSubsession):
    pass

def creating_session(subsession):
    if subsession.round_number == 1:
        subsession.session.vars['phase2_reasoning_rounds'] = draw_reasoning_rounds(
            C.NUM_ROUNDS
        )
    subsession.group_randomly()
    is_reasoning_round = subsession.round_number in subsession.session.vars[
        'phase2_reasoning_rounds'
    ]
    for player in subsession.get_players():
        player.is_reasoning_round = is_reasoning_round

def reasoning_rounds_for(player):
    return player.session.vars['phase2_reasoning_rounds']

class Group(BaseGroup):
    pass

def set_payoffs(group: Group): # because we use wait_for_all_groups
    for p in group.get_players():
        other = p.get_others_in_group()[0]
        final_num = p.revised_num if p.field_maybe_none("revised_num") is not None else p.num
        other_revised_num = other.field_maybe_none("revised_num")
        p.other_num = other.num
        p.other_revised_num = other_revised_num

        p.bonus = final_num == other.num - 1

        p.payoff = cu(final_num)
        if p.bonus == True:
            p.payoff += cu(20) 

        p.participant.vars[f"initial_num_{p.round_number}"] = p.num
        p.participant.vars[f"revised_num_{p.round_number}"] = p.field_maybe_none("revised_num")
        p.participant.vars[f"num_{p.round_number}"] = final_num
        p.participant.vars[f"other_num_{p.round_number}"] = other.num
        p.participant.vars[f"other_revised_num_{p.round_number}"] = other_revised_num
        p.participant.vars[f"reason_{p.round_number}"] = (
            p.reason if p.round_number in reasoning_rounds_for(p) else None
        )
        p.participant.vars[f"bonus_{p.round_number}"] = p.bonus
        p.participant.vars['phase2_reasoning_rounds'] = reasoning_rounds_for(p)

class Player(BasePlayer):
    num = models.IntegerField(
        min = 11,
        max = 20,
        label = "請選擇您的數字：",
    )
    revised_num = models.IntegerField(
        min = 11,
        max = 20,
        blank=True,
        label = "請重新選擇數字：",
    )
    other_num = models.IntegerField(
        min = 11,
        max = 20,
    )
    other_revised_num = models.IntegerField(
        min=11,
        max=20,
        blank=True,
    )
    reason = models.LongStringField(
        label = "請說明您選擇該數字的理由：",
        initial = "",
        rows = 3
    )
    is_reasoning_round = models.BooleanField(initial=False)
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

    @staticmethod
    def is_displayed(player):
        return True

    @staticmethod
    def vars_for_template(player):
        return {"number_choices": range(11, 21)}


class reasoningWaitPage(WaitPage):
    title_text = "請等待其他受試者完成決策"

    wait_for_all_groups = True

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

    # block forbidden inputs
    @staticmethod
    def error_message(player, values):
        revised_num = values.get('revised_num')
        if revised_num is not None and revised_num == player.num:
            return "重新選擇的數字不可與原先選擇相同。"

        content = values['reason'].strip() # .strip removes leading/trailing blankspace

        if len(content) == 0: # block empty input
            return "理由欄位不能為空，請輸入您的決策思考過程。"

        if len(set(content)) < 3 and len(content) > 0: # block too short, single-word, or repetitive inputs
            return "請勿輸入過短、單一，或重複的文字內容。"
        

class DecisionWaitPage(WaitPage):
    title_text = "請等待其他受試者完成決策"

    wait_for_all_groups = True
    after_all_players_arrive = 'set_payoffs'

class Results(Page):
    @staticmethod
    def vars_for_template(player):
        player_history = player.in_all_rounds()
        history = []
        reasoning_rounds = reasoning_rounds_for(player)

        for p in player_history:
            history.append({
                'round': p.round_number,
                'initial_num': f"{p.num}",
                'revised_num': p.field_maybe_none("revised_num"),
                'num': f"{p.revised_num if p.field_maybe_none('revised_num') is not None else p.num}",
                "other_num": f"{player.in_round(p.round_number).other_num}",
                "other_changed": p.field_maybe_none("other_revised_num") is not None,
                "other_revised_num": p.field_maybe_none("other_revised_num"),
                "reason": (
                    player.in_round(p.round_number).reason
                    if p.round_number in reasoning_rounds else None
                ),
                'is_current': p.round_number == player.round_number,
                'is_reasoning_round': p.round_number in reasoning_rounds,
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
    title_text = "請等待其他受試者確認結果"

    wait_for_all_groups = True

page_sequence = [
    InstructionPage, 
    Phase2StartWaitPage,
    game, 
    reasoningWaitPage,
    game_with_reason,
    DecisionWaitPage,
    Results,
    ResultsWaitPage
]
