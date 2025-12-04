from firebase_bridge import firebase_component, send_to_js
firebase_component()
import streamlit as st
import time
from math import ceil

st.set_page_config(page_title="Host", layout="wide")
st.title("Host Console")

if st.session_state.host is None:
    st.warning("No host set. Set yourself as host on Home first.")
    st.stop()

if st.session_state.player_name != st.session_state.host:
    st.info("You are viewing the host console. Actions here affect the shared session_state. (Host only features shown.)")

# Helper: quick players list
players = [p["name"] for p in st.session_state.players]

st.header("Memory Round Controller")
col1, col2 = st.columns([2,1])
with col1:
    st.write("Start a memory round to determine order (or for practice).")
    mem_units = st.session_state.settings["memory_units"]
    mem_type = st.session_state.settings["memory_type"]

with col2:
    if st.button("Generate & Start Memory Round"):
        # Very simple generator for numbers only
        import random
        seq = []
        if mem_type == "Numbers":
            seq = [str(random.randint(0,9)) for _ in range(mem_units)]
        else:
            # fallback words/shapes samples
            pool = ["apple","cloud","star","triangle","circle","dog","cat","tree"]
            seq = [random.choice(pool) for _ in range(mem_units)]
        st.session_state.memory_round = {
            "sequence": seq,
            "start_time": time.time(),
            "phase": "memorize"
        }
        st.session_state.game_phase = "memory1"
        st.success("Memory round started. Switch to Player page to experience it as players.")

if st.session_state.memory_round:
    mr = st.session_state.memory_round
    st.write("Current memory round (host view):")
    st.write("Sequence:", " ".join(mr["sequence"]))
    st.write("Phase:", mr.get("phase"))

st.markdown("---")
st.header("Category Draft & Picks")
st.write("Current categories (host editable):")
cols = st.columns(3)
for i,cat in enumerate(st.session_state.categories):
    cols[i%3].write(f"{i+1}. {cat}")

st.markdown("---")
st.header("Question Entry & Reveal")

st.write("Enter a question and the (private) correct answer to enable suggested reveal order.")
q_text = st.text_input("Question", key="host_question_text")
q_answer = st.text_input("Correct Answer (host-only, used for suggested correctness)", key="host_question_answer")
q_value = st.selectbox("Question value", st.session_state.settings["question_values"], index=0)

if st.button("Submit question to players"):
    st.session_state.current_question = {
        "text": q_text,
        "answer": q_answer,
        "value": q_value,
        "main": None
    }
    # clear previous answers/reveals
    st.session_state.answers = {}
    st.session_state.revealed = {}
    st.session_state.game_phase = "play1"
    st.success("Question sent to players.")

st.write("Current question (players see it after submit):")
st.json(st.session_state.current_question)

st.markdown("### Suggested reveal order (host-only helper)")
if st.session_state.current_question:
    # compute suggested correctness by naive contains check (host finalizes)
    suggested = []
    for name, ans in st.session_state.answers.items():
        if not ans:
            continue
        host_ans = (st.session_state.current_question.get("answer") or "").lower()
        candidate = ans.lower()
        likely = host_ans in candidate or candidate in host_ans
        suggested.append((name, ans, likely))
    # sort: likely incorrect first
    suggested_sorted = sorted(suggested, key=lambda x: (x[2], x[0]))  # False (incorrect) first
    st.write("Suggested (incorrect→correct) — only visible to host:")
    for s in suggested_sorted:
        st.write(f"- {s[0]} — {s[1]} — likely match: {s[2]}")
else:
    st.info("No current question.")

st.markdown("---")
st.header("Reveal & Mark Answers (host controls)")
st.write("Click a player's name to reveal their answer to everyone, then mark Correct/Incorrect.")

for p in players:
    col1, col2 = st.columns([3,1])
    revealed = st.session_state.revealed.get(p, False)
    answer_preview = "???" if not revealed else st.session_state.answers.get(p, "")
    col1.write(f"**{p}**: {answer_preview}")
    # reveal button
    if col2.button(f"Reveal: {p}"):
        st.session_state.revealed[p] = True
        st.experimental_rerun()

# Mark correctness interface
st.markdown("#### Mark correctness")
for p in players:
    if st.session_state.revealed.get(p, False):
        row = st.columns([3,1,1])
        row[0].write(f"{p}: {st.session_state.answers.get(p,'')}")
        if row[1].button(f"Correct##{p}"):
            # store correctness - small local store
            key = f"correct_{p}"
            st.session_state[key] = True
            st.success(f"{p} marked correct.")
        if row[2].button(f"Wrong##{p}"):
            key = f"correct_{p}"
            st.session_state[key] = False
            st.error(f"{p} marked wrong.")

st.markdown("---")
st.write("Use the scoring engine (not yet implemented) to apply points after marking. For now, correctness flags are stored as `correct_<player>` in session_state.")

