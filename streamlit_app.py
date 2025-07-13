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
if "approval_pending" not in st.session_state:
    st.session_state.approval_pending = False
if "pending_user_message" not in st.session_state:
    st.session_state.pending_user_message = None

def send_message(user_message, allow_web_search=False):
    try:
        logging.info(f"User: {user_message}")
        payload = {"message": user_message}
        if allow_web_search:
            payload["allow_web_search"] = True
        res = requests.post(
            API_URL,
            json=payload
        )
        res.raise_for_status()
        data = res.json()
        # Save the raw model response for UI display
        st.session_state["prompt_raw_response"] = data
        # Only show the main reply (strip <think>...</think> if present)
        reply = data.get("reply", "No reply from backend.")
        if isinstance(reply, str):
            import re
            # Remove <think>...</think> blocks
            reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
        logging.info(f"Bot: {reply}")
        # Handle approval workflow
        if data.get("needs_approval"):
            st.session_state.approval_pending = True
            st.session_state.pending_user_message = user_message
        else:
            st.session_state.approval_pending = False
            st.session_state.pending_user_message = None
        return reply, data.get("needs_approval", False)
    except Exception as e:
        logging.error(f"Error: {e}")
        st.session_state["prompt_raw_response"] = {"error": str(e)}
        return f"Error: {e}", False

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

# Move chat transcript display above the chat form
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Abcab_bot:** {msg['content']}")

# Approval workflow UI
if st.session_state.approval_pending and st.session_state.pending_user_message:
    st.warning("The bot needs additional sources to provide accurate answer, would you like to search the web for the latest information?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, search the web", key="approve_web_search"):
            with st.spinner("Searching the web and generating answer..."):
                reply, _ = send_message(st.session_state.pending_user_message, allow_web_search=True)
            st.session_state.messages.append({"role": "bot", "content": reply})
            st.session_state.approval_pending = False
            st.session_state.pending_user_message = None
            st.rerun()
    with col2:
        if st.button("No, skip web search", key="deny_web_search"):
            st.session_state.messages.append({"role": "bot", "content": "Web search skipped by user."})
            st.session_state.approval_pending = False
            st.session_state.pending_user_message = None
            st.rerun()

# Place chat form at the bottom
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message:", key="input")
    submitted = st.form_submit_button("Send")
    if submitted and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state["pending_bot_input"] = user_input

# After the form, handle pending bot reply outside form context
pending_bot_input = st.session_state.pop("pending_bot_input", None)
if pending_bot_input:
    with st.spinner("Thinking..."):
        reply, needs_approval = send_message(pending_bot_input)
    st.session_state.messages.append({"role": "bot", "content": reply})
    st.rerun()

# Optional: Show raw model response
with st.expander("Show raw response"):
    import json
    raw = st.session_state.get("prompt_raw_response")
    if raw:
        st.text(json.dumps(raw, indent=2, ensure_ascii=False))
    else:
        st.info("No model response yet.")
