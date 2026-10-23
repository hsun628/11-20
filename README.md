# Team Reasoning with LLM Interaction

### Project Overview
This project contains the oTree implementation and OpenAI API integration for a team reasoning experiment.

***

### Module descriptions
#### phase1:
otree and html (pages) for the first stage of the experiment. 
- **data handling**: results are stored into `participant.vars` to be passed to subsequent phases.

#### phase2:
similar to phase1

#### phase_AI:
similar to phase1
  - **core functions**:
    - `gpt_generate`: use GPT API to generate a reasoning based on the participant's decision.
    - `gpt_judge`: an independent GPT API acts as a judge to compare the reasonings.
  
  - `prompt.md`: contains the full text of the system prompts and reasoning examples. (Note: The active prompts used by the server are mirrored in `phase_AI/__init__.py`).

#### phase4:
Combines AI reasoning generation and evaluation with the final prediction rounds. The instruction and processing pages run before the prediction pages, AI logic is in `phase4/ai_processing.py`, and results are saved to the phase4 player records.

#### Reasoning rounds
Part II and Part III each draw one reasoning round from every interval in `reasoning_rounds.REASONING_ROUND_RANGES`. Update that shared setting to adjust the intervals; selected rounds are saved separately per part and reused for AI processing and the final phase.

***

### setup instructions:
  1. create a `.env` file in the root directory and add your own `api_key`.
  2. adjust `num_participant` and `debug` mode in `settings.py`.