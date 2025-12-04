from firebase_bridge import firebase_component, send_to_js
firebase_component()
import streamlit as st
from collections import Counter

st.set_page_config(page_title="Intermission", layout="wide")
st.title("Intermission — Suggest & Vote")

if not st.session_state.players:
    st.info("No players joined yet.")
    st.stop()

player_id = st.session_state.local_name
if not player_id:
    st.info("Set your name on Home first.")
    st.stop()

st.header("Suggest up to 5 categories (you can overwrite your earlier suggestions)")
with st.form("suggest"):
    prev = st.session_state.suggestions.get(player_id, [""]*5)
    s1 = st.text_input("1", value=prev[0] if len(prev)>0 else "")
    s2 = st.text_input("2", value=prev[1] if len(prev)>1 else "")
    s3 = st.text_input("3", value=prev[2] if len(prev)>2 else "")
    s4 = st.text_input("4", value=prev[3] if len(prev)>3 else "")
    s5 = st.text_input("5", value=prev[4] if len(prev)>4 else "")
    subm = st.form_submit_button("Submit suggestions")
    if subm:
        cleaned = [s.strip() for s in [s1,s2,s3,s4,s5] if s.strip()]
        st.session_state.suggestions[player_id] = cleaned
        st.success("Suggestions saved.")

st.markdown("---")
st.header("Voting on pooled categories")
# pool = all suggestions unique
pool = []
for auth, lst in st.session_state.suggestions.items():
    for c in lst:
        if c and c not in pool:
            pool.append(c)

st.write(f"{len(pool)} pooled categories available for voting.")
if not pool:
    st.info("No suggestions yet. Wait for players to submit.")
else:
    st.write("You must pick exactly 5 categories to vote for. You cannot vote for categories you personally suggested.")
    blocked = set(st.session_state.suggestions.get(player_id, []))
    voteable = [c for c in pool if c not in blocked]
    if not voteable:
        st.info("No voteable categories (all categories were your suggestions).")
    else:
        with st.form("voting"):
            selected = []
            cols = st.columns(2)
            for i,cat in enumerate(voteable):
                if cols[i%2].checkbox(cat, key=f"vote_{i}"):
                    selected.append(cat)
            vs = st.form_submit_button("Submit votes")
            if vs:
                # collect selected via state
                chosen = []
                for i,cat in enumerate(voteable):
                    if st.session_state.get(f"vote_{i}", False):
                        chosen.append(cat)
                if len(chosen) != 5:
                    st.error(f"You selected {len(chosen)}. Please select exactly 5.")
                else:
                    st.session_state.votes[player_id] = chosen
                    st.success("Votes recorded.")

st.markdown("---")
st.header("Vote tally (admin view)")
all_votes = []
for v in st.session_state.votes.values():
    all_votes.extend(v)
counts = Counter(all_votes)
if counts:
    ranked = counts.most_common()
    for i,(cat,cnt) in enumerate(ranked,1):
        st.write(f"{i}. {cat} — {cnt} votes")
    top10 = [c for c,_ in ranked][:10]
    st.write("Top 10 (tentative):")
    for i,cat in enumerate(top10,1):
        st.write(f"{i}. {cat}")
    # if all players voted, lock in next_round_categories
    if len(st.session_state.votes) == len(st.session_state.players):
        st.session_state.next_round_categories = top10
        st.success("All votes in. Top 10 stored for next round.")
else:
    st.info("No votes yet.")
