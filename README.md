# Team Reasoning with LLM Interaction

This repository contains an oTree web application for a multi-stage decision-making study, including participant decision pages, result tracking, and optional OpenAI-based reasoning analysis.

## Setup

1. Install the packages in `requirements.txt`.
2. Set `OPENAI_API_KEY` in the environment when using the AI analysis feature.
3. Configure `NUM_PARTICIPANT`, `OTREE_PRODUCTION`, `OTREE_ADMIN_PASSWORD`, and `OTREE_SECRET_KEY` for deployment as appropriate.
4. Start the project with `otree devserver` for local development.

The app can run without an OpenAI API key when AI analysis is not used.
