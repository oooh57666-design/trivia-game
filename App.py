import streamlit as st

st.set_page_config(page_title="Trivia Game", layout="wide")

# Initialize session state defaults (if not present)
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.players = []            # list of dicts: {"name": str, "score": int}
    st.session_state.host = None             # host name string
    st.session_state.player_name = ""        # local player's chosen name
    st.session_state.settings = {
        "memory_type": "Numbers",
        "memory_units": 10,
        "memorize_time": 5,
        "entry_time": 8,
        "main_time": 15,
        "side_time": 10,
        "question_values": [100,200,400,600,800,1000],
        "sub_penalty": 0,    # 0 means no penalty; negative for penalty amount
        "min_sub_save": 50,
        "side_correct_when_main_correct": True,
        "side_share_when_main_wrong": True,
    }
    st.session_state.categories = [f"Category {i+1}" for i in range(20)]
    st.session_state.suggestions = {}  # player_name -> list of suggestions during intermission
    st.session_state.votes = {}        # player_name -> list of voted categories
    st.session_state.current_question = None  # {"text":..., "answer":..., "value": ...}
    st.session_state.answers = {}     # player_name -> answer string
    st.session_state.revealed = {}    # player_name -> bool
    st.session_state.memory_round = {}  # temporary memory round data
    st.session_state.game_phase = "lobby"  # lobby, memory1, draft1, play1, intermission, memory2, draft2, play2, end

st.title("Trivia Game — Home")

st.write("Welcome! Use the left sidebar to navigate between pages:")
st.markdown("""
- **Settings** — configure the game (host only)  
- **Host** — host controls (start memory, ask questions, reveal answers)  
- **Player** — player UI to join, play memory, answer questions  
- **Intermission** — suggest categories & vote between rounds
""")

st.sidebar.header("Join / Identity")

# Choose role locally (not secure role enforcement; host is the user who sets host name)
name = st.sidebar.text_input("Your name", st.session_state.player_name)
st.session_state.player_name = name

col1, col2 = st.sidebar.columns(2)
if col1.button("Join as Player"):
    if name and name not in [p["name"] for p in st.session_state.players]:
        st.session_state.players.append({"name": name, "score": 0})
    st.success(f"Joined as player: {name}")

if col2.button("Set as Host"):
    if name:
        st.session_state.host = name
        if name not in [p["name"] for p in st.session_state.players]:
            st.session_state.players.append({"name": name, "score": 0})
        st.success(f"Host set to: {name}")

st.sidebar.write("Current host:", st.session_state.host)
st.sidebar.write("Players joined:")
for p in st.session_state.players:
    st.sidebar.write(f"- {p['name']} (score: {p.get('score',0)})")

st.sidebar.markdown("---")
st.sidebar.write("Game phase:")
st.sidebar.write(st.session_state.game_phase)

st.markdown("## Quick actions (for testing)")
col1, col2, col3 = st.columns(3)
if col1.button("Reset game state"):
    # careful: resets everything
    st.session_state.clear()
    st.experimental_rerun()

if col2.button("Simulate next phase"):
    # quick helper for testing phase transitions
    mapping = {
        "lobby": "memory1",
        "memory1": "draft1",
        "draft1": "play1",
        "play1": "intermission",
        "intermission": "memory2",
        "memory2": "draft2",
        "draft2": "play2",
        "play2": "end",
        "end": "lobby"
    }
    st.session_state.game_phase = mapping.get(st.session_state.game_phase, "lobby")
    st.success(f"Phase -> {st.session_state.game_phase}")

if col3.button("Clear suggestions & votes"):
    st.session_state.suggestions = {}
    st.session_state.votes = {}
    st.success("Cleared suggestions and votes")

