import os
import json
import requests
from typing import Dict, Any, List, Optional
from knowledge_base import kb
from context_manager import context_mgr
from database import get_messages

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_config.json")

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "provider": "local", # "local", "gemini", "openai", "groq"
        "api_key": os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or "",
        "model": "gemini-1.5-flash"
    }

def save_config(provider: str, api_key: str, model: str = ""):
    config = {
        "provider": provider,
        "api_key": api_key,
        "model": model or ("gemini-1.5-flash" if provider == "gemini" else "gpt-4o-mini")
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return config

CUSTOMER_SUPPORT_SYSTEM_PROMPT = """You are 'Nova', an intelligent, warm, and highly capable Customer Support AI for an enterprise e-commerce platform.
Your responsibilities:
1. Provide accurate, empathetic, and concise answers to customer queries.
2. Rely strictly on the provided FAQ Knowledge Base whenever relevant. Do not fabricate policies or return windows.
3. If an order tracking ID is provided, acknowledge it and summarize the order status clearly.
4. If you cannot answer the query with high confidence or the customer is frustrated, suggest escalating to a live human support specialist.
5. Respond in the customer's specified language naturally.

CRITICAL: Return your response strictly as valid JSON with the following schema:
{
  "intent": "<one of: greeting, goodbye, order_tracking, refund_return, billing_payment, shipping_delivery, account_access, product_inquiry, human_escalation, bot_info, general_inquiry>",
  "confidence": <float between 0.0 and 1.0>,
  "response": "<your conversational answer in markdown format>",
  "suggest_escalation": <true or false>
}
"""

class LLMClient:
    def __init__(self):
        pass

    def call_gemini(self, api_key: str, prompt: str, model: str = "gemini-1.5-flash") -> Optional[Dict[str, Any]]:
        """Call Gemini REST API directly."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json"
            }
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception as e:
            print(f"Gemini API error: {e}")
        return None

    def call_openai_compatible(self, api_key: str, base_url: str, model: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI or Groq compatible chat completions endpoint."""
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": CUSTOMER_SUPPORT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            print(f"OpenAI/Groq API error: {e}")
        return None

    def generate_response(self, session_id: str, user_text: str, current_lang: str = "en") -> Dict[str, Any]:
        """
        Orchestrates LLM query with Prompt Engineering, or falls back to local NLP engine.
        """
        config = load_config()
        provider = config.get("provider", "local")
        api_key = config.get("api_key", "").strip()

        # If provider is configured with an active key, attempt LLM generation
        if provider in ["gemini", "openai", "groq"] and api_key:
            # Build Context & Knowledge Base Prompt
            history = get_messages(session_id, limit=6)
            history_str = ""
            for msg in history:
                history_str += f"{msg['sender'].upper()}: {msg['content']}\n"

            # Retrieve top relevant FAQs for prompt grounding
            faq_matches = kb.search(user_text, top_k=3, threshold=0.25)
            faq_context = ""
            for idx, item in enumerate(faq_matches, 1):
                f = item["faq"]
                faq_context += f"{idx}. Q: {f['question']}\nA: {f['answer']}\n"

            session_context = context_mgr.get_context(session_id)
            
            prompt = f"""=== KNOWLEDGE BASE CONTEXT ===
{faq_context if faq_context else "No direct FAQ matched."}

=== CURRENT SESSION CONTEXT ===
Language: {current_lang}
Saved Order ID: {session_context.get('order_id', 'None')}
Customer Name: {session_context.get('customer_name', 'None')}

=== RECENT CONVERSATION HISTORY ===
{history_str}
USER: {user_text}

=== INSTRUCTIONS ===
Analyze the user's inquiry. Use the knowledge base where appropriate. Return valid JSON containing intent, confidence, response, and suggest_escalation.
"""
            llm_result = None
            if provider == "gemini":
                llm_result = self.call_gemini(api_key, f"{CUSTOMER_SUPPORT_SYSTEM_PROMPT}\n\n{prompt}", config.get("model", "gemini-1.5-flash"))
            elif provider == "openai":
                llm_result = self.call_openai_compatible(api_key, "https://api.openai.com/v1", config.get("model", "gpt-4o-mini"), prompt)
            elif provider == "groq":
                llm_result = self.call_openai_compatible(api_key, "https://api.groq.com/openai/v1", config.get("model", "llama-3.1-8b-instant"), prompt)

            if llm_result and "response" in llm_result:
                # Update context with any newly recognized details
                intent = llm_result.get("intent", "general_inquiry")
                confidence = float(llm_result.get("confidence", 0.90))
                session_context["last_intent"] = intent
                session_context["last_confidence"] = confidence
                context_mgr.save_context(session_id, session_context, current_lang)

                return {
                    "response": llm_result.get("response"),
                    "intent": intent,
                    "confidence": confidence,
                    "entities": session_context,
                    "language": current_lang,
                    "suggest_escalation": llm_result.get("suggest_escalation", confidence < 0.60),
                    "action": "llm_generated",
                    "provider": provider
                }

        # Fallback to local intelligent NLP Context Manager engine
        local_result = context_mgr.process_turn(session_id, user_text, current_lang)
        local_result["provider"] = "local_nlp"
        return local_result

llm_client = LLMClient()
