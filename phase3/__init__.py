# models

from otree.api import *
from settings import DEBUG
from reasoning_rounds import draw_reasoning_rounds
# from settings import num_participant

class C(BaseConstants):
    NAME_IN_URL = 'phase3'
    PLAYERS_PER_GROUP = 2 #if DEBUG else int(num_participant)
    NUM_ROUNDS = 3 if DEBUG else 10
    Winner_Reward = 100

class Subsession(BaseSubsession):
    pass

def creating_session(subsession):
    if subsession.round_number == 1:
        subsession.session.vars['phase3_reasoning_rounds'] = draw_reasoning_rounds(
            C.NUM_ROUNDS
        )
    is_reasoning_round = subsession.round_number in subsession.session.vars[
        'phase3_reasoning_rounds'
    ]
    for player in subsession.get_players():
        player.is_reasoning_round = is_reasoning_round

def reasoning_rounds_for(player):
    return player.session.vars['phase3_reasoning_rounds']

class Group(BaseGroup):
    mean_number = models.FloatField()

def set_payoffs(subsession: Subsession): # because we use wait_for_all_groups
    for group in subsession.get_groups():
        final_numbers = {
            p.id_in_group: (
                p.revised_num
                if p.field_maybe_none("revised_num") is not None
                else p.num
            )
            for p in group.get_players()
        }
        all_num = [final_numbers[p.id_in_group] for p in group.get_players()]
        
        group.mean_number = sum(all_num) / C.PLAYERS_PER_GROUP

        for p in group.get_players():
            final_num = final_numbers[p.id_in_group]
            other = p.get_others_in_group()[0]
            other_initial_num = other.num
            other_revised_num = other.field_maybe_none("revised_num")
            p.other_num = other_initial_num
            p.other_revised_num = other_revised_num
            p.target_number = round(0.7 * ((final_num + other_initial_num) / 2), 2)
            p.distance = round(abs(final_num - p.target_number), 2)
            opponent_distance = round(abs(other_initial_num - p.target_number), 2)
            p.bonus_2 = p.distance <= opponent_distance
            p.payoff = cu(C.Winner_Reward if p.bonus_2 else 0)

            p.participant.vars[f'initial_num_2_{p.round_number}'] = p.num
            p.participant.vars[f'revised_num_2_{p.round_number}'] = p.field_maybe_none("revised_num")
            p.participant.vars[f'num_2_{p.round_number}'] = final_num
            p.participant.vars[f'other_num_2_{p.round_number}'] = p.other_num
            p.participant.vars[f'other_revised_num_2_{p.round_number}'] = other_revised_num
            p.participant.vars[f'reason_2_{p.round_number}'] = p.reason if p.round_number in reasoning_rounds_for(p) else None
            p.participant.vars[f'payoff_2_{p.round_number}'] = p.payoff
            p.participant.vars[f'bonus_2_{p.round_number}'] = p.bonus_2
            p.participant.vars['phase3_reasoning_rounds'] = reasoning_rounds_for(p)

class Player(BasePlayer):
    target_number = models.FloatField()
    num = models.IntegerField(
        min = 0,
        max = 100,
        label = "請選擇您的數字：",
    )
    revised_num = models.IntegerField(
        min = 0,
        max = 100,
        blank=True,
        label = "請重新選擇數字：",
    )
    other_num = models.IntegerField(
        min=0, 
        max=100
    )
    other_revised_num = models.IntegerField(
        min=0, 
        max=100, 
        blank=True
    )
    distance = models.FloatField()
    reason = models.LongStringField(
        label = "請說明您選擇該數字的理由：",
        initial = "",
        rows = 5
    )
    is_reasoning_round = models.BooleanField(initial=False)
    bonus_2 = models.BooleanField(
        initial = False
    )

##############################################################################

# pages

from otree.api import *

class InstructionPage(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1
    
    def vars_for_template(player):
        num_player_per_group = C.PLAYERS_PER_GROUP
        return {
            "group_size": int(num_player_per_group)
        }

class Phase3StartWaitPage(WaitPage):
    title_text = "請等待其他受試者完成準備"

    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

class p_beauty(Page):
    form_model = 'player'
    form_fields = ['num']

    @staticmethod
    def is_displayed(player):
        return True


class reasoningWaitPage(WaitPage):
    title_text = "請等待其他受試者完成決策"

    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player):
        return player.round_number in reasoning_rounds_for(player)


class p_beauty_reasoning(Page):
    form_model = 'player'
    form_fields = ['revised_num', 'reason']

    @staticmethod
    def is_displayed(player):
        return player.round_number in reasoning_rounds_for(player)

    @staticmethod
    def vars_for_template(player):
        return {"number_choices": range(0, 101)}
    
    # block forbidden inputs
    @staticmethod
    def error_message(player, values):
        revised_num = values.get('revised_num')
        if revised_num is not None and revised_num == player.num:
            return "重新選擇的數字不可與原先選擇相同。"

        content = values['reason'].strip() # .strip removes leading/trailing blankspace

        if len(content) == 0: 
            return "請填寫您的決策理由。"

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
            g = p.group
            final_num = (
                p.revised_num
                if p.field_maybe_none("revised_num") is not None
                else p.num
            )
            other_revised_num = p.field_maybe_none("other_revised_num")
            other_final_num = (
                other_revised_num
                if other_revised_num is not None
                else p.other_num
            )
            comparison_target = round(
                0.7 * ((final_num + other_final_num) / 2), 2
            )
            comparison_winner = (
                abs(final_num - comparison_target)
                <= abs(other_final_num - comparison_target)
            )
            history.append({
                'round': p.round_number,
                'initial_num': f"{p.num}",
                'revised_num': p.field_maybe_none("revised_num"),
                'num': f"{p.revised_num if p.field_maybe_none('revised_num') is not None else p.num}",
                'other_num': p.other_num,
                'other_changed': other_revised_num is not None,
                'other_revised_num': other_revised_num,
                'other_final_num': other_final_num,
                'mean': f"{g.mean_number:.2f}",
                "target": f"{p.target_number:.2f}",
                "reason": player.in_round(p.round_number).reason if g.round_number in reasoning_rounds else None,
                'is_current': p.round_number == player.round_number,
                'is_reasoning_round': p.round_number in reasoning_rounds,
                'bonus': player.in_round(p.round_number).bonus_2,
                'round_payoff': player.in_round(p.round_number).payoff,
                'comparison_target': f"{comparison_target:.2f}",
                'comparison_winner': comparison_winner,
                'comparison_payoff': cu(
                    C.Winner_Reward if comparison_winner else 0
                )
            })

        if player.round_number == C.NUM_ROUNDS:
            round_payoffs = {r: player.in_round(r).payoff for r in range(1, C.NUM_ROUNDS + 1)}
            sum_payoffs = sum(round_payoffs.values())

            player.participant.vars["phase3_round_payoffs"] = round_payoffs
            player.participant.vars["phase3_sum_payoffs"] = sum_payoffs
            player.participant.vars["phase3_history"] = history
            
        return {
            'history': history
        }
    

class ResultsWaitPage(WaitPage):
    title_text = "請等待其他受試者確認結果"

    wait_for_all_groups = True

page_sequence = [
    InstructionPage, 
    Phase3StartWaitPage,
    p_beauty, 
    reasoningWaitPage,
    p_beauty_reasoning,
    DecisionWaitPage,
    Results,
    ResultsWaitPage
]
