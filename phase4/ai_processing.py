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

model_used = "gpt-5.4"


def get_openai_client():
    api_key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("API_KEY")
        or os.getenv("api_key")
    )
    if not api_key:
        raise RuntimeError(
            "Missing OpenAI API key. Set OPENAI_API_KEY in the app environment."
        )
    return OpenAI(api_key=api_key)


class C(BaseConstants):
    NAME_IN_URL = "phase4"
    NUM_ROUNDS = 5 if DEBUG else 15
    Pass_Reward_p2 = 40
    Pass_Reward_p3 = 40

    experimental_rules = """
        * Part II consists of 15 rounds. Before the first round begins, the computer will randomly pair participants into groups of two for this part of the experiment.
        * In each round, all participants must choose an integer between 11 and 20. If your chosen number is exactly one less than the number chosen by the other participant in your group (hereafter referred to as your "opponent"), you will be the "Number Winner" of that round.
        * Your base payoff for each round will be equal to the number you choose, in experimental currency units (ECUs). The Number Winner of that round will receive an additional 20 ECUs.
        """
    experimental_rules_2 = """
        * Part III consists of 15 rounds. Before the first round begins, the computer will randomly pair participants into groups of two for this part of the experiment.
        * In each round, all participants must choose an integer between 11 and 20. If your chosen number is exactly one less than the number chosen by the other participant in your group (hereafter referred to as your "opponent"), you will be the "Number Winner" of that round.
        * Your base payoff for each round will be equal to the number you choose, in experimental currency units (ECUs). The Number Winner of that round will receive an additional 20 ECUs. Moreover, if your chosen number is the same as the number chosen by your opponent, you will receive an additional 10 ECUs.
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

    client = get_openai_client()
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model_used,
                messages=[
                    {"role": "system", "content": generate_prompt},
                    {
                        "role": "user",
                        "content": f"""You are given the round number: {round_number} and the provided decision: {participant_decision}, write a reasoning (about 30-40 characters in Traditional Chinese, 50 characters at most) explaining the underlying thoughts and the information used for the decision. Your response must strictly follow the specified JSON format.
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
        You are a professional judge. Your task is to evaluate the explanations (decision-making reasons) participants provide for their decision-making process.

    ### Judging Task:
        Compare the reasons provided by the following two participants. Determine which participant more specifically explains the "underlying thoughts" behind their decision and the "information" they used to make it.

    ### Evaluation Criteria (Strictly Adhere to the Following):

    * **Information & Belief:** Does the participant mention specific information they observed? Do they describe inferences or assumptions about the current situation? Do they explain in detail how they formed these inferences or assumptions?

    * **Logic & Strategy:** Does the participant clearly show how they derived their final decision from the aforementioned information and beliefs?
        * **Is the logic consistent with the rules? (Crucial):** Does the causal relationship described in the reason align with the experimental rules? If the reason contradicts the rules (for example, claiming that a decision can produce an effect that is impossible under the rules), treat it as a "Logical Break." A reason with a Logical Break must be evaluated lower than a logically consistent reason.

    * **Level of Specificity:** Is the reason specific? For example, prefer "Because I observed A, I expected B, and therefore chose strategy C" over "I just picked one" or "I wanted to choose this." You can further assess:
        - Whether the reason contains specific information related to the rules rather than only vague descriptions.
        - Whether the statements have clear causal relationships and form a coherent line of reasoning.

    ### Strict Prohibitions (Do NOT Consider):

    * **Do NOT judge based on the "quality" or "probability of winning" of the decision:** Even if a participant's reasoning contains calculation errors or their decision has a very low probability of winning, their reason should still receive a higher evaluation if they clearly and logically explain their thought process.
        * **Note:** Your task is to evaluate "which participant more specifically explained the thoughts behind their decision and the information they used," NOT "which decision was smarter."

    * **Do NOT judge based on the length of the reason:** Do not treat a longer reason as more specific or detailed simply because it has more words. For example, "Because I observed A, I expected B, and therefore chose strategy C" and "After carefully observing, I noticed A, so I expected others to do B; consequently, I chose strategy C to increase my chance of winning" convey the same information and reasoning process, and should receive the same or very similar evaluations.

    * **Do NOT Favor Self-Invented Jargon:** Participants may use invented terms that sound professional (e.g., "Boundary Suppression Effect" or "Group Deviation Law"). Do not give a reason a higher evaluation merely because it contains non-standard terms that appear neither in the experimental instructions nor in everyday language.
        - Consider whether the participant clearly explains what the invented terms mean and whether they have concrete logical meaning in an everyday context.
        - If removing these terms makes the reason hollow or lacking in substance, give it a lower evaluation.

    ### Experimental instruction:
        Refer to the instructions for the relevant part of the experiment:
        {experimental_rules}

    ### Response Format:
        The following are two reasons written for the same decision. Compare them according to the evaluation criteria and prohibitions above.

            - reasoning_A: {reasons[0]}
            - reasoning_B: {reasons[1]}

        Determine which reason more specifically explains the "underlying thoughts" and "information used" behind the decision. If the two reasons are extremely close in specificity, you may declare a tie. Briefly explain your judgment in Traditional Chinese and follow the JSON format below exactly.

        {{
            "winner": "reasoning_A" or "reasoning_B" or "Tie",
            "analysis": "A brief reason for your judgement of the winner."
        }}
    """

    client = get_openai_client()
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


_thread_storage = {}


class AIProcessor:
    def gpt_process(self, participant_vars):
        p_id = participant_vars["id_in_subsession"]
        phase2_history = [dict(h) for h in participant_vars.get("phase2_history", [])]
        phase3_history = [dict(h) for h in participant_vars.get("phase3_history", [])]
        phase2_lookup = {h["round"]: h for h in phase2_history}
        phase3_lookup = {h["round"]: h for h in phase3_history}
        reasoning_rounds_p2 = participant_vars.get(
            "phase2_reasoning_rounds",
            [h["round"] for h in phase2_history if h.get("is_reasoning_round")],
        )
        reasoning_rounds_p3 = participant_vars.get(
            "phase3_reasoning_rounds",
            [h["round"] for h in phase3_history if h.get("is_reasoning_round")],
        )
        payoff_by_reasoning_by_round = {
            r: random.choice([True, False]) for r in reasoning_rounds_p2
        }
        payoff_by_reasoning_2_by_round = {
            r: random.choice([True, False]) for r in reasoning_rounds_p3
        }
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
                if r in reasoning_rounds_p2 and current and human_reason and human_num is not None:
                    target_is_flipped = random.choice([True, False])
                    gpt_reason = current.get("gpt_reason") or gpt_generate(C.experimental_rules, r, human_num)
                    winner, analysis = gpt_judge(C.experimental_rules, human_reason, gpt_reason, target_is_flipped)
                    original = cu(phase2_payoffs.get(r, 0))
                    payoff_by_reasoning = payoff_by_reasoning_by_round[r]
                    if payoff_by_reasoning:
                        final = cu(C.Pass_Reward_p2) if winner in ["Human", "Tie"] else cu(0)
                        payoff_basis = "理由判斷結果"
                    else:
                        final = original
                        payoff_basis = "數字選擇"
                    final_phase2[r] = final
                    current.update({
                        "human_reason": human_reason, "gpt_reason": gpt_reason,
                        "winner_type": winner,
                        "result_text": "您的理由較具體" if winner in ["Human", "Tie"] else "AI生成的理由較具體",
                        "payoff_basis": payoff_basis,
                        "payoff_by_reasoning": payoff_by_reasoning,
                        "final_payoff": final,
                    })
                    p2_db_data[r] = {
                        "is_flipped": target_is_flipped, "gpt_reason": gpt_reason,
                        "gpt_analysis": analysis, "winner_type": winner,
                        "payoff_by_reasoning": payoff_by_reasoning,
                        "payoff_adj": final - original,
                    }

                current = phase3_lookup.get(r)
                human_reason = str(participant_vars.get(f"reason_2_{r}") or "").strip()
                human_num = participant_vars.get(f"num_2_{r}")
                if r in reasoning_rounds_p3 and current and human_reason and human_num is not None:
                    target_is_flipped = random.choice([True, False])
                    gpt_reason = current.get("gpt_reason_2") or gpt_generate(C.experimental_rules_2, r, human_num)
                    winner, analysis = gpt_judge(C.experimental_rules_2, human_reason, gpt_reason, target_is_flipped)
                    original = cu(phase3_payoffs.get(r, 0))
                    payoff_by_reasoning_2 = payoff_by_reasoning_2_by_round[r]
                    if payoff_by_reasoning_2:
                        final = cu(C.Pass_Reward_p3) if winner in ["Human", "Tie"] else cu(0)
                        payoff_basis_2 = "理由判斷結果"
                    else:
                        final = original
                        payoff_basis_2 = "數字選擇"
                    final_phase3[r] = final
                    current.update({
                        "human_reason_2": human_reason, "gpt_reason_2": gpt_reason,
                        "winner_type_2": winner,
                        "result_text_2": "您的理由較具體" if winner in ["Human", "Tie"] else "AI生成的理由較具體",
                        "payoff_basis_2": payoff_basis_2,
                        "payoff_by_reasoning_2": payoff_by_reasoning_2,
                        "final_payoff_2": final,
                    })
                    p3_db_data[r] = {
                        "is_flipped_2": target_is_flipped, "gpt_reason_2": gpt_reason,
                        "gpt_analysis_2": analysis, "winner_type_2": winner,
                        "payoff_by_reasoning_2": payoff_by_reasoning_2,
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
