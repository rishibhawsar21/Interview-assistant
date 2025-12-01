# src/prompts.py

EVAL_PROMPT_TEMPLATE = """
You are an expert interview evaluator.

Question: {question}
Candidate Answer: {answer}
Role: {role}
Level: {level}

Evaluate according to this rubric (each 0-2):
- relevance_and_correctness
- structure_and_clarity
- depth_and_examples
- technical_accuracy
- communication_and_conciseness

Provide output as JSON ONLY following this exact schema:
{
 "scores": {"relevance_and_correctness": int, "structure_and_clarity": int, "depth_and_examples": int, "technical_accuracy": int, "communication_and_conciseness": int},
 "total_score_out_of_10": float,
 "justifications": {"relevance_and_correctness": str, "structure_and_clarity": str, "depth_and_examples": str, "technical_accuracy": str, "communication_and_conciseness": str},
 "improvement_tips": [str],
 "model_answer": str
}

Be concise. Return valid JSON only.
"""
