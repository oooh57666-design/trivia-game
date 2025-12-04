import streamlit as st
import time

st.set_page_config(page_title="Player", layout="wide")
st.title("Player View")

# Join / identity
name = st.text_input("Your player name", value=st.session_state.player_name or "")
if st.button("Join / Update name"):
    st.session_state.player_name = name
    if name and name not in [p["name"] for p in st.session_state.players]:
        st.session_state.players.append({"name": name, "score": 0})
    st.success(f"Joined as {name}")

if not st.session_state.player_name:
    st.info("Please enter a name and join to participate.")
    st.stop()

st.write(f"Hello, {st.session_state.player_name} — Score: {next((p['score'] for p in st.session_state.players if p['name']==st.session_state.player_name),0)}")

st.markdown("---")
st.header("Memory Round (if active)")
mr = st.session_state.get("memory_round")
if mr and st.session_state.game_phase.startswith("memory"):
    phase = mr.get("phase","memorize")
    seq = mr.get("sequence",[])
    mem_time = st.session_state.settings.get("memorize_time",5)
    entry_time = st.session_state.settings.get("entry_time",8)
    if phase == "memorize":
        st.write("Memorize this sequence:")
        st.write(" ".join(seq))
        st.write(f"You will have {entry_time} seconds to enter them when the sequence hides.")
        if st.button("I finished memorizing (host may control actual timing)"):
            # switch to entry
            st.session_state.memory_round["phase"] = "entry"
            st.experimental_rerun()
    elif phase == "entry":
        st.write("Enter the sequence values one-by-one. Submit each entry (auto-detect style).")
        # display what user has entered so far
        if "my_mem_entries" not in st.session_state:
            st.session_state.my_mem_entries = []
        entered = st.session_state.my_mem_entries
        st.write("Entered:", " ".join(entered))
        next_val = st.text_input("Next unit", key="mem_input")
        if st.button("Submit unit"):
            if next_val:
                st.session_state.my_mem_entries.append(next_val.strip())
                st.experimental_rerun()
        if st.button("Finish memory entry (submit all)"):
            # store results per player (simple)
            if "memory_results" not in st.session_state:
                st.session_state.memory_results = {}
            st.session_state.memory_results[st.session_state.player_name] = st.session_state.my_mem_entries.copy()
            st.success("Memory entry saved.")
else:
    st.info("No active memory round.")

st.markdown("---")
st.header("Answering Questions")
cq = st.session_state.get("current_question")
if cq:
    st.subheader("Current question")
    st.write(cq.get("text"))
    # Answer box + submit bottom-right emulation
    if "local_answer" not in st.session_state:
        st.session_state.local_answer = ""
    answer = st.text_input("Your answer", value=st.session_state.local_answer, key="answer_input")
    st.session_state.local_answer = answer
    if st.button("Submit answer"):
        st.session_state.answers[st.session_state.player_name] = answer
        st.success("Answer submitted. Waiting for reveal.")
else:
    st.write("Waiting for the host to submit a question...")

st.markdown("---")
st.write("Revealed answers (updates when host reveals):")
for p, revealed in st.session_state.revealed.items():
    if revealed:
        st.write(f"- {p}: {st.session_state.answers.get(p,'')}")
    else:
        st.write(f"- {p}: ???")

