from otree.api import *
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import random
import time
import threading

from settings import DEBUG


load_dotenv()

my_api_key = os.getenv("api_key")
model_used = "gpt-5.4"
client = OpenAI(api_key=my_api_key)


class C(BaseConstants):
    NAME_IN_URL = "phase_AI_prepare"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 3 if DEBUG else 10
    Pass_Reward_p2 = 40
    Pass_Reward_p3 = 40
    reasoning_rounds_p2 = [1, 3] if DEBUG else [1, 4, 7, 10]
    reasoning_rounds_p3 = [1, 3] if DEBUG else [1, 5, 10]

    experimental_rules = """
        * Part II consists of 10 rounds. At the beginning of this part, the computer will randomly assign all participants into groups of two.
        * In each round, both you and the other participant in your group (hereafter referred to as your "opponent") must choose an integer between 11 and 20. Both you and the opponent will receive an amount of experimental currency equal to the number each chooses. If your chosen number is exactly one less than your opponent's, then you are the "winner" and will receive an additional 20 units of experimental currency.
        * At the end of each round, the computer will display both players' chosen numbers for that round, whether you are the winner, and your payoff for each round.
        """
    experimental_rules_2 = """
        * Part III consists of 10 rounds. At the beginning, the computer randomly divides all participants into groups, and the number of participants in each group will be displayed on the screen.
        * In each round, all participants in your group must choose an integer between 0 and 100.
        * The average of all numbers chosen by participants in your group is called the "Average Number."
        * The person whose choice is closest to **0.7 times the Average Number** (called the "Target Number") is the "winner" of the round and will receive a 100 units of experimental currency. In the event of a tie, the computer will randomly select one winner.
        * After each round ends, the computer will display the past "Average Number" and "Target Number" for your group, whether you are the winner, and your payoff for each round.
        """


def gpt_generate(experimental_rules, round_number, participant_decision):
    generate_prompt = f"""

        ### Role:
            You are a college student participating in an economics experiment. Your task is to write a reasoning for a specific decision.

        ### Task:
            You will be presented with a participant's decision from the experiment described below. Based on that decision, write a reasoning (about 30-40 characters in Traditional Chinese, 50 characters at most) explaining the underlying thoughts and the information used for that decision. The reasoning should follow the requirements below:
            * **Requirements**:
                * Your reasoning should include the information and beliefs you observed or used, and demonstrate the process of how you derived the decision from said information and beliefs.
                * The reasoning should sound like a real participant, not like a game theory expert.
                * Do not mention Nash equilibrium, infinite iteration, dominance, or formal strategic terminologies.
                * You may think strategically, but do not fully formalize or optimize the reasoning.* Use natural, conversational language.
                * Some uncertainty is allowed (e.g., “I guess”, “maybe”, “probably”).
                * The reasoning should not look highly sophisticated or mathematically complete.
                * The reasoning should be in accordance with the provided round number.

        ### Experimental Rules:
            {experimental_rules}

        ### Response Format:
            Please provide the participant's decision and the reasoning (in Traditional Chinese) you have written. Your response must strictly follow this JSON format:
            {{
                "round": {round_number},
                "decision": {participant_decision},
                "reasoning": "Your reasoning (about 30 characters in Traditional Chinese) explaining the underlying thoughts and the information used for the decision."
            }}
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model_used,
                messages=[
                    {"role": "system", "content": generate_prompt},
                    {
                        "role": "user",
                        "content": f"""Based on the round number: {round_number} and the provided decision: {participant_decision}, write a reasoning (about 30-40 characters in Traditional Chinese, 50 characters at most) explaining the underlying thoughts and the information used for the decision. Your response must strictly follow the specified JSON format.
                    """,
                    },
                ],
                response_format={"type": "json_object"},
                temperature=1,
                max_completion_tokens=300,
            )

            generate_result = response.choices[0].message.content
            data_generate = json.loads(generate_result)
            return data_generate.get("reasoning")
        except Exception as exc:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"JSON / API error: {exc}")
            return "JSON / API error"


def gpt_judge(experimental_rules, reasoning_1, reasoning_2, is_flipped_value):
    if is_flipped_value:
        reasons = [reasoning_2, reasoning_1]
    else:
        reasons = [reasoning_1, reasoning_2]

    judge_prompt = f"""

    ### Role:
        You are a professional judge. Your task is to evaluate the explanations provided by participants regarding their decision-making process.

    ### Judging Task:
        Compare the reasons provided by the following two participants. Determine which participant more specifically explains the "underlying thoughts" and the "information used" behind their decision.

    ### Evaluation Criteria (Strictly Adhere to the Following):

    * **Information & Belief:** Does the participant mention specific information they observed? Do they state their inferences or hypotheses about the current situation? Did they elaborate on how they arrive at these inferences and hypotheses?

    * **Logic & Strategy:** Does the participant demonstrate the derivation process from the aforementioned information and beliefs to their final decision?
        * **Is the logic consistent with the experimental rules? (Crucial):** Does the claimed causal relationship in the reasoning align with the experimental rules? If the reasoning fundamentally contradicts the rules or physical facts, the reasoning should be considered a "Logical Break." Such a reasoning must receive a lower evaluation than one that is logically self-consistent.

    * **Level of Specificity:** Is the reason specific? (For example: prefer "Because I observed A, I expected B, and therefore adopted strategy C" over "I just picked one" or "I wanted to choose this"). You can further judge based on:
        - Whether the reason contains specific information related to the rules, rather than just a vague description.
        - Whether there are clear causal and logical relationships between sentences.

    ### Strict Prohibitions (Do NOT Consider):

    * **Do NOT judge based on the "quality" or "winning probability" of the decision:** Even if the participant's reasoning contains calculation errors or the decision itself has a very low probability of winning, as long as they clearly and logically explain their thought process, that reason should receive a higher evaluation.
    * **Note:** Your mission is to evaluate "who more specifically explained their underlying thoughts and information used," NOT "how smart the decision was."

    * **Reasoning Length**: Do not judge the specificity or detail of a reason based on its word count. (For example: "Because I observed A, I expected B, and therefore adopted strategy C" and "Under my careful observation, I discovered A, so I expect others to do B; consequently, I decided to adopt strategy C to increase my winning probability" describe the same content. They should receive the same or very similar evaluation).

    * **Do NOT Favor "Self-Invented Jargon":** Participants may use self-invented professional-sounding terms (e.g., "Boundary Suppression Effect," "Group Deviation Law"). Do not award a higher evaluation simply because the reasoning contains these non-standard terms that appear neither in the experimental instruction nor in everyday language.
        - Pay attention to whether the participant explicitly explains the meaning of these invented terms, or whether the terms carry concrete logical weight within their common-sense semantic context.
        - If the reasoning becomes hollow or lacks substance once these terms are removed, the reasoning should receive a lower evaluation.

    ### Experimental instruction:
        {experimental_rules}

    ### Response Format:
        The following are two reasonings for a decision. Please evaluate them based on the judge criterion and prohibition above.

            - reasoning_A: {reasons[0]}
            - reasoning_B: {reasons[1]}

        Please state in the following JSON format which reasoning more specifically explained the underlying thoughts and information used. If the two are extremely close, you may declare a tie.

        {{
            "winner": "reasoning_A" or "reasoning_B" or "Tie",
            "analysis": "A brief reason for your judgement of the winner."
        }}
    """

    response = client.chat.completions.create(
        model=model_used,
        messages=[
            {"role": "system", "content": judge_prompt},
            {
                "role": "user",
                "content": "Please return only the specified JSON format.",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_completion_tokens=500,
    )
    data_judge = json.loads(response.choices[0].message.content)
    winner = data_judge.get("winner", "")
    gpt_analysis = data_judge.get("analysis", "")

    if "reasoning_A" in winner:
        final_winner = "Human" if not is_flipped_value else "AI"
    elif "reasoning_B" in winner:
        final_winner = "AI" if not is_flipped_value else "Human"
    elif "Tie" in winner:
        final_winner = "Tie"

    return final_winner, gpt_analysis


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
