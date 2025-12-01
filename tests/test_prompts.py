# tests/test_prompts.py
from src.prompts import EVAL_PROMPT_TEMPLATE

def test_prompt_contains_json_schema():
    assert "Provide output as JSON ONLY" in EVAL_PROMPT_TEMPLATE
    assert '"scores"' in EVAL_PROMPT_TEMPLATE
