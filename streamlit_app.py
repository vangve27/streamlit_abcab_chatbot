import streamlit as st
import requests
import os
from dotenv import load_dotenv
import logging
import subprocess
import time
import socket

load_dotenv()
API_URL = "http://localhost:5000/chat"

# Set up logging to 'streamlit_app.log'
logging.basicConfig(
    filename="streamlit_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

st.set_page_config(page_title="ABCAB Chatbot", layout="wide")
st.title("ABCAB Chatbot ")

if "messages" not in st.session_state:
    st.session_state.messages = []

def send_message(user_message):
    try:
        logging.info(f"User: {user_message}")
        res = requests.post(
            API_URL,
            json={"message": user_message}
        )
        res.raise_for_status()
        data = res.json()
        # Save the raw model response for UI display
        st.session_state["prompt_raw_response"] = data
        reply = data.get("reply", "No reply from backend.")
        logging.info(f"Bot: {reply}")
        return reply
    except Exception as e:
        logging.error(f"Error: {e}")
        st.session_state["prompt_raw_response"] = {"error": str(e)}
        return f"Error: {e}"

def is_backend_running(host="localhost", port=5000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        try:
            sock.connect((host, port))
            return True
        except Exception:
            return False

# Try to start backend if not running
if not is_backend_running():
    st.warning("Backend not running. Attempting to start Flask backend...")
    backend_proc = subprocess.Popen([
        "python", os.path.join(os.path.dirname(__file__), "app.py")
    ])
    # Wait for backend to start
    for _ in range(10):
        if is_backend_running():
            st.success("Flask backend started!")
            break
        time.sleep(1)
    else:
        st.error("Failed to start backend. Please check app.py manually.")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message:", key="input")
    submitted = st.form_submit_button("Send")
    if submitted and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("Thinking..."):
            reply = send_message(user_input)
        st.session_state.messages.append({"role": "bot", "content": reply})

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Abcab_bot:** {msg['content']}")

# Optional: Show raw model response
with st.expander("Show raw response"):
    import json
    raw = st.session_state.get("prompt_raw_response")
    if raw:
        st.text(json.dumps(raw, indent=2, ensure_ascii=False))
    else:
        st.info("No model response yet.")
