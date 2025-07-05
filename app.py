from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv
import logging

app = Flask(__name__)
CORS(app)

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable not set.")

# Add your web search API key and endpoint to your .env file:
# SERPER_API_KEY=your_serper_api_key
# SERPER_API_URL=https://google.serper.dev/search
serper_api_key = os.getenv("SERPER_API_KEY")
serper_api_url = os.getenv("SERPER_API_URL", "https://google.serper.dev/search")

# Set up logging to 'chatbot.log'
logging.basicConfig(
    filename="chatbot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def fetch_web_results(query):
    logging.info(f"Fetching web results for query: {query}")
    if not serper_api_key:
        return "[Web search unavailable: SERPER_API_KEY not set.]"
    headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}
    payload = {"q": query}
    try:
        resp = requests.post(serper_api_url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        logging.info(f"Web search response: {data}")
        if "organic" in data:
            snippets = []
            for item in data["organic"][:5]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                snippets.append(f"- {title}: {snippet} ({link})")
            return "\n".join(snippets)
        return "[No web results found.]"
    except Exception as e:
        logging.error(f"Web search error: {e}")
        return f"[Web search error: {e}]"

@app.route('/chat', methods=['POST'])
def chat():
    logging.info("Received /chat request")
    data = request.json
    user_message = data.get('message', '')
    logging.info(f"User message: {user_message}")
    max_tokens = data.get('max_tokens', 1500)
    temperature = data.get('temperature', 0.7)

    # Always fetch web results and add to context (RAG)
    web_context = fetch_web_results(user_message)
    logging.info(f"Web context: {web_context}")
    system_prompt = (
        "You are an AI assistant. Always reply in English. "
        "You have access to the following web search results. Use this information to answer the user's question as accurately as possible.\n" + web_context
    )
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    logging.info(f"Payload to LLM: {payload}")
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            data=json.dumps(payload)
        )
        logging.info(f"LLM response status: {response.status_code}")
        result = response.json()
        logging.info(f"LLM response: {result}")
        choice = result.get('choices', [{}])[0]
        message = choice.get('message', {})
        reply = message.get('content')
        if not reply:
            reasoning = message.get('reasoning', '')
            reply = reasoning.strip() if reasoning else "Sorry, I don't have a direct answer."
        logging.info(f"Final reply: {reply}")
        return jsonify({"reply": reply, "raw": result})
    except Exception as e:
        logging.error(f"Error in LLM call: {e}")
        return jsonify({"reply": f"Error: {e}", "raw": {}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
