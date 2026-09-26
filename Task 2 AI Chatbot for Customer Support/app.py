import os
import uuid
from flask import Flask, request, jsonify, render_template
from database import (
    init_db, create_session, get_session, list_sessions, delete_session,
    save_message, get_messages, create_ticket, list_tickets, add_custom_faq
)
from knowledge_base import kb
from llm_client import llm_client, load_config, save_config

app = Flask(__name__, template_folder="templates", static_folder="static")

# Ensure database is initialized on startup
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id")
    language = data.get("language", "en")

    if not message:
        return jsonify({"status": "error", "message": "Message cannot be empty."}), 400

    # Ensure valid session
    if not session_id or not get_session(session_id):
        session_id = str(uuid.uuid4())[:8]
        preview_title = message[:28] + "..." if len(message) > 28 else message
        create_session(session_id, title=preview_title, language=language)

    # Save user message
    save_message(session_id, sender="user", content=message, language=language)

    # Process through dual engine (LLM / NLP Context Engine)
    result = llm_client.generate_response(session_id, message, language)

    # Save bot message with intent and confidence
    save_message(
        session_id=session_id,
        sender="bot",
        content=result.get("response", ""),
        intent=result.get("intent", "general_inquiry"),
        confidence=result.get("confidence", 0.5),
        language=result.get("language", language),
        metadata={
            "suggest_escalation": result.get("suggest_escalation", False),
            "provider": result.get("provider", "local_nlp"),
            "action": result.get("action")
        }
    )

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "response": result.get("response"),
        "intent": result.get("intent"),
        "confidence": result.get("confidence"),
        "entities": result.get("entities", {}),
        "language": result.get("language", language),
        "suggest_escalation": result.get("suggest_escalation", False),
        "provider": result.get("provider", "local_nlp")
    })

@app.route("/api/sessions", methods=["GET"])
def get_all_sessions():
    sessions = list_sessions()
    return jsonify({"status": "success", "sessions": sessions})

@app.route("/api/sessions/new", methods=["POST"])
def create_new_session():
    data = request.get_json() or {}
    session_id = str(uuid.uuid4())[:8]
    lang = data.get("language", "en")
    title = data.get("title", "New Support Inquiry")
    create_session(session_id, title=title, language=lang)
    
    # Send initial greeting
    welcome_text = "Hello! Welcome to Customer Support. How can I help you today?"
    if lang == "es":
        welcome_text = "¡Hola! Bienvenido a Atención al Cliente. ¿Cómo puedo ayudarte hoy?"
    elif lang == "fr":
        welcome_text = "Bonjour ! Bienvenue au service client. Comment puis-je vous aider aujourd'hui ?"
    elif lang == "de":
        welcome_text = "Hallo! Willkommen beim Kundenservice. Wie kann ich Ihnen heute helfen?"
    elif lang == "ur":
        welcome_text = "السلام علیکم! کسٹمر سپورٹ میں خوش آمدید۔ آج میں آپ کی کیا مدد کر سکتا ہوں؟"
    elif lang == "hi":
        welcome_text = "नमस्ते! ग्राहक सेवा में आपका स्वागत है। आज मैं आपकी क्या सहायता कर सकता हूँ?"
    elif lang == "ar":
        welcome_text = "مرحباً بك في خدمة العملاء! كيف يمكنني مساعدتك اليوم؟"

    save_message(session_id, sender="bot", content=welcome_text, intent="greeting", confidence=0.99, language=lang)
    return jsonify({"status": "success", "session_id": session_id})

@app.route("/api/sessions/<session_id>/messages", methods=["GET"])
def get_session_messages(session_id):
    messages = get_messages(session_id)
    session = get_session(session_id)
    return jsonify({
        "status": "success",
        "session": session,
        "messages": messages
    })

@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def remove_session(session_id):
    delete_session(session_id)
    return jsonify({"status": "success", "message": "Session deleted."})

@app.route("/api/faqs", methods=["GET"])
def get_faqs():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    all_faqs = kb.get_all_faqs()

    if query:
        results = kb.search(query, top_k=10, threshold=0.1)
        faqs = [r["faq"] for r in results]
    else:
        faqs = all_faqs

    if category and category.lower() != "all":
        faqs = [f for f in faqs if f.get("category", "").lower() == category.lower()]

    categories = list(set(f.get("category", "General") for f in all_faqs))
    return jsonify({
        "status": "success",
        "faqs": faqs,
        "categories": ["All"] + sorted(categories)
    })

@app.route("/api/faqs", methods=["POST"])
def add_faq():
    data = request.get_json() or {}
    category = data.get("category", "General").strip()
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    keywords = data.get("keywords", "").strip()

    if not question or not answer:
        return jsonify({"status": "error", "message": "Question and Answer are required."}), 400

    faq_id = add_custom_faq(category, question, answer, keywords)
    return jsonify({"status": "success", "faq_id": faq_id, "message": "Custom FAQ added successfully."})

@app.route("/api/tickets", methods=["POST"])
def submit_ticket():
    data = request.get_json() or {}
    session_id = data.get("session_id", "")
    customer_name = data.get("customer_name", "Valued Customer").strip()
    email = data.get("email", "").strip()
    category = data.get("category", "General Support").strip()
    priority = data.get("priority", "Medium").strip()
    issue_summary = data.get("issue_summary", "").strip()

    if not issue_summary:
        return jsonify({"status": "error", "message": "Issue summary is required."}), 400

    ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
    create_ticket(ticket_id, session_id, customer_name, email, category, priority, issue_summary)

    return jsonify({
        "status": "success",
        "ticket_id": ticket_id,
        "message": f"Support ticket #{ticket_id} has been opened with {priority} priority. An agent will follow up shortly."
    })

@app.route("/api/tickets", methods=["GET"])
def fetch_tickets():
    tickets = list_tickets()
    return jsonify({"status": "success", "tickets": tickets})

@app.route("/api/settings", methods=["GET"])
def get_settings():
    cfg = load_config()
    key = cfg.get("api_key", "")
    masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else ("***" if key else "")
    return jsonify({
        "status": "success",
        "provider": cfg.get("provider", "local"),
        "model": cfg.get("model", ""),
        "has_api_key": bool(key),
        "masked_key": masked_key
    })

@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.get_json() or {}
    provider = data.get("provider", "local")
    api_key = data.get("api_key", "").strip()
    model = data.get("model", "")
    
    # If user didn't enter a new key, retain old one if unchanged
    if not api_key:
        old_cfg = load_config()
        if old_cfg.get("provider") == provider:
            api_key = old_cfg.get("api_key", "")

    saved = save_config(provider, api_key, model)
    return jsonify({"status": "success", "config": {
        "provider": saved["provider"],
        "model": saved["model"],
        "has_api_key": bool(saved["api_key"])
    }})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
