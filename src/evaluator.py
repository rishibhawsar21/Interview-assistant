# src/evaluator.py
import json
import re
import logging
from string import Template
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()
GEN_KEY = os.getenv("GEMINI_API_KEY")
if not GEN_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set in .env")
genai.configure(api_key=GEN_KEY)

from src.llm_client import run_prompt

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

EVAL_PROMPT = Template("""
You are an expert technical interview evaluator.
Question: $question
Candidate Answer: $answer
Role: $role
Level: $level

Evaluate the candidate's answer and return a JSON object ONLY with this schema:

{
  "scores": {
    "relevance_and_correctness": int,
    "structure_and_clarity": int,
    "depth_and_examples": int,
    "technical_accuracy": int,
    "communication_and_conciseness": int
  },
  "total_score_out_of_10": float,
  "justifications": {
    "relevance_and_correctness": "short justification",
    "structure_and_clarity": "short justification",
    "depth_and_examples": "short justification",
    "technical_accuracy": "short justification",
    "communication_and_conciseness": "short justification"
  },
  "improvement_tips": ["tip1", "tip2"],
  "model_answer": "concise model answer"
}

Return JSON only — no extra commentary. If you cannot follow the schema exactly, still output a JSON object (best-effort).
""")

def extract_first_json(text: str):
    if not text:
        return None
    start = text.find("{")
    if start == -1:
        m = re.search(r"(\{.*\})", text, re.S)
        if not m:
            return None
        text = m.group(1)
    else:
        text = text[start:]
    stack = 0
    for i, ch in enumerate(text):
        if ch == "{":
            stack += 1
        elif ch == "}":
            stack -= 1
            if stack == 0:
                return text[:i+1]
    return None

def repair_and_normalize(data: dict):
    """Try to ensure the minimal keys exist and normalize types."""
    # ensure scores numeric ints
    if "scores" in data and isinstance(data["scores"], dict):
        for k, v in list(data["scores"].items()):
            try:
                data["scores"][k] = int(float(v))
            except Exception:
                # if not convertible, drop or set 0
                try:
                    data["scores"][k] = int(v)
                except Exception:
                    data["scores"][k] = 0
    # compute total if missing
    if "total_score_out_of_10" not in data and "scores" in data and isinstance(data["scores"], dict):
        try:
            data["total_score_out_of_10"] = float(sum(data["scores"].values()))
        except Exception:
            pass
    # tolerate alternate single key "score"
    if "total_score_out_of_10" not in data and "score" in data:
        try:
            data["total_score_out_of_10"] = float(data["score"])
        except Exception:
            pass
    return data

def evaluate_answer(question: str, answer: str, role: str, level: str):
    prompt = EVAL_PROMPT.substitute(question=question, answer=answer, role=role, level=level)
    logger.debug("Prompt (trunc): %s", prompt[:1000])

    resp = run_prompt(prompt, max_output_tokens=700)
    if "error" in resp:
        return {"error": resp["error"]}

    text = resp.get("text", "")
    logger.debug("Raw model text (first 2000 chars): %s", text[:2000])

    jtxt = extract_first_json(text)
    if not jtxt:
        # return raw text for debugging
        return {"raw_text": text}

    try:
        data = json.loads(jtxt)
    except Exception as e:
        logger.exception("JSON parse failed")
        return {"raw_text": text, "parse_error": str(e)}

    data = repair_and_normalize(data)
    return data
