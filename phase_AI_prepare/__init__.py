from otree.api import *
from phase_AI import C as AIC
from phase_AI import gpt_generate, gpt_judge
import random
import time
import threading


class C(BaseConstants):
    NAME_IN_URL = "phase_AI_prepare"
    PLAYERS_PER_GROUP = AIC.PLAYERS_PER_GROUP
    NUM_ROUNDS = AIC.NUM_ROUNDS
    reasoning_rounds_p2 = AIC.reasoning_rounds_p2
    reasoning_rounds_p3 = AIC.reasoning_rounds_p3
    experimental_rules = AIC.experimental_rules
    experimental_rules_2 = AIC.experimental_rules_2
    Pass_Reward_p2 = AIC.Pass_Reward_p2
    Pass_Reward_p3 = AIC.Pass_Reward_p3


class Subsession(BaseSubsession):
    def creating_session(self):
        if self.round_number == 1:
            self.group_like_round("phase_1", 1)


class Group(BaseGroup):
    pass


_thread_storage = {}


class Player(BasePlayer):
    is_gpt_finished = models.BooleanField(initial=False)
    gpt_reason = models.LongStringField()
    gpt_analysis = models.LongStringField()
    winner_type = models.StringField()
    gpt_reason_2 = models.LongStringField()
    gpt_analysis_2 = models.LongStringField()
    winner_type_2 = models.StringField()

    def gpt_process(self, participant_vars):
        p_id = participant_vars["id_in_subsession"]
        phase2_history = [dict(h) for h in participant_vars.get("phase2_history", [])]
        phase3_history = [dict(h) for h in participant_vars.get("phase3_history", [])]
        phase2_lookup = {h["round"]: h for h in phase2_history}
        phase3_lookup = {h["round"]: h for h in phase3_history}
        phase2_payoffs = participant_vars.get("phase2_round_payoffs", {})
        phase3_payoffs = participant_vars.get("phase3_round_payoffs", {})
        final_phase2 = {r: cu(phase2_payoffs.get(r, 0)) for r in range(1, C.NUM_ROUNDS + 1)}
        final_phase3 = {r: cu(phase3_payoffs.get(r, 0)) for r in range(1, C.NUM_ROUNDS + 1)}
        p2_db_data = {}
        p3_db_data = {}

        try:
            time.sleep((p_id - 1) * 0.5)
            for r in range(1, C.NUM_ROUNDS + 1):
                current = phase2_lookup.get(r)
                human_reason = str(participant_vars.get(f"reason_{r}") or "").strip()
                human_num = participant_vars.get(f"num_{r}")
                if r in C.reasoning_rounds_p2 and current and human_reason and human_num is not None:
                    target_is_flipped = random.choice([True, False])
                    gpt_reason = current.get("gpt_reason") or gpt_generate(C.experimental_rules, r, human_num)
                    winner, analysis = gpt_judge(C.experimental_rules, human_reason, gpt_reason, target_is_flipped)
                    original = cu(phase2_payoffs.get(r, 0))
                    final = cu(C.Pass_Reward_p2) if winner in ["Human", "Tie"] else cu(0)
                    final_phase2[r] = final
                    current.update({
                        "human_reason": human_reason, "gpt_reason": gpt_reason,
                        "winner_type": winner,
                        "result_text": "您的理由較具體" if winner in ["Human", "Tie"] else "AI生成的理由較具體",
                        "final_payoff": final,
                    })
                    p2_db_data[r] = {
                        "is_flipped": target_is_flipped, "gpt_reason": gpt_reason,
                        "gpt_analysis": analysis, "winner_type": winner,
                        "payoff_adj": final - original,
                    }

                current = phase3_lookup.get(r)
                human_reason = str(participant_vars.get(f"reason_2_{r}") or "").strip()
                human_num = participant_vars.get(f"num_2_{r}")
                if r in C.reasoning_rounds_p3 and current and human_reason and human_num is not None:
                    target_is_flipped = random.choice([True, False])
                    gpt_reason = current.get("gpt_reason_2") or gpt_generate(C.experimental_rules_2, r, human_num)
                    winner, analysis = gpt_judge(C.experimental_rules_2, human_reason, gpt_reason, target_is_flipped)
                    original = cu(phase3_payoffs.get(r, 0))
                    final = cu(C.Pass_Reward_p3) if winner in ["Human", "Tie"] else cu(0)
                    final_phase3[r] = final
                    current.update({
                        "human_reason_2": human_reason, "gpt_reason_2": gpt_reason,
                        "winner_type_2": winner,
                        "result_text_2": "您的理由較具體" if winner in ["Human", "Tie"] else "AI生成的理由較具體",
                        "final_payoff_2": final,
                    })
                    p3_db_data[r] = {
                        "is_flipped_2": target_is_flipped, "gpt_reason_2": gpt_reason,
                        "gpt_analysis_2": analysis, "winner_type_2": winner,
                        "payoff_adj_2": final - original,
                    }

            _thread_storage[p_id] = {
                "status": "done",
                "phase2_history": phase2_history,
                "phase3_history": phase3_history,
                "total_phase2_payoff": sum(final_phase2.values()),
                "total_phase3_payoff": sum(final_phase3.values()),
                "p2_db_data": p2_db_data,
                "p3_db_data": p3_db_data,
            }
        except Exception as exc:
            print(f"AI processing failed for participant {p_id}: {exc}")
            _thread_storage[p_id] = {
                "status": "error",
                "error": "AI processing failed. Check the server log for details.",
            }


class InstructionPage(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class Phase3CompleteWaitPage(WaitPage):
    title_text = "請等待所有受試者完成實驗第三部分"
    wait_for_all_groups = True


class ProcessingPage(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def live_method(player, data):
        p_id = player.id_in_subsession

        if data.get("type") == "API_start":
            if not player.is_gpt_finished and p_id not in _thread_storage:
                participant_vars = dict(player.participant.vars)
                participant_vars["id_in_subsession"] = p_id
                thread = threading.Thread(target=player.gpt_process, args=(participant_vars,))
                thread.daemon = True
                thread.start()
            return {player.id_in_group: {"status": "started"}}

        if data.get("type") == "check_status":
            output = _thread_storage.get(p_id)
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

                for r, values in output["p3_db_data"].items():
                    target = player.in_round(int(r))
                    target.gpt_reason_2 = values["gpt_reason_2"]
                    target.gpt_analysis_2 = values["gpt_analysis_2"]
                    target.winner_type_2 = values["winner_type_2"]

                player.is_gpt_finished = True
                del _thread_storage[p_id]
                return {player.id_in_group: {"status": "finished"}}
            if output and output.get("status") == "error":
                del _thread_storage[p_id]
                return {player.id_in_group: {"status": "error", "message": output["error"]}}

            return {player.id_in_group: {"status": "processing"}}


class PrepareWaitPage(WaitPage):
    title_text = "請等待AI處理所有受試者理由"
    wait_for_all_groups = True


page_sequence = [
    Phase3CompleteWaitPage,
    InstructionPage,
    ProcessingPage,
    PrepareWaitPage,
]
