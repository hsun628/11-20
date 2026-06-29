# models

from otree.api import *
from settings import DEBUG
# from settings import num_participant

class C(BaseConstants):
    NAME_IN_URL = 'after_questionaire'
    PLAYERS_PER_GROUP = 2 # if DEBUG else int(num_participant)
    NUM_ROUNDS = 3 if DEBUG else 10
    Prediction_Reward = 50
    reasoning_rounds = [1, 3] if DEBUG else [1, 4, 7, 10]
    exchange_rate = 0.25   # exchange rate for NTD
    participation_fee = 150

class Subsession(BaseSubsession):
    def creating_session(self):
        if self.round_number == 1:
            self.group_like_round("phase_1", 1)

class Group(BaseGroup):
    pass

def calculate_results(group:Group):
    for p in group.get_players():
        tp = [player for player in p.subsession.get_players() if player.id_in_subsession == p.tp_id][0]
        history = tp.participant.vars.get("reason_history", [])

        current_entry = None
        for entry in history:
            if entry.get("round") == p.round_number:
                current_entry = entry
                break
        
        if current_entry:
            real_winner_type = current_entry.get("winner_type")
            is_correct = False

            if p.prediction == "Tie":
                is_correct = (real_winner_type == "Tie")
            else:
                if not p.is_flipped:
                    if (p.prediction == "A" and real_winner_type == "Human") or \
                       (p.prediction == "B" and real_winner_type == "AI"):
                        is_correct = True
                else:
                    if (p.prediction == "A" and real_winner_type == "AI") or \
                       (p.prediction == "B" and real_winner_type == "Human"):
                        is_correct = True

            p.payoff = cu(C.Prediction_Reward) if is_correct else cu(0)
    
class Player(BasePlayer):  
    prediction = models.StringField(
        choices = ["A", "Tie", "B"],
        widget = widgets.RadioSelectHorizontal,
    )

    tp_id = models.IntegerField()
    is_flipped = models.BooleanField()


#############################################################################

# pages

from otree.api import *
import random

class InstructionPage(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

class questionaireStartWaitPage(WaitPage):
    title_text = "請等待其他受試者完成準備"

    wait_for_all_groups = True

class Prediction(Page):
    form_model = 'player'
    form_fields = ['prediction']

    @staticmethod
    def is_displayed(player):
        if player.field_maybe_none("is_flipped") is None:
            player.is_flipped = random.choice([True, False])
        return player.round_number in C.reasoning_rounds

    @staticmethod
    def vars_for_template(player):
        if player.field_maybe_none("tp_id") is None:
            others = player.get_others_in_group()
            target = random.choice(others)   
            player.tp_id = target.id_in_subsession
        
        tp = player.subsession.get_players()[player.tp_id - 1]
           
        history = tp.participant.vars.get("reason_history",[])
        current_entry = next(
            (entry for entry in history if entry.get("round") == player.round_number),
            {"human_reason": "NaN", "gpt_reason": "NaN", "winner_type": "NaN"}
        )

        target_decision = tp.participant.vars.get(f'decision_{player.round_number}') 

        if player.is_flipped:
            reason_a = current_entry.get("gpt_reason")
            reason_b = current_entry.get("human_reason")
        else:
            reason_a = current_entry.get("human_reason")
            reason_b = current_entry.get("gpt_reason")
        
        player.participant.vars[f"reason_a_{player.round_number}"] = reason_a
        player.participant.vars[f"reason_b_{player.round_number}"] = reason_b

        reasoning_round_num = C.reasoning_rounds.index(player.round_number) + 1

        return {
            "round_number": player.round_number,
            "tp_id": player.tp_id,
            "target_decision": target_decision,
            "reason_a": reason_a,
            "reason_b": reason_b,
            "reason_history": current_entry,
            "reasoning_round_num": reasoning_round_num
        }

class PredictionWaitPage(WaitPage):
    title_text = "請等待其他受試者完成預測"
    
    @staticmethod
    def is_displayed(player):
        return player.round_number in C.reasoning_rounds

    after_all_players_arrive = 'calculate_results'


class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number in C.reasoning_rounds
    
    @staticmethod
    def vars_for_template(player):
        tp_id = player.tp_id 
        prediction = player.prediction

        all_players = player.subsession.get_players()
        tp = all_players[tp_id - 1]

        history = tp.participant.vars.get("reason_history", [])

        current_entry = next((e for e in history if e.get("round") == player.round_number), {})
        real_winner = current_entry.get("winner_type")

        is_correct = False
        if prediction == "Tie":
            is_correct = (real_winner == "Tie")
        elif prediction == "A":
            is_correct = (real_winner == "AI") if player.is_flipped else (real_winner == "Human")
        elif prediction == "B":
            is_correct = (real_winner == "Human") if player.is_flipped else (real_winner == "AI")

        result_text = "正確" if is_correct else "錯誤"

        reasoning_round_num = C.reasoning_rounds.index(player.round_number) + 1

        return {
            "reason_a": player.participant.vars[f"reason_a_{player.round_number}"],
            "reason_b": player.participant.vars[f"reason_b_{player.round_number}"],
            "real_winner": real_winner,
            "is_correct": is_correct,
            "result_text": result_text,
            "reasoning_round_num": reasoning_round_num
        }

class Payoff(Page):
    title_text = "感謝您參加本實驗，請確認您的報酬金額。"

    @staticmethod
    def vars_for_template(player):
        if player.round_number == C.NUM_ROUNDS:
            if 'points_before_fee' not in player.participant.vars:
                player.participant.vars['points_before_fee'] = player.participant.payoff
            
            if not player.participant.vars.get("fee_added"):
                player.participant.payoff = player.participant.payoff*C.exchange_rate + cu(C.participation_fee)
                player.participant.vars["fee_added"] = True

        return {
            "total_payoff_no_participation_fee": int(player.participant.vars.get('points_before_fee')),
            "total_NTD_payoff": player.participant.payoff
        }
    
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
    
class redirect_to_form(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS


page_sequence = [
    InstructionPage,
    questionaireStartWaitPage,
    Prediction,
    PredictionWaitPage,
    Results,
    Payoff,
    redirect_to_form
]
