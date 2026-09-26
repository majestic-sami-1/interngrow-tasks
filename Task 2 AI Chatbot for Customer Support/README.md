# Nova AI - Enterprise Customer Support Chatbot (Week 2)

An intelligent, production-ready AI Customer Support Chatbot built with Python Flask, Natural Language Understanding (NLP), context-aware multi-turn dialog tracking, semantic FAQ knowledge base search, live confidence scoring, and upgrade features including Voice Input (STT), Text-to-Speech (TTS), and Multi-language support.

---

## 🌟 Features

### Core Customer Support Capabilities
1. **Natural Language Understanding (NLU)**:
   - Intent recognition across 10+ standard enterprise support domains: `greeting`, `order_tracking`, `refund_return`, `billing_payment`, `shipping_delivery`, `account_access`, `product_inquiry`, `human_escalation`, `bot_info`, and `goodbye`.
   - Domain entity & slot extractors for tracking numbers (`ORD-XXXXX`), email addresses, currency amounts, and customer names.
2. **Context-Aware Responses**:
   - Multi-turn dialog memory retaining customer context across turns.
   - Intelligent slot-filling dialog flows (e.g., prompting for an order ID when a tracking request is made, and automatically tracking it once provided).
3. **FAQ Knowledge Base**:
   - Curated repository of 20+ enterprise policies and Q&As spanning Orders, Shipping, Returns & Refunds, Billing, Account Security, and Hardware/Technical support.
   - Semantic TF-IDF and keyword-weighted search matching.
   - Interactive modal to browse, filter, search, and add custom FAQ articles.
4. **Conversation History**:
   - Persistent chat session storage in SQLite (`chatbot.db`).
   - Switch between multiple conversation sessions, create new chats, delete sessions, and export conversation transcripts (`.txt`).
5. **Intent Recognition & Live Confidence Scoring**:
   - Dynamic intent badge displaying recognized intent in real-time.
   - Animated visual confidence gauge with calibrated rating:
     - 🟢 **High Confidence (>= 80%)**: Direct pattern or FAQ match.
     - 🟡 **Moderate Confidence (60% - 79%)**: Generalized semantic match.
     - 🔴 **Low Confidence (< 60%)**: Triggers automated human escalation recommendation.
6. **Human Agent Escalation & Ticketing**:
   - Triggered either manually via button or automatically on low confidence / `human_escalation` queries.
   - Generates priority support tickets with reference IDs (e.g., `TCK-XXXXXX`) and persistent tracking.

### 🚀 Upgrade Features
1. **Voice Input (Speech-to-Text)**:
   - Microphone button integrated into the chat input bar.
   - Real-time transcription using the browser's native Web Speech API (`webkitSpeechRecognition`).
   - Animated audio wave visualizer bar during voice recording.
2. **Text-to-Speech (TTS)**:
   - "Read Aloud" speaker button on every bot message bubble.
   - Auto-read toggle in the top navigation bar.
   - Voice configuration in the Context Inspector (voice model selection, speech rate slider from 0.8x to 1.5x).
3. **Multi-language Support**:
   - Dynamic language switcher in the header supporting **English**, **Español (Spanish)**, **Français (French)**, **Deutsch (German)**, **اردو (Urdu)**, **हिंदी (Hindi)**, and **العربية (Arabic)**.
   - Automatically adapts bot conversational templates, Speech-to-Text recognition language, and TTS synthesis language!
4. **Dual AI Architecture**:
   - **Default Local NLP Mode**: Works 100% offline with zero external API dependencies.
   - **Enhanced LLM Mode**: Option in Settings modal to connect Google Gemini, OpenAI, or Groq API keys with custom prompt engineering.

---

## 🏗️ Architecture

```
Task 2AI Chatbot for Customer Support/
├── app.py                # Main Flask application and REST API endpoints
├── nlp_engine.py         # NLU, regex patterns, entity extraction, confidence scoring
├── context_manager.py    # Multi-turn conversation state, slots, and response formulation
├── knowledge_base.py     # FAQ knowledge base and semantic search algorithm
├── llm_client.py         # Prompt engineering & LLM provider connector (Gemini, OpenAI, Groq)
├── database.py           # SQLite persistence layer (sessions, messages, tickets, FAQs)
├── test_chatbot.py       # Automated unit and integration test suite
├── templates/
│   └── index.html        # Responsive single-page application template
├── static/
│   ├── css/
│   │   └── style.css     # Cybernetic glassmorphism styling and animations
│   └── js/
│       └── app.js        # Frontend client logic (Chat, STT, TTS, Inspector, Modals)
└── requirements.txt      # Project dependencies
```

---

## 🛠️ Installation & Setup

1. **Clone or Navigate to the project directory**:
   ```bash
   cd "Task 2AI Chatbot for Customer Support"
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Automated Test Suite**:
   ```bash
   python -m unittest test_chatbot.py -v
   ```

4. **Launch the Application**:
   ```bash
   python app.py
   ```

5. **Open in Browser**:
   Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in Chrome, Edge, Safari, or Firefox.

---

## 🧪 Testing Scenarios

Try these queries in the chat:
- **Order Tracking**:
  - *"Where is my order?"* -> Bot will prompt for Order ID.
  - *"ORD-10002"* -> Bot will provide live tracking status.
- **Returns & Policies**:
  - *"What is your return policy?"* -> Matched from FAQ Knowledge Base.
- **Multilingual Queries**:
  - Select *Español* and type: *"Hola, dónde está mi pedido?"*
  - Select *Français* and type: *"Bonjour, je veux parler à un conseiller"*
- **Human Escalation**:
  - *"I want to speak to a real human representative"* -> Automatically provides a ticket button.
- **Voice Features**:
  - Click the microphone icon to speak your query.
  - Click "Read Aloud" on any response to hear natural speech synthesis.
