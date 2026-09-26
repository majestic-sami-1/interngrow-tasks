import re
from typing import Dict, Any, List, Tuple, Optional

# Intent definitions with keyword patterns, phrases, and multilingual triggers
INTENT_PATTERNS = {
    "greeting": {
        "patterns": [
            r"\b(hello|hi|hey|greetings|good\s+(morning|afternoon|evening|day)|howdy|sup)\b",
            r"\b(hola|buenos\s+dias|buenas\s+tardes)\b", # Spanish
            r"\b(bonjour|salut|coucou)\b", # French
            r"\b(hallo|guten\s+(tag|morgen|abend))\b", # German
            r"\b(salam|assalam|marhaba|namaste|aadaab)\b", # Multilingual
            r"(ہیلو|سلام|السلام\s+علیکم|آداب)", # Urdu
            r"(नमस्ते|नमस्कार|प्रणाम)", # Hindi
            r"(مرحبا|أهلا|السلام\s+عليكم)" # Arabic
        ],
        "keywords": ["hello", "hi", "hey", "greeting", "morning", "afternoon", "evening", "welcome"],
        "base_confidence": 0.95
    },
    "goodbye": {
        "patterns": [
            r"\b(bye|goodbye|see\s+you|farewell|have\s+a\s+nice\s+day|cya|take\s+care)\b",
            r"\b(adios|chao|hasta\s+luego)\b", # Spanish
            r"\b(au\s+revoir|a\s+bientot|adieu)\b", # French
            r"\b(tschuss|auf\s+wiedersehen)\b", # German
            r"(خدا\s+حافظ|الوداع)", # Urdu
            r"(अलविदा|फिर\s+मिलेंगे)", # Hindi
            r"(مع\s+السلامة|وداعا)" # Arabic
        ],
        "keywords": ["bye", "goodbye", "farewell", "cya", "night"],
        "base_confidence": 0.92
    },
    "human_escalation": {
        "patterns": [
            r"\b(human|agent|representative|real\s+person|live\s+agent|speak\s+to\s+(someone|human|person|agent)|talk\s+to\s+(someone|human|person|agent)|escalate|operator|customer\s+service\s+rep)\b",
            r"\b(hablar\s+con\s+(?:un\s+)?(agente|humano|representante)|atenci[oó]n\s+al\s+cliente)\b", # Spanish
            r"\b(parler\s+(?:[aà]\s+|avec\s+)?(?:un\s+)?(humain|conseiller|agent)|service\s+client)\b", # French
            r"\b(mit\s+einem\s+(?:menschen|mitarbeiter)\s+sprechen|kundenservice)\b", # German
            r"(انسان\s+سے\s+بات|ایجنٹ\s+سے\s+بات|نمائندے\s+سے\s+بات)", # Urdu
            r"(एजेंट\s+से\s+बात|इंसान\s+से\s+बात|अधिकारी\s+से\s+बात)", # Hindi
            r"(التحدث\s+مع\s+موظف|خدمة\s+العملاء|ممثل\s+الدعم)" # Arabic
        ],
        "keywords": ["agent", "human", "representative", "operator", "person", "escalate", "advisor", "rep", "humain", "conseiller", "agente", "mitarbeiter"],
        "base_confidence": 0.94
    },
    "order_tracking": {
        "patterns": [
            r"\b(track|tracking|where\s+is\s+my\s+order|order\s+status|check\s+order|locate\s+order|delivery\s+status|package\s+status|ord[-\s]?\d+)\b",
            r"\b(d[oó]nde\s+est[aá]\s+mi\s+pedido|rastrear\s+pedido|estado\s+del\s+pedido)\b", # Spanish
            r"\b(o[uù]\s+est\s+ma\s+commande|suivi\s+de\s+commande|suivre\s+colis)\b", # French
            r"\b(wo\s+ist\s+meine\s+bestellung|sendungsverfolgung|bestellstatus)\b", # German
            r"(میرا\s+آرڈر\s+کہاں\s+ہے|آرڈر\s+ٹریک|پارسل\s+کہاں\s+ہے)", # Urdu
            r"(मेरा\s+आर्डर\s+कहाँ\s+है|ट्रैक\s+ऑर्डर|डिलीवरी\s+स्टेटस)", # Hindi
            r"(أين\s+طلبي|تتبع\s+الطلب|حالة\s+الشحنة)" # Arabic
        ],
        "keywords": ["track", "order", "status", "package", "parcel", "shipment", "locate", "arrived", "delivery"],
        "base_confidence": 0.91
    },
    "refund_return": {
        "patterns": [
            r"\b(refund|return|send\s+back|money\s+back|exchange|return\s+policy|reimburse|cancel\s+and\s+refund)\b",
            r"\b(reembolso|devoluci[oó]n|devolver|cambiar\s+talla)\b", # Spanish
            r"\b(remboursement|retourner|renvoyer|[eé]change)\b", # French
            r"\b(r[uü]ckerstattung|zur[uü]ckschicken|umtausch|geld\s+zur[uü]ck)\b", # German
            r"(واپسی|پیسے\s+واپس|ریفنڈ|تبادلہ)", # Urdu
            r"(रिफंड|वापसी|पैसे\s+वापस|बदलना)", # Hindi
            r"(استرجاع\s+المبلغ|إرجاع\s+المنتج|استبدال)" # Arabic
        ],
        "keywords": ["refund", "return", "exchange", "money back", "reimburse", "send back", "swap"],
        "base_confidence": 0.90
    },
    "billing_payment": {
        "patterns": [
            r"\b(billing|payment|invoice|receipt|charged|double\s+charge|credit\s+card|paypal|klarna|declined|pay\s+failed|vat)\b",
            r"\b(pago|factura|cobro|tarjeta|recibo)\b", # Spanish
            r"\b(paiement|facture|carte\s+bancaire|prelevement)\b", # French
            r"\b(zahlung|rechnung|kreditkarte|abgebucht)\b", # German
            r"(بلنگ|ادائیگی|انوائس|رسید|پیمنٹ)", # Urdu
            r"(भुगतान|बिलिंग|रसीद|चालान)", # Hindi
            r"(الدفع|الفاتورة|بطاقة\s+ائتمان|خصم)" # Arabic
        ],
        "keywords": ["payment", "billing", "invoice", "receipt", "charge", "charged", "credit card", "declined", "vat"],
        "base_confidence": 0.89
    },
    "shipping_delivery": {
        "patterns": [
            r"\b(shipping\s+rates?|shipping\s+costs?|delivery\s+times?|how\s+long\s+to\s+ship|international\s+shipping|express\s+shipping|carrier|dhl|fedex|customs)\b",
            r"\b(envio|gastos\s+de\s+envio|tiempo\s+de\s+entrega|envio\s+internacional)\b", # Spanish
            r"\b(livraison|frais\s+de\s+port|delai\s+de\s+livraison|international)\b", # French
            r"\b(versand|lieferzeit|versandkosten|internationale\s+lieferung)\b", # German
            r"(شپنگ|ڈیلیوری|کتنے\s+دن\s+لگیں|بین\s+الاقوامی)", # Urdu
            r"(शिपिंग|डिलीवरी\s+का\s+समय|लागत|अंतर्राष्ट्रीय)", # Hindi
            r"(الشحن|تكلفة\s+الشحن|مدة\s+التوصيل|شحن\s+دولي)" # Arabic
        ],
        "keywords": ["shipping", "delivery", "rate", "cost", "carrier", "international", "days", "dispatch", "express"],
        "base_confidence": 0.88
    },
    "account_access": {
        "patterns": [
            r"\b(password|reset\s+password|login|log\s+in|sign\s+in|locked\s+out|update\s+profile|change\s+address|email\s+address|delete\s+account)\b",
            r"\b(contrasena|olvide\s+mi\s+contrasena|iniciar\s+sesion|cambiar\s+direccion)\b", # Spanish
            r"\b(mot\s+de\s+passe|connexion|changer\s+adresse|compte)\b", # French
            r"\b(passwort|anmelden|adresse\s+andern|konto)\b", # German
            r"(پاسورڈ|لاگ\s+ان|اکاؤنٹ|پتہ\s+تبدیل)", # Urdu
            r"(पासवर्ड|लॉगिन|खाता|पता\s+बदलें)", # Hindi
            r"(كلمة\s+المرور|تسجيل\s+الدخول|تغيير\s+العنوان|حسابي)" # Arabic
        ],
        "keywords": ["password", "login", "account", "profile", "locked", "signin", "address", "email"],
        "base_confidence": 0.89
    },
    "product_inquiry": {
        "patterns": [
            r"\b(warranty|guarantee|broken|defective|malfunction|not\s+working|troubleshoot|specs|specification|stock|manual)\b",
            r"\b(garantia|defectuoso|no\s+funciona|averiado)\b", # Spanish
            r"\b(garantie|defectueux|ne\s+fonctionne\s+pas|en\s+panne)\b", # French
            r"\b(garantie|defekt|funktioniert\s+nicht|reparatur)\b", # German
            r"(وارنٹی|خراب|کام\s+نہیں\s+کر\s+رہا)", # Urdu
            r"(वारंटी|खराब|काम\s+नहीं\s+कर\s+रहा)", # Hindi
            r"(الضمان|معطل|لا\s+يعمل|مواصفات)" # Arabic
        ],
        "keywords": ["warranty", "guarantee", "broken", "defective", "troubleshoot", "repair", "specs", "stock"],
        "base_confidence": 0.87
    },
    "bot_info": {
        "patterns": [
            r"\b(who\s+are\s+you|what\s+are\s+you|what\s+can\s+you\s+do|are\s+you\s+a\s+bot|are\s+you\s+ai|help\s+me\s+with|your\s+name)\b",
            r"\b(quien\s+eres|que\s+puedes\s+hacer|eres\s+un\s+robot)\b", # Spanish
            r"\b(qui\s+es\s+tu|que\s+peux\s+tu\s+faire|es\s+tu\s+une\s+ia)\b", # French
            r"\b(wer\s+bist\s+du|was\s+kannst\s+du|bist\s+du\s+eine\s+ki)\b", # German
            r"(تم\s+کون\s+ہو|کیا\s+کر\s+سکتے\s+ہو|کیا\s+تم\s+بوٹ\s+ہو)", # Urdu
            r"(तुम\s+कौन\s+हो|आप\s+क्या\s+कर\s+सकते\s+हैं|क्या\s+तुम\s+एआई\s+हो)", # Hindi
            r"(من\s+أنت|ماذا\s+يمكنك\s+أن\s+تفعل|هل\s+أنت\s+روبوت)" # Arabic
        ],
        "keywords": ["bot", "ai", "who", "features", "capabilities", "virtual assistant", "support agent"],
        "base_confidence": 0.95
    }
}

class NLPEngine:
    """NLU, Entity Extractor, Intent Recognizer and Confidence Scoring Engine."""

    def __init__(self):
        pass

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract structured domain entities from user message."""
        entities = {}
        
        # 1. Order ID (e.g., ORD-12345, ORD9821, #98124, Order 54321)
        order_match = re.search(r'\b(?:ord[-\s]?\d{4,8}|#\d{4,8}|order\s+#?\s*(\d{4,8}))\b', text, re.IGNORECASE)
        if order_match:
            val = order_match.group(0).upper().replace(" ", "").replace("#", "ORD-")
            if not val.startswith("ORD-") and not val.startswith("ORD"):
                val = f"ORD-{val}"
            entities["order_id"] = val

        # 2. Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', text)
        if email_match:
            entities["email"] = email_match.group(0).lower()

        # 3. Currency / Monetary Amounts
        money_match = re.search(r'(?:\$|€|£|\bUSD\b|\bEUR\b|\bPKR\b|\bINR\b)\s*(\d+(?:\.\d{2})?)|\b(\d+(?:\.\d{2})?)\s*(?:dollars?|euros?|pounds?|rupees?)', text, re.IGNORECASE)
        if money_match:
            val = money_match.group(1) or money_match.group(2)
            entities["amount"] = val

        # 4. Customer Name extraction pattern
        name_match = re.search(r'\b(?:my\s+name\s+is|i\s+am|i\'m|call\s+me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', text, re.IGNORECASE)
        if name_match:
            entities["customer_name"] = name_match.group(1).strip().title()

        return entities

    def detect_language(self, text: str) -> str:
        """Heuristic language detection based on character ranges and key language markers."""
        # Urdu / Arabic script detection
        if re.search(r'[\u0600-\u06FF]', text):
            # Differentiate Urdu vs Arabic markers
            if re.search(r'[ٹڈڑںےہئے]', text) or any(w in text for w in ['ہے', 'ہوں', 'کیا', 'کیسے', 'آرڈر', 'سلام']):
                return 'ur'
            return 'ar'

        # Devanagari (Hindi)
        if re.search(r'[\u0900-\u097F]', text):
            return 'hi'

        text_lower = text.lower()
        
        # Spanish detection markers
        es_markers = ['hola', 'gracias', 'por favor', 'pedido', 'reembolso', 'dónde', 'dias', 'tardes', 'cuenta', 'ayuda', 'cuál']
        if any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in es_markers):
            return 'es'

        # French detection markers
        fr_markers = ['bonjour', 'merci', 's\'il vous plaît', 'commande', 'remboursement', 'où', 'livraison', 'facture', 'aide']
        if any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in fr_markers):
            return 'fr'

        # German detection markers
        de_markers = ['hallo', 'danke', 'bitte', 'bestellung', 'rückerstattung', 'rechnung', 'versand', 'hilfe', 'kunde']
        if any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in de_markers):
            return 'de'

        return 'en'

    def classify_intent(self, text: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Classify customer query intent and calculate a robust confidence score.
        Returns: (intent_name, confidence_score, debug_details)
        """
        text_lower = text.lower().strip()
        entities = self.extract_entities(text)
        language = self.detect_language(text)

        if not text_lower:
            return "general_inquiry", 0.0, {"reason": "empty input"}

        intent_scores: Dict[str, float] = {}
        matched_details: Dict[str, Any] = {}

        for intent, config in INTENT_PATTERNS.items():
            score = 0.0
            reasons = []

            # 1. Regex pattern matching
            for pattern in config["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 0.85
                    reasons.append(f"regex_match: {pattern[:25]}...")
                    break

            # 2. Keyword density
            kw_hits = [kw for kw in config["keywords"] if kw in text_lower]
            if kw_hits:
                kw_boost = min(len(kw_hits) * 0.20, 0.40)
                score += kw_boost
                reasons.append(f"keywords: {kw_hits}")

            # 3. Entity synergy bonus
            if intent == "order_tracking" and "order_id" in entities:
                score += 0.35
                reasons.append("order_id_present")
            elif intent == "billing_payment" and "amount" in entities:
                score += 0.25
                reasons.append("amount_present")
            elif intent == "account_access" and "email" in entities:
                score += 0.25
                reasons.append("email_present")

            # Base confidence adjustment
            if score > 0:
                final_score = min(score * config["base_confidence"], 0.98)
                intent_scores[intent] = round(final_score, 3)
                matched_details[intent] = {"score": round(final_score, 3), "reasons": reasons}

        if not intent_scores:
            # Fallback intent
            return "general_inquiry", 0.35, {"reason": "no pattern or keyword match"}

        # Priority arbitration: Domain-specific intents override pure greetings/smalltalk
        domain_intents = [
            "order_tracking", "refund_return", "human_escalation", 
            "billing_payment", "shipping_delivery", "account_access", 
            "product_inquiry"
        ]
        
        # Check if a domain intent is present alongside a greeting
        best_domain_intent = None
        best_domain_score = 0.0
        for d_intent in domain_intents:
            if d_intent in intent_scores and intent_scores[d_intent] >= 0.50:
                if intent_scores[d_intent] > best_domain_score:
                    best_domain_score = intent_scores[d_intent]
                    best_domain_intent = d_intent

        if best_domain_intent:
            best_intent = best_domain_intent
            best_score = best_domain_score
        else:
            best_intent = max(intent_scores, key=intent_scores.get)
            best_score = intent_scores[best_intent]

        return best_intent, best_score, {
            "all_scores": intent_scores,
            "entities": entities,
            "language": language,
            "top_match": matched_details.get(best_intent, {})
        }

# Singleton instance
nlp = NLPEngine()
