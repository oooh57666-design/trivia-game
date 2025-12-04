
import json
import uuid
import streamlit as st
import streamlit.components.v1 as components

# Store messages waiting to be sent to JavaScript
if "js_queue" not in st.session_state:
    st.session_state.js_queue = []

# This unique session ID lets JS know which user is which
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


def send_to_js(type, data):
    """Queue a message to send to the browser's JS side."""
    st.session_state.js_queue.append({"type": type, "data": data})


def firebase_component():
    """Inject JS into the page and create a communication bridge."""

    queue_json = json.dumps(st.session_state.js_queue)
    session_id = st.session_state.session_id

    st.session_state.js_queue = []

    components.html(
        f"""
        <div id="firebase-bridge"></div>

        <script type="module">
            // --- IMPORT FIREBASE LIBRARIES ---
            import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js";
            import {{ 
                getFirestore, doc, setDoc, getDoc, updateDoc, onSnapshot 
            }} from "https://www.gstatic.com/firebasejs/12.6.0/firebase-firestore.js";

            // --- FIREBASE CONFIG ---
            const firebaseConfig = {{
                apiKey: "AIzaSyAZtG1Bc0RjwN4juzgzd6WPSk1ixIg87x0",
                authDomain: "trivia-game-f3c34.firebaseapp.com",
                projectId: "trivia-game-f3c34",
                storageBucket: "trivia-game-f3c34.firebasestorage.app",
                messagingSenderId: "57817673958",
                appId: "1:57817673958:web:96d9e228967a8a9b250b27",
                measurementId: "G-DRPN3J0XSV"
            }};

            // Initialize Firebase
            const app = initializeApp(firebaseConfig);
            const db = getFirestore(app);

            // Load queued Python messages
            const messages = {queue_json};

            // Unique user ID from Python side
            const sessionID = "{session_id}";

            // Listen for messages from Python
            window.addEventListener("message", async (event) => {{
                const msg = event.data;
                if (!msg || msg.target !== "firebase-js") return;

                if (msg.type === "set") {{
                    await setDoc(doc(db, msg.collection, msg.doc), msg.data, {{ merge: true }});
                }}

                if (msg.type === "update") {{
                    await updateDoc(doc(db, msg.collection, msg.doc), msg.data);
                }}

                if (msg.type === "subscribe") {{
                    const unsub = onSnapshot(
                        doc(db, msg.collection, msg.doc),
                        (snapshot) => {{
                            const payload = {{
                                target: "streamlit",
                                type: "snapshot",
                                collection: msg.collection,
                                doc: msg.doc,
                                data: snapshot.data()
                            }};
                            window.parent.postMessage(payload, "*");
                        }}
                    );
                    window._sub = unsub;
                }}
            }});

            // Send queued messages to JS immediately
            for (const m of messages) {{
                window.postMessage(
                    {{
                        target: "firebase-js",
                        ...m.data
                    }},
                    "*"
                );
            }}
        </script>
        """,
        height=0,
    )
