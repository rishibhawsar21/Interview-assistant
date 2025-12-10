# Interview Assistant

A Streamlit-based interactive app to practice technical interview questions with LLM-backed evaluation and feedback.

## Features
- Role-based question selection (AI Engineer, Data Scientist, ML Engineer)
- Answer evaluation using an LLM-based evaluator
- JSON-based question bank for easy editing
- Docker support for containerized runs
- Unit tests with pytest

## Tech stack
- Python 3.12
- Streamlit (UI)
- LLM integration (see `src/llm_client.py`)
- Docker
- pytest for testing

## Quick start (local)

1. Clone repo
```bash
git clone https://github.com/rishibhawsar21/Interview-assistant.git
cd Interview-assistant
