# app.py

import os
import json
import random
import streamlit as st
from dotenv import load_dotenv
from src.llm_client import get_llm
from src.evaluator import evaluate_answer
from src.storage import Storage

load_dotenv()



st.set_page_config(page_title="AI Interview Coach", layout="wide")

# Simple question bank loader
QUESTIONS_DIR = os.path.join(os.path.dirname(__file__), "questions")

def load_questions(role):
    path = os.path.join(QUESTIONS_DIR, f"{role.lower().replace(' ', '_')}.json")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"Junior": [], "Intermediate": [], "Senior": []}

# Initialize storage
storage = Storage(db_path="sessions.json")

st.title("AI Interview Coach")

with st.sidebar:
    st.header("Session")
    user_name = st.text_input("Your name (optional)")
    role = st.selectbox("Role", ["Data Scientist", "ML Engineer", "AI Engineer"])
    level = st.selectbox("Level", ["Junior", "Intermediate", "Senior"])
    if st.button("New Question"):
        questions = load_questions(role)
        if questions.get(level):
            st.session_state.current_question = random.choice(questions[level])
        else:
            st.session_state.current_question = "No questions found for this role/level."

if "current_question" not in st.session_state:
    st.session_state.current_question = "Click 'New Question' to begin."

st.subheader("Question")
st.write(st.session_state.current_question)

answer = st.text_area("Your answer (type here)", height=200)

total = None
evaluation = None

if st.button("Submit Answer"):
    if not answer.strip():
        st.warning("Please type an answer before submitting.")
    else:
        with st.spinner("Evaluating..."):
            # call evaluator which uses LangChain/OpenAI
            evaluation = evaluate_answer(
                question=st.session_state.current_question,
                answer=answer,
                role=role,
                level=level
            )

    if evaluation is None:
        st.error("Evaluation failed. Check logs or API key.")
    else:
    # If evaluator returned an explicit error
        if "error" in evaluation:
            st.error("Evaluation error: " + str(evaluation["error"]))
        if "raw_text" in evaluation:
            st.code(evaluation["raw_text"][:4000])

    # If model returned raw_text (non-JSON), show it for debugging
        elif "raw_text" in evaluation:
            st.warning("Evaluator returned raw text (couldn't parse JSON). See output below:")
            st.code(evaluation["raw_text"][:4000])

        else:        # Safely extract total score
            total = evaluation.get("total_score_out_of_10")

        if total is None:
            # Try computing total from scores
            scores = evaluation.get("scores")
            if isinstance(scores, dict):
                try:
                    total = float(sum(int(float(v)) for v in scores.values()))
                except Exception:
                    total = None

        # Show total score
        if total is not None:
            st.success(f"Score: {total}/10")
        else:
            st.info("Score: Not available")

        # Show category scores
        if "scores" in evaluation:
            st.markdown("### Category Scores")
            st.json(evaluation["scores"])

        # Show justifications
        if "justifications" in evaluation:
            st.markdown("### Justifications")
            for k, v in evaluation["justifications"].items():
                st.write(f"**{k}**: {v}")

        # Show improvement tips
        if "improvement_tips" in evaluation:
            st.markdown("### Improvement Tips")
            for tip in evaluation["improvement_tips"]:
                st.write(f"- {tip}")

        # Show model answer
        if "model_answer" in evaluation:
            st.markdown("### Model Answer")
            st.write(evaluation["model_answer"])


# Session history viewer
st.sidebar.markdown("---")
st.sidebar.subheader("Recent Attempts")
for rec in reversed(storage.load_recent(limit=5)):
    st.sidebar.write(f"**{rec.get('role')} | {rec.get('level')}**")
    st.sidebar.write(rec.get('question'))
    st.sidebar.write(f"Score: {rec.get('evaluation', {}).get('total_score_out_of_10')}/10")
