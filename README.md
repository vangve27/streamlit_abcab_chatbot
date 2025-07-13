# ABCAB Chatbot (Streamlit Edition)

A modern web-based chatbot using OpenRouter's DeepSeek model, with a Python Flask backend and a Streamlit frontend. Now with Retrieval-Augmented Generation (RAG) and full backend trace logging.

## Features
- Secure API key management via `.env` file
- Flask backend for model communication
- Retrieval-Augmented Generation (RAG) with Smart Fallback:
  - The backend analyzes the LLM's response for signs of outdated or insufficient knowledge (e.g., "real-time access", "current weather", "I recommend checking", and many more fallback phrases).
  - If the LLM cannot answer or indicates a knowledge cutoff, the UI prompts the user for approval to perform a web search.
  - Upon approval, the backend fetches relevant web results using the Serper API and augments the LLM context for up-to-date answers
- Streamlit chat UI with:
  - Clean, interactive chat interface
  - Markdown-style formatting for bot responses
  - Expander to show the full raw model response (including reasoning, tokens, etc.)
  - Logging of user and bot messages to `streamlit_app.log`
- Full backend trace logging to `chatbot.log` (request, web search, LLM payload, responses, errors)
- Handles DeepSeek's unique response format (uses `content` or `reasoning`)

## Prerequisites
- Python 3.8+
- An OpenRouter API key
- A Serper API key (for web search)

## Setup Instructions

### 1. Clone or Download the Project
Place all files (`app.py`, `streamlit_app.py`, etc.) in a folder, e.g. `main`.

### 2. Create the `.env` File
In the project folder, create a file named `.env` with this content:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
SERPER_API_KEY=your_serper_api_key_here
SERPER_API_URL=https://google.serper.dev/search
```
Replace the values with your actual API keys.

### 3. Install Python Dependencies
Open a terminal in the project folder and run:
```powershell
pip install flask flask-cors python-dotenv requests streamlit
```

### 4. Run the Streamlit Frontend (auto-starts backend)
In the project folder, run:
```powershell
streamlit run streamlit_app.py
```
This will launch the Streamlit chat UI in your browser (usually at [http://localhost:8501](http://localhost:8501)). The backend will be started automatically if not already running.

### 5. Use the Chatbot
- Type your message and interact with the bot.
- Click "Show raw response" to see the full backend JSON response for each message.

## How It Works
- The backend receives your message, performs a web search for up-to-date information, and augments the LLM context with the search results.
- The LLM uses both the web context and your question to generate an answer.
- All backend processing steps are logged in `chatbot.log` for traceability.
- The Streamlit frontend formats bot responses with markdown-like styling for readability.
- The raw model response (including reasoning, tokens, etc.) is available in the UI for each message.
- The backend first tries to answer using the LLM alone. If the answer is insufficient or indicates outdated knowledge (using an expanded set of fallback phrases), the UI will prompt you to approve a web search. If you approve, the backend fetches web results and re-asks the LLM with this new context for a more accurate answer.

## Troubleshooting
- **API Key not set:** Make sure your `.env` file is present and correct.
- **CORS or network errors:** Ensure the backend is running before starting the Streamlit app.
- **No response or errors:** Check `chatbot.log` and `streamlit_app.log` for details.
- **Verbose or meta responses:** This is a DeepSeek model quirk; the backend will show the full reasoning if no direct answer is given.

## Customization
- To use a different model, change the `model` field in `app.py`.
- To change the system prompt, edit the `system` message in the backend payload.
- To increase response length, raise the `max_tokens` value in `app.py`.

---
