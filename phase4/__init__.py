# models

from otree.api import *
from settings import DEBUG
from . import ai_processing
import threading
from settings import num_participant

class C(BaseConstants):
    NAME_IN_URL = 'phase4'
    PLAYERS_PER_GROUP = 4  if DEBUG else int(num_participant)
    # Keep source-round indices for storing AI results against the original rounds.
    NUM_ROUNDS = ai_processing.C.NUM_ROUNDS
    Prediction_Reward = 40

    exchange_rate = 0.25   # exchange rate for NTD
    participation_fee = 150

def reasoning_rounds_p2_for(player):
    return player.participant.vars["phase2_reasoning_rounds"]

def prediction_rounds_p2_for(player):
    return list(range(1, len(reasoning_rounds_p2_for(player)) + 1))


def basic_source_round_for_prediction(player, prediction_round):
    reasoning_rounds = reasoning_rounds_p2_for(player)
    if prediction_round < 1 or prediction_round > len(reasoning_rounds):
        raise ValueError(
            f"Prediction round {prediction_round} is outside the Basic schedule."
        )
    return reasoning_rounds[prediction_round - 1]


def eligible_prediction_targets(player, prediction_round):
    schedule_id = player.participant.vars["phase2_reasoning_schedule_id"]
    eligible_targets = []
    for candidate in player.subsession.get_players():
        if candidate.id_in_subsession == player.id_in_subsession:
            continue
        if candidate.participant.vars.get(
            "phase2_reasoning_schedule_id"
        ) != schedule_id:
            continue

        source_round = basic_source_round_for_prediction(
            candidate, prediction_round
        )
        history = candidate.participant.vars.get("phase2_history", [])
        if any(
            entry.get("round") == source_round
            and entry.get("human_reason")
            and entry.get("gpt_reason")
            for entry in history
        ):
            eligible_targets.append((candidate, source_round))
    return eligible_targets


def reasoning_rounds_p3_for(player):
    return player.participant.vars["phase3_reasoning_rounds"]

class Subsession(BaseSubsession):
    def creating_session(self):
        if self.round_number > 1:
            self.group_like_round(1)

class Group(BaseGroup):
    pass

def calculate_results(group:Group):
    for p in group.get_players():
        p.is_correct = False
        p.payoff = cu(0)

        if (
            p.round_number not in prediction_rounds_p2_for(p)
            or p.field_maybe_none("tp_id") is None
        ):
            continue

        tp = [player for player in p.subsession.get_players() if player.id_in_subsession == p.tp_id][0]
        source_round = p.field_maybe_none("basic_source_round")
        if source_round is None:
            source_round = basic_source_round_for_prediction(tp, p.round_number)
            p.basic_source_round = source_round
        history = tp.participant.vars.get("phase2_history", [])

        current_entry = None
        for entry in history:
            if entry.get("round") == source_round:
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

            p.is_correct = is_correct
            p.payoff = cu(C.Prediction_Reward) if is_correct else cu(0)
    
class Player(BasePlayer):  
    is_gpt_finished = models.BooleanField(initial=False)
    payoff_by_reasoning = models.BooleanField(blank=True)
    payoff_by_reasoning_2 = models.BooleanField(blank=True)
    gpt_reason = models.LongStringField()
    gpt_analysis = models.LongStringField()
    winner_type = models.StringField()
    gpt_reason_2 = models.LongStringField()
    gpt_analysis_2 = models.LongStringField()
    winner_type_2 = models.StringField()
    is_correct = models.BooleanField(initial=False)
    prediction = models.StringField(
        choices = ["A", "Tie", "B"],
        widget = widgets.RadioSelectHorizontal,
    )

    tp_id = models.IntegerField()
    basic_source_round = models.IntegerField(blank=True)
    is_flipped = models.BooleanField()


#############################################################################

# pages

from otree.api import *
import random

class InstructionPage(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class ProcessingPage(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def live_method(player, data):
        p_id = player.id_in_subsession

        if data.get("type") == "API_start":
            if not player.is_gpt_finished and p_id not in ai_processing._thread_storage:
                participant_vars = dict(player.participant.vars)
                participant_vars["id_in_subsession"] = p_id
                participant_vars["phase2_reasoning_rounds"] = (
                    player.participant.vars["phase2_reasoning_rounds"]
                )
                participant_vars["phase3_reasoning_rounds"] = (
                    player.participant.vars["phase3_reasoning_rounds"]
                )
                thread = threading.Thread(
                    target=ai_processing.AIProcessor().gpt_process,
                    args=(participant_vars,),
                )
                thread.daemon = True
                thread.start()
            return {player.id_in_group: {"status": "started"}}

        if data.get("type") == "check_status":
            output = ai_processing._thread_storage.get(p_id)
            if output and output.get("status") == "done":
                player.participant.vars["phase2_history"] = output["phase2_history"]
                player.participant.vars["phase3_history"] = output["phase3_history"]
                player.participant.vars["total_phase2_payoff"] = output["total_phase2_payoff"]
                player.participant.vars["total_phase3_payoff"] = output["total_phase3_payoff"]
                player.participant.vars["ai_p2_db_data"] = output["p2_db_data"]
                player.participant.vars["ai_p3_db_data"] = output["p3_db_data"]

                for r, values in output["p2_db_data"].items():
                    target = player.in_round(int(r))
                    target.gpt_reason = values["gpt_reason"]
                    target.gpt_analysis = values["gpt_analysis"]
                    target.winner_type = values["winner_type"]
                    target.payoff_by_reasoning = values["payoff_by_reasoning"]

                for r, values in output["p3_db_data"].items():
                    target = player.in_round(int(r))
                    target.gpt_reason_2 = values["gpt_reason_2"]
                    target.gpt_analysis_2 = values["gpt_analysis_2"]
                    target.winner_type_2 = values["winner_type_2"]
                    target.payoff_by_reasoning_2 = values["payoff_by_reasoning_2"]

                player.is_gpt_finished = True
                del ai_processing._thread_storage[p_id]
                return {player.id_in_group: {"status": "finished"}}
            if output and output.get("status") == "error":
                del ai_processing._thread_storage[p_id]
                return {player.id_in_group: {"status": "error", "message": output["error"]}}

            return {player.id_in_group: {"status": "processing"}}


class PrepareWaitPage(WaitPage):
    title_text = "請等待AI處理其他受試者理由"
    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class Prediction(Page):
    form_model = 'player'
    form_fields = ['prediction']

    @staticmethod
    def is_displayed(player):
        if player.round_number in prediction_rounds_p2_for(player):
            if player.field_maybe_none("is_flipped") is None:
                player.is_flipped = random.choice([True, False])
            return True
        return False

    @staticmethod
    def vars_for_template(player):
        if player.field_maybe_none("tp_id") is None:
            eligible_targets = eligible_prediction_targets(
                player, player.round_number
            )
            if not eligible_targets:
                raise ValueError(
                    "No other participant in the same reasoning schedule has "
                    "complete Basic reasoning data for prediction round "
                    f"{player.round_number}."
                )
            target, source_round = random.choice(eligible_targets)
            player.tp_id = target.id_in_subsession
            player.basic_source_round = source_round

        tp = next(
            participant
            for participant in player.subsession.get_players()
            if participant.id_in_subsession == player.tp_id
        )
        source_round = player.field_maybe_none("basic_source_round")
        if source_round is None:
            source_round = basic_source_round_for_prediction(
                tp, player.round_number
            )
            player.basic_source_round = source_round

        history = tp.participant.vars.get("phase2_history",[])
        current_entry = next(
            (entry for entry in history if entry.get("round") == source_round),
            {"human_reason": "NaN", "gpt_reason": "NaN", "winner_type": "NaN"}
        )

        target_num = tp.participant.vars.get(f'num_{source_round}')

        if player.is_flipped:
            reason_a = current_entry.get("gpt_reason")
            reason_b = current_entry.get("human_reason")
        else:
            reason_a = current_entry.get("human_reason")
            reason_b = current_entry.get("gpt_reason")
        
        player.participant.vars[f"reason_a_{player.round_number}"] = reason_a
        player.participant.vars[f"reason_b_{player.round_number}"] = reason_b

        reasoning_round_num = (
            prediction_rounds_p2_for(player).index(player.round_number) + 1
        )

        return {
            "round_number": player.round_number,
            "source_round": source_round,
            "tp_id": player.tp_id,
            "target_num": target_num,
            "reason_a": reason_a,
            "reason_b": reason_b,
            "reason_history": current_entry,
            "reasoning_round_num": reasoning_round_num
        }

class PredictionWaitPage(WaitPage):
    title_text = "請等待其他受試者完成預測"
    
    @staticmethod
    def is_displayed(player):
        return player.round_number in prediction_rounds_p2_for(player)

    after_all_players_arrive = 'calculate_results'


class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number in prediction_rounds_p2_for(player)
    
    @staticmethod
    def vars_for_template(player):
        tp_id = player.tp_id 
        all_players = player.subsession.get_players()
        tp = next(
            participant
            for participant in all_players
            if participant.id_in_subsession == tp_id
        )

        history = tp.participant.vars.get("phase2_history", [])

        source_round = player.field_maybe_none("basic_source_round")
        if source_round is None:
            source_round = basic_source_round_for_prediction(
                tp, player.round_number
            )
        current_entry = next((e for e in history if e.get("round") == source_round), {})
        real_winner = current_entry.get("winner_type")

        result_text = "正確" if player.is_correct else "錯誤"

        reasoning_round_num = (
            prediction_rounds_p2_for(player).index(player.round_number) + 1
        )

        return {
            "reason_a": player.participant.vars[f"reason_a_{player.round_number}"],
            "reason_b": player.participant.vars[f"reason_b_{player.round_number}"],
            "real_winner": real_winner,
            "is_correct": player.is_correct,
            "result_text": result_text,
            "reasoning_round_num": reasoning_round_num
        }

class AIResults(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player):
        phase2_history = player.participant.vars.get("phase2_history", [])
        phase2_round_payoffs = player.participant.vars.get("phase2_round_payoffs", {})
        ai_p2_db_data = player.participant.vars.get("ai_p2_db_data", {})
        reasoning_rounds_p2 = reasoning_rounds_p2_for(player)
        for entry in phase2_history:
            entry["is_reasoning_round"] = entry.get("round") in reasoning_rounds_p2
            entry["result_text"] = entry.get("result_text", "-")
            round_number = entry.get("round")
            db_entry = ai_p2_db_data.get(
                round_number, ai_p2_db_data.get(str(round_number), {})
            )
            entry["payoff_by_reasoning"] = entry.get(
                "payoff_by_reasoning", db_entry.get("payoff_by_reasoning")
            )
            if entry.get("final_payoff") is None:
                entry["final_payoff"] = cu(
                    phase2_round_payoffs.get(round_number, 0)
                )

        phase3_history = player.participant.vars.get("phase3_history", [])
        phase3_round_payoffs = player.participant.vars.get("phase3_round_payoffs", {})
        ai_p3_db_data = player.participant.vars.get("ai_p3_db_data", {})
        reasoning_rounds_p3 = reasoning_rounds_p3_for(player)
        for entry in phase3_history:
            entry["is_reasoning_round"] = entry.get("round") in reasoning_rounds_p3
            entry["result_text_2"] = entry.get("result_text_2", "-")
            entry["bonus"] = entry.get("bonus", entry.get("bonus_2", False))
            entry["payoff_basis_2"] = entry.get("payoff_basis_2", "-")
            round_number = entry.get("round")
            db_entry = ai_p3_db_data.get(
                round_number, ai_p3_db_data.get(str(round_number), {})
            )
            entry["payoff_by_reasoning_2"] = entry.get(
                "payoff_by_reasoning_2", db_entry.get("payoff_by_reasoning_2")
            )
            if entry.get("final_payoff_2") is None:
                entry["final_payoff_2"] = cu(
                    phase3_round_payoffs.get(round_number, 0)
                )

        return {
            "phase2_history": phase2_history,
            "phase3_history": phase3_history,
            "total_phase2_payoff": player.participant.vars.get(
                "total_phase2_payoff", 0
            ),
            "total_phase3_payoff": player.participant.vars.get(
                "total_phase3_payoff", 0
            ),
        }

class Payoff(Page):
    title_text = "感謝您參加本實驗，請確認您的報酬金額。"

    @staticmethod
    def vars_for_template(player):
        if player.round_number == C.NUM_ROUNDS:
            if 'points_before_fee' not in player.participant.vars:
                original_phase2 = player.participant.vars.get("phase2_sum_payoffs", 0)
                original_phase3 = player.participant.vars.get("phase3_sum_payoffs", 0)
                adjusted_phase2 = player.participant.vars.get(
                    "total_phase2_payoff", original_phase2
                )
                adjusted_phase3 = player.participant.vars.get(
                    "total_phase3_payoff", original_phase3
                )
                adjustment = (
                    adjusted_phase2
                    - original_phase2
                    + adjusted_phase3
                    - original_phase3
                )
                player.participant.vars['points_before_fee'] = (
                    player.participant.payoff + adjustment
                )
            
            if not player.participant.vars.get("fee_added"):
                player.participant.payoff = (
                    player.participant.vars['points_before_fee'] * C.exchange_rate
                    + cu(C.participation_fee)
                )
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
    ProcessingPage,
    PrepareWaitPage,
    Prediction,
    PredictionWaitPage,
    Results,
    AIResults,
    Payoff,
    redirect_to_form
]
