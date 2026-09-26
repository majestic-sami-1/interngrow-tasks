import unittest
import json
import os
from database import init_db, get_connection, create_session, get_session, save_message, get_messages, create_ticket, list_tickets
from nlp_engine import nlp
from knowledge_base import kb
from context_manager import context_mgr
from app import app

class ChatbotSystemTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_nlp_intent_recognition(self):
        """Test NLP Intent Classifier across multiple query classes."""
        test_cases = [
            ("Hello there!", "greeting"),
            ("Where is my order?", "order_tracking"),
            ("I need to return this shirt and get a refund", "refund_return"),
            ("Why did my credit card payment decline?", "billing_payment"),
            ("What are your shipping rates and delivery times?", "shipping_delivery"),
            ("How do I reset my password?", "account_access"),
            ("I want to speak to a real human agent please", "human_escalation"),
            ("What can you do?", "bot_info")
        ]
        for query, expected_intent in test_cases:
            intent, conf, meta = nlp.classify_intent(query)
            self.assertEqual(intent, expected_intent, f"Query '{query}' expected '{expected_intent}', got '{intent}'")
            self.assertGreaterEqual(conf, 0.70, f"Confidence for '{query}' should be >= 0.70, got {conf}")

    def test_nlp_entity_extraction(self):
        """Test entity extraction for orders, emails, and amounts."""
        text = "Hello, my order ORD-84920 was $59.99, please contact test@example.com"
        entities = nlp.extract_entities(text)
        self.assertEqual(entities.get("order_id"), "ORD-84920")
        self.assertEqual(entities.get("email"), "test@example.com")
        self.assertEqual(entities.get("amount"), "59.99")

    def test_multilingual_recognition(self):
        """Test multilingual intent triggers."""
        spanish_query = "Hola, dónde está mi pedido?"
        intent, conf, meta = nlp.classify_intent(spanish_query)
        self.assertEqual(intent, "order_tracking")

        french_query = "Bonjour, je veux parler à un humain"
        intent, conf, meta = nlp.classify_intent(french_query)
        self.assertEqual(intent, "human_escalation")

        german_query = "Wo ist meine Bestellung?"
        intent, conf, meta = nlp.classify_intent(german_query)
        self.assertEqual(intent, "order_tracking")

        urdu_query = "میرا آرڈر کہاں ہے"
        intent, conf, meta = nlp.classify_intent(urdu_query)
        self.assertEqual(intent, "order_tracking")

    def test_faq_knowledge_base_search(self):
        """Test FAQ search and confidence scoring."""
        results = kb.search("How long do returns and refunds take?", top_k=2)
        self.assertTrue(len(results) > 0)
        top = results[0]
        self.assertEqual(top["faq"]["category"], "Returns & Refunds")
        self.assertGreaterEqual(top["score"], 0.4)

    def test_context_manager_multi_turn_slot_filling(self):
        """Test multi-turn dialog flow with slot-filling."""
        import uuid
        session_id = f"test_slot_{uuid.uuid4().hex[:6]}"
        create_session(session_id, title="Test Session")

        # Turn 1: User wants to track order without ID
        turn1 = context_mgr.process_turn(session_id, "I want to track my order")
        self.assertEqual(turn1["intent"], "order_tracking")
        self.assertIn("order", turn1["response"].lower())
        ctx = context_mgr.get_context(session_id)
        self.assertEqual(ctx.get("pending_slot"), "order_id")

        # Turn 2: User supplies order ID in next turn
        turn2 = context_mgr.process_turn(session_id, "It is ORD-10002")
        self.assertEqual(turn2["intent"], "order_tracking")
        self.assertIn("ORD-10002", turn2["response"])
        self.assertGreaterEqual(turn2["confidence"], 0.90)

    def test_flask_api_endpoints(self):
        """Test Flask REST API endpoints."""
        client = app.test_client()

        # 1. Root route
        res = client.get("/")
        self.assertEqual(res.status_code, 200)

        # 2. Chat endpoint
        res = client.post("/api/chat", json={
            "session_id": "test_api_session",
            "message": "What payment methods do you accept?",
            "language": "en"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("Visa", data["response"])
        self.assertGreaterEqual(data["confidence"], 0.70)

        # 3. FAQs endpoint
        res = client.get("/api/faqs")
        self.assertEqual(res.status_code, 200)
        faq_data = res.get_json()
        self.assertGreater(len(faq_data["faqs"]), 10)

        # 4. Tickets endpoint
        res = client.post("/api/tickets", json={
            "session_id": "test_api_session",
            "customer_name": "Jane Doe",
            "email": "jane@example.com",
            "category": "Billing",
            "priority": "High",
            "issue_summary": "Incorrect charge on monthly invoice"
        })
        self.assertEqual(res.status_code, 200)
        ticket_data = res.get_json()
        self.assertIn("ticket_id", ticket_data)
        self.assertTrue(ticket_data["ticket_id"].startswith("TCK-"))

if __name__ == "__main__":
    unittest.main()
