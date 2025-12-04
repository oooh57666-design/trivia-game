from firebase_bridge import firebase_component, send_to_js
firebase_component()
import streamlit as st
import time

st.set_page_config(page_title="Player", layout="wide")
st.title("Player View")

if not st.session_state.players:
    st.info("No players yet. Join on Home.")
    st.stop()

# Ensure local name
name = st.text_input("Your player name", value=st.session_state.local_name or "")
if st.button("Join / Update name"):
    if not name:
        st.warning("Enter a name")
    else:
        st.session_state.local_name = name
        if not any(p["name"] == name for p in st.session_state.players):
            st.session_state.players.append({"id": name, "name": name, "score": 0})
        st.success(f"Joined as {name}")
        st.rerun()

if not st.session_state.local_name:
    st.info("Set your local name first.")
    st.stop()

player_id = st.session_state.local_name

# Show personal score
player = next((p for p in st.session_state.players if p["name"] == player_id), None)
score = player["score"] if player else 0
st.write(f"Hello, {player_id} — Score: {score}")

st.markdown("---")
# Memory round participation
if st.session_state.phase.startswith("memory"):
    mr = st.session_state.memory
    if not mr:
        st.info("Memory round not started yet.")
    else:
        if mr.get("phase") == "memorize":
            st.subheader("Memorize Phase")
            seq = mr.get("sequence", [])
            st.write("Memorize this:")
            st.write(" ".join(seq))
            st.write(f"You have {st.session_state.settings['memorize_time']} seconds (host controls timing).")
            if st.button("I finished memorizing"):
                st.session_state.memory["phase"] = "entry"
                st.rerun()
        elif mr.get("phase") == "entry":
            st.subheader("Entry Phase")
            # create per-player entry store
            if "my_mem_entries" not in st.session_state:
                st.session_state.my_mem_entries = []
            st.write("Entered so far:", " ".join(st.session_state.my_mem_entries))
            next_unit = st.text_input("Next unit", key="mem_next")
            if st.button("Submit unit"):
                if next_unit:
                    st.session_state.my_mem_entries.append(next_unit.strip())
                    st.experimental_set_query_params()  # light refresh helper
                    st.rerun()
            if st.button("Finish memory entry"):
                st.session_state.suggestions[player_id] = st.session_state.my_mem_entries.copy()
                st.success("Memory entry stored (for demo).")
                st.rerun()
else:
    st.write("No active memory round.")

st.markdown("---")
# Answering current question
cq = st.session_state.current_question
if cq and not st.session_state.phase.startswith("memory"):
    st.subheader("Current question")
    st.write(cq.get("text"))
    # show main player's name at top
    main = cq.get("main")
    main_name = main
    st.write(f"Main player: {main_name}")
    # mandatory sub selection if you are main and haven't picked
    # sub selection UI: only shown to main player when question active
    if player_id == main:
        st.write("You are the main player for this question. Pick a sub:")
        options = [p["id"] for p in st.session_state.players if p["id"] != player_id]
        sub_choice = st.selectbox("Choose sub (mandatory)", options, key="sub_choice")
        if st.button("Confirm sub choice"):
            st.session_state.current_question["sub"] = sub_choice
            # reward chosen sub +50 immediately
            subp = next((pp for pp in st.session_state.players if pp["id"] == sub_choice), None)
            if subp:
                subp["score"] = subp.get("score",0) + 50
            st.success(f"Sub {sub_choice} chosen.")
            st.rerun()

    # Answer box minimal: text input + submit
    if "local_answer" not in st.session_state:
        st.session_state.local_answer = ""
    ans = st.text_input("Type your answer", value=st.session_state.local_answer, key="answer_input")
    st.session_state.local_answer = ans
    if st.button("Submit answer"):
        st.session_state.answers[player_id] = {"answer": ans, "submitted": True}
        st.success("Answer submitted.")
        st.rerun()
else:
    st.write("Waiting for host to post a question...")

st.markdown("---")
st.header("Reveal view")
st.write("Answers revealed by host will appear below.")
for p in st.session_state.players:
    pid = p["id"]
    if st.session_state.revealed.get(pid, False):
        st.write(f"- {p['name']}: {st.session_state.answers.get(pid,{}).get('answer','')}")
    else:
        st.write(f"- {p['name']}: ???")

st.markdown("---")
# Mini leaderboard popup when reveals are present
if any(st.session_state.revealed.values()):
    st.subheader("Leaderboard")
    sorted_players = sorted(st.session_state.players, key=lambda x: x["score"], reverse=True)
    for i,pl in enumerate(sorted_players, 1):
        st.write(f"{i}. {pl['name']} — {pl['score']}")
