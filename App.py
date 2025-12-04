from firebase_bridge import firebase_component, send_to_js
firebase_component()
import streamlit as st

st.set_page_config(page_title="Trivia Game", layout="wide")

# Initialize session state defaults
if "initialized" not in st.session_state:
    st.session_state.initialized = True

    # Basic identity + players
    st.session_state.players = []  # list of dicts: {"id":str,"name":str,"score":int}
    st.session_state.host = None   # host name string
    st.session_state.local_name = ""  # local user name (this browser)

    # Game high-level
    st.session_state.game_id = "session_001"
    st.session_state.phase = "lobby"  # lobby, memory1, draft1, play1, intermission, memory2, draft2, play2, end

    # Settings (default)
    st.session_state.settings = {
        "memory_type": "Numbers",
        "memory_units": 10,
        "memorize_time": 5,
        "entry_time": 8,
        "main_time": 15,
        "side_time": 10,
        "question_values": [100,200,400,600,800,1000],
        "sub_penalty": 0,
        "min_sub_save": 50,
        "side_correct_when_main_correct": True,
        "side_share_when_main_wrong": True,
        "theme": "Blue"
    }

    # Categories
    st.session_state.categories = [f"Category {i+1}" for i in range(20)]
    st.session_state.next_round_categories = []  # populated after voting

    # Memory round data (shared)
    st.session_state.memory = {}

    # Draft picks
    st.session_state.draft_order = []  # player ids in order
    st.session_state.picks = {}  # player_id -> list of picked categories

    # Play round state
    st.session_state.current_question = None  # dict
    st.session_state.answers = {}  # player_id -> {"answer":str,"submitted":bool}
    st.session_state.revealed = {}  # player_id -> bool
    st.session_state.correctness = {}  # player_id -> True/False/None

    # Intermission: suggestions + votes
    st.session_state.suggestions = {}  # player_id -> [cat,cat,...]
    st.session_state.votes = {}  # player_id -> [cat,..]
    st.session_state.next_round_categories = []

    # Stats
    st.session_state.stats = {
        "most_correct": {},
        "most_saves": {}
    }

# Helper functions
def find_player_by_name(name):
    for p in st.session_state.players:
        if p["name"] == name:
            return p
    return None

# UI
st.title("Trivia Game — Home")
st.write("Welcome to your multiplayer trivia + memory game.")
st.markdown("---")

col1, col2 = st.columns([2,1])

with col1:
    st.header("Join or host")
    name = st.text_input("Your name", value=st.session_state.local_name)
    if st.button("Join as Player"):
        if not name:
            st.warning("Enter a name first.")
        else:
            st.session_state.local_name = name
            existing = find_player_by_name(name)
            if not existing:
                # create player id = name lower with suffix if needed
                pid = name
                count = 1
                while any(p["name"] == pid for p in st.session_state.players):
                    pid = f"{name}_{count}"
                    count += 1
                st.session_state.players.append({"id": pid, "name": name, "score": 0})
                st.success(f"Joined as {name}")
            else:
                st.info("You are already joined.")

    if st.button("Set me as Host"):
        if not name:
            st.warning("Enter a name first.")
        else:
            st.session_state.local_name = name
            if not find_player_by_name(name):
                st.session_state.players.append({"id": name, "name": name, "score": 0})
            st.session_state.host = name
            st.success(f"{name} is now the host.")

with col2:
    st.header("Quick controls (host)")
    if st.session_state.host == st.session_state.local_name:
        if st.button("Start Memory Round 1"):
            st.session_state.memory = {}
            st.session_state.phase = "memory1"
            st.experimental_rerun()
        if st.button("Go to Draft 1"):
            st.session_state.phase = "draft1"
            st.experimental_rerun()
        if st.button("Start Play 1"):
            st.session_state.phase = "play1"
            st.experimental_rerun()
        if st.button("Go to Intermission"):
            st.session_state.phase = "intermission"
            st.experimental_rerun()
    else:
        st.write("Host-only quick controls shown here when you are host.")

st.markdown("---")
st.header("Game summary")
st.write(f"Host: {st.session_state.host}")
st.write(f"Phase: {st.session_state.phase}")
st.write("Players:")
for p in st.session_state.players:
    st.write(f"- {p['name']} (score: {p['score']})")

st.markdown("---")
st.write("Use the sidebar to navigate to Settings, Host, Player, or Intermission pages.")
