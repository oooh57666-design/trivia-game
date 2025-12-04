from firebase_bridge import firebase_component, send_to_js
firebase_component()
import streamlit as st
import random
import time
from math import floor

st.set_page_config(page_title="Host", layout="wide")
st.title("Host Console")

if not st.session_state.host:
    st.warning("No host set. Set yourself as host on Home to access host features.")
    st.stop()

is_host = (st.session_state.local_name == st.session_state.host)

# Show players and quick controls
st.header("Players")
cols = st.columns([2,1,1])
with cols[0]:
    for p in st.session_state.players:
        st.write(f"- {p['name']} (score: {p['score']})")

with cols[1]:
    if is_host and st.button("Reset scores"):
        for p in st.session_state.players:
            p['score'] = 0
        st.success("Scores reset.")

with cols[2]:
    if is_host and st.button("Clear answers/marks"):
        st.session_state.answers = {}
        st.session_state.revealed = {}
        st.session_state.correctness = {}
        st.success("Cleared answers/reveals.")

st.markdown("---")
st.header("Memory Round (host control)")

if is_host:
    if st.button("Generate memory sequence and start"):
        mem_type = st.session_state.settings["memory_type"]
        units = st.session_state.settings["memory_units"]
        seq = []
        if mem_type == "Numbers":
            seq = [str(random.randint(0,9)) for _ in range(units)]
        else:
            pool = ["apple","cloud","star","triangle","circle","dog","cat","tree","sun","moon","book","car"]
            seq = [random.choice(pool) for _ in range(units)]
        st.session_state.memory = {
            "sequence": seq,
            "phase": "memorize",
            "start_time": time.time()
        }
        st.session_state.phase = "memory1"
        st.success("Memory round started. Players should go to Player page.")
    if st.session_state.memory:
        st.write("Current sequence (host):")
        st.write(" ".join(st.session_state.memory.get("sequence", [])))
        st.write("Phase:", st.session_state.memory.get("phase"))

st.markdown("---")
st.header("Category Draft (host view)")
st.write("Draft order is determined by memory results. Use the 'Draft order' below or set manually.")

if "draft_order" not in st.session_state or not st.session_state.draft_order:
    # default draft order = players order
    st.session_state.draft_order = [p["id"] for p in st.session_state.players]

st.write("Draft order (player IDs):", st.session_state.draft_order)
st.write("Picks so far:")
for pid, picks in st.session_state.picks.items():
    st.write(f"- {pid}: {picks}")

if is_host and st.button("Reset picks"):
    st.session_state.picks = {}
    st.success("Picks cleared.")

st.markdown("---")
st.header("Question Entry & Suggested Reveal")

st.write("Enter question and correct answer (host only). The suggestion is only a helper; host marks final correctness.")

q_text = st.text_input("Question text", key="host_q_text")
q_ans = st.text_input("Correct answer (host-only)")
q_val = st.selectbox("Question value", st.session_state.settings["question_values"], index=0)

if is_host and st.button("Submit question to players"):
    # initialize current_question structure
    main_player = None
    # determine main player by rotation: we choose next by stored index
    if "main_index" not in st.session_state:
        st.session_state.main_index = 0
    if st.session_state.players:
        main_player = st.session_state.players[st.session_state.main_index % len(st.session_state.players)]["id"]
        st.session_state.main_index = (st.session_state.main_index + 1) % len(st.session_state.players)
    st.session_state.current_question = {
        "text": q_text,
        "correct_answer": q_ans,
        "value": q_val,
        "main": main_player,
        "sub": None,
        "timestamp": time.time(),
    }
    # clear answers storage
    st.session_state.answers = {p["id"]: {"answer": "", "submitted": False} for p in st.session_state.players}
    st.session_state.revealed = {p["id"]: False for p in st.session_state.players}
    st.session_state.correctness = {p["id"]: None for p in st.session_state.players}
    st.session_state.phase = "play1"
    st.success("Question submitted to players.")

st.markdown("Suggested reveal order (host-only helper):")
if st.session_state.current_question:
    suggested = []
    host_correct = (st.session_state.current_question.get("correct_answer") or "").lower()
    for pid, info in st.session_state.answers.items():
        ans = info.get("answer","") or ""
        if ans:
            ans_l = ans.lower()
            likely = (host_correct in ans_l) or (ans_l in host_correct)
            suggested.append((pid, ans, likely))
    # sort: likely incorrect first
    suggested_sorted = sorted(suggested, key=lambda x: (x[2], x[0]))
    for pid, ans, likely in suggested_sorted:
        st.write(f"- {pid}: {ans} — likely match: {likely}")

st.markdown("---")
st.header("Reveal & Mark (host)")

for p in st.session_state.players:
    pid = p["id"]
    col1, col2 = st.columns([3,1])
    revealed = st.session_state.revealed.get(pid, False)
    preview = "???" if not revealed else st.session_state.answers.get(pid, {}).get("answer","")
    col1.write(f"**{p['name']}**: {preview}")
    if is_host and col2.button(f"Reveal {pid}"):
        st.session_state.revealed[pid] = True
        st.rerun()

# Mark correctness (host)
st.markdown("Mark correctness (use these to compute score):")
for p in st.session_state.players:
    pid = p["id"]
    if st.session_state.revealed.get(pid, False):
        cols = st.columns([3,1,1])
        cols[0].write(f"{p['name']}: {st.session_state.answers.get(pid,{}).get('answer','')}")
        if is_host and cols[1].button(f"Correct##{pid}"):
            st.session_state.correctness[pid] = True
            st.success(f"{p['name']} marked correct.")
        if is_host and cols[2].button(f"Wrong##{pid}"):
            st.session_state.correctness[pid] = False
            st.error(f"{p['name']} marked wrong.")

st.markdown("---")
st.header("Apply scoring now")
if is_host and st.button("Compute & apply scoring for this question"):
    # scoring engine: implement rules described
    q = st.session_state.current_question
    if not q:
        st.error("No active question.")
    else:
        V = q["value"]
        main = q["main"]
        sub = q.get("sub")
        # convenience: build mapping from pid->correct bool
        correct = st.session_state.correctness.copy()
        # helper find player dict by id
        def get_player(pid):
            for p in st.session_state.players:
                if p["id"] == pid:
                    return p
            return None

        # apply scoring
        main_correct = bool(correct.get(main, False))
        sub_correct = bool(correct.get(sub, False)) if sub else False

        # reset incremental awarding dict
        awards = {p["id"]: 0 for p in st.session_state.players}

        if main_correct:
            # main gets full value
            awards[main] += V
            # side players who are correct get +50 each (including sub, but sub gets 100 if correct)
            for pid, val in correct.items():
                if pid == main: continue
                if val:
                    if pid == sub:
                        awards[pid] += 100
                    else:
                        awards[pid] += 50
        else:
            # main wrong
            # if sub correct -> main gets 1/2 V, sub gets 1/4 V (min_sub_save)
            if sub and correct.get(sub, False):
                awards[main] += V//2
                sub_amt = max(st.session_state.settings.get("min_sub_save",50), V//4)
                awards[sub] += sub_amt
                # remaining half V to share among side players who are correct (excluding sub and main? includes other side players)
                side_pool = V//2
                # count side players correct excluding sub and main
                side_correct_ids = [pid for pid,val in correct.items() if val and pid not in (main, sub)]
                if side_correct_ids:
                    per = round(side_pool / len(side_correct_ids))
                    for pid in side_correct_ids:
                        awards[pid] += per
            else:
                # sub not correct or no sub
                # side players who are correct share half V (including sub if they are correct? sub is included above)
                side_pool = V//2
                side_correct_ids = [pid for pid,val in correct.items() if val and pid != main]
                if side_correct_ids:
                    per = round(side_pool / len(side_correct_ids))
                    for pid in side_correct_ids:
                        awards[pid] += per
                # sub penalty if applicable
                if sub and not correct.get(sub, True):
                    penalty = st.session_state.settings.get("sub_penalty",0)
                    if penalty != 0:
                        # penalty value is negative or zero
                        awards[sub] += penalty

        # apply awards to players' scores
        for pid, amt in awards.items():
            pl = get_player(pid)
            if pl:
                pl["score"] = pl.get("score",0) + int(amt)

        st.success("Scoring applied. Awards:")
        for pid, amt in awards.items():
            if amt != 0:
                st.write(f"{pid}: {amt}")

        # cleanup: clear current question
        st.session_state.current_question = None
        st.session_state.answers = {}
        st.session_state.revealed = {}
        st.session_state.correctness = {}
        st.rerun()
