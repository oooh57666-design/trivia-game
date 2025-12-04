from firebase_bridge import firebase_component, send_to_js
firebase_component()
import streamlit as st

st.set_page_config(page_title="Settings", layout="wide")

st.title("Settings — Host control panel")
if st.session_state.host is None:
    st.warning("No host set. Go to Home and set yourself as host to change settings.")
    st.stop()

# Simple permission check (UI only)
is_host = (st.session_state.player_name == st.session_state.host)
if not is_host:
    st.info("You are viewing settings. Only the host may make changes here.")

# Settings panel
st.header("General Settings")
cols = st.columns([2,1])
with cols[0]:
    name = st.text_input("Game Name", value="Trivia Game", key="ui_game_name")
    host_name = st.text_input("Host Name", value=st.session_state.host)
with cols[1]:
    theme = st.selectbox("Theme (host-only)", ["Blue","Purple","Silver","Gold","Midnight","Neon"], index=0)

st.markdown("---")
st.header("Memory Game Settings")
c1, c2, c3 = st.columns(3)
with c1:
    mem_type = st.selectbox("Memory Type", ["Numbers","Words","Shapes"], index=["Numbers","Words","Shapes"].index(st.session_state.settings["memory_type"]))
    mem_units = st.number_input("Units to memorize", min_value=3, max_value=20, value=st.session_state.settings["memory_units"], step=1)
with c2:
    mem_time = st.number_input("Memorize seconds", min_value=1, max_value=20, value=st.session_state.settings["memorize_time"], step=1)
    entry_time = st.number_input("Entry seconds", min_value=3, max_value=30, value=st.session_state.settings["entry_time"], step=1)
with c3:
    st.write("Note: Units are shown for memorize time, then hidden; players enter units one-by-one.")

st.markdown("---")
st.header("Question & Timing")
q1, q2 = st.columns(2)
with q1:
    main_time = st.number_input("Main player time (s)", min_value=5, max_value=120, value=st.session_state.settings["main_time"])
    side_time = st.number_input("Side players time (s)", min_value=3, max_value=120, value=st.session_state.settings["side_time"])
with q2:
    st.write("Question point values")
    # checkboxes for each question value
    vals = [100,200,400,600,800,1000]
    enabled_vals = []
    cols_vals = st.columns(3)
    for i,v in enumerate(vals):
        cb = cols_vals[i%3].checkbox(str(v), value=(v in st.session_state.settings["question_values"]))
        if cb: enabled_vals.append(v)

st.markdown("---")
st.header("Sub & Scoring Options")
sp_col1, sp_col2 = st.columns(2)
with sp_col1:
    sub_penalty = st.number_input("Sub penalty for wrong answer (0=no penalty, negative to subtract)", value=int(st.session_state.settings.get("sub_penalty",0)))
    min_sub_save = st.number_input("Minimum sub save points (min returned if 1/4 < min)", min_value=0, value=int(st.session_state.settings.get("min_sub_save",50)))
with sp_col2:
    side_when_main_correct = st.checkbox("Side players get +50 when main correct", value=st.session_state.settings.get("side_correct_when_main_correct", True))
    side_share_when_main_wrong = st.checkbox("Side players share half value when main wrong", value=st.session_state.settings.get("side_share_when_main_wrong", True))

st.markdown("---")
st.header("Categories (20)")
st.write("Edit the 20 host categories below. These are used in Round 1. During intermission players will suggest & vote for categories for Round 2.")
cat_cols = st.columns(2)
for i in range(20):
    key = f"cat_{i}"
    default = st.session_state.categories[i] if i < len(st.session_state.categories) else f"Category {i+1}"
    if i % 2 == 0:
        val = cat_cols[0].text_input(f"{i+1}.", value=default, key=key)
    else:
        val = cat_cols[1].text_input(f"{i+1}.", value=default, key=key)
    # update session categories immediately
    if len(st.session_state.categories) > i:
        st.session_state.categories[i] = val
    else:
        st.session_state.categories.append(val)

st.markdown("---")
if is_host:
    if st.button("Save Settings"):
        # persist settings
        st.session_state.settings.update({
            "memory_type": mem_type,
            "memory_units": mem_units,
            "memorize_time": mem_time,
            "entry_time": entry_time,
            "main_time": main_time,
            "side_time": side_time,
            "question_values": enabled_vals,
            "sub_penalty": sub_penalty,
            "min_sub_save": min_sub_save,
            "side_correct_when_main_correct": side_when_main_correct,
            "side_share_when_main_wrong": side_share_when_main_wrong,
        })
        st.success("Settings saved to session_state.")
else:
    st.info("Only the host can save changes here.")

st.markdown("---")
st.write("Session state preview (for debugging):")
st.json({
    "host": st.session_state.host,
    "players": [p["name"] for p in st.session_state.players],
    "settings": st.session_state.settings,
    "categories_count": len(st.session_state.categories)
})

