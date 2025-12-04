from firebase_bridge import firebase_component, send_to_js
firebase_component()
import streamlit as st

st.set_page_config(page_title="Intermission", layout="wide")
st.title("Intermission — Suggest & Vote")

if not st.session_state.players:
    st.info("No players joined yet. Go to Home and join.")
    st.stop()

player_name = st.session_state.player_name
if not player_name:
    st.info("Enter your name on the Home page and join to participate.")
    st.stop()

st.header("1) Suggest 5 categories (60s)")
with st.form("suggestions_form"):
    # prefill if they already suggested
    prev = st.session_state.suggestions.get(player_name, [""]*5)
    s1 = st.text_input("1", value=prev[0] if len(prev)>0 else "")
    s2 = st.text_input("2", value=prev[1] if len(prev)>1 else "")
    s3 = st.text_input("3", value=prev[2] if len(prev)>2 else "")
    s4 = st.text_input("4", value=prev[3] if len(prev)>3 else "")
    s5 = st.text_input("5", value=prev[4] if len(prev)>4 else "")
    submitted = st.form_submit_button("Submit suggestions")
    if submitted:
        st.session_state.suggestions[player_name] = [s.strip() for s in [s1,s2,s3,s4,s5] if s.strip()]
        st.success("Suggestions saved.")

st.markdown("---")
st.header("2) Voting on pooled categories")

# Build pooled categories (excluding duplicates and blanks)
pool = []
for author, sugests in st.session_state.suggestions.items():
    for cat in sugests:
        if cat and cat not in pool:
            pool.append(cat)

if not pool:
    st.info("No suggestions yet. Wait for other players, or host can start the next round.")
else:
    st.write("You must vote for exactly 5 categories. You cannot vote for categories you suggested.")
    # hide categories suggested by this player
    blocked = set(st.session_state.suggestions.get(player_name, []))
    voteable = [c for c in pool if c not in blocked]
    if not voteable:
        st.write("All pooled categories were suggested by you; you have no voteable categories. That's okay.")
    else:
        with st.form("votes_form"):
            votes = []
            # create checkboxes, enforce max=5 on submit
            cols = st.columns(2)
            for i,cat in enumerate(voteable):
                if cols[i%2].checkbox(cat, key=f"vote_{i}"):
                    votes.append(cat)
            vote_sub = st.form_submit_button("Submit votes (exactly 5 required)")
            if vote_sub:
                # count checkbox states via session form values - simpler: read selected keys
                selected = []
                for i,cat in enumerate(voteable):
                    if st.session_state.get(f"vote_{i}", False):
                        selected.append(cat)
                if len(selected) != 5:
                    st.error(f"You selected {len(selected)}. Please select exactly 5.")
                else:
                    st.session_state.votes[player_name] = selected
                    st.success("Votes recorded.")

st.markdown("---")
st.header("Results (top 10 will be used for Round 2 once voting completes)")

# Tally votes
from collections import Counter
all_votes = []
for v in st.session_state.votes.values():
    all_votes.extend(v)
counts = Counter(all_votes)
if counts:
    ranked = counts.most_common()
    st.write("Vote counts:")
    for cat, c in ranked:
        st.write(f"- {cat}: {c} votes")
    top10 = [c for c,_ in ranked][:10]
    st.write("Top 10 categories (tentative):")
    for i,cat in enumerate(top10):
        st.write(f"{i+1}. {cat}")
    # store as next round categories when all players voted
    if len(st.session_state.votes) == len(st.session_state.players):
        st.session_state.next_round_categories = top10
        st.success("All players have voted. Top 10 stored for Round 2.")
else:
    st.info("No votes yet.")

