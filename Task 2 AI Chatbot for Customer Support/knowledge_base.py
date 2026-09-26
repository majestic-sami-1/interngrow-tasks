import re
import math
from typing import List, Dict, Any, Tuple
from database import get_all_custom_faqs

# Default enterprise knowledge base entries
DEFAULT_FAQS: List[Dict[str, Any]] = [
    # Orders & Tracking
    {
        "id": "faq_ord_1",
        "category": "Order Tracking",
        "question": "How can I track my order?",
        "answer": "You can track your order at any time by providing your Order ID (format: ORD-XXXXX) right here in the chat, or by navigating to 'My Orders' in your account dashboard. You will also receive live email and SMS updates once your package is dispatched.",
        "keywords": ["track", "order", "status", "where is my order", "package", "shipment", "locate order"]
    },
    {
        "id": "faq_ord_2",
        "category": "Order Tracking",
        "question": "Can I modify or cancel my order after placing it?",
        "answer": "Orders can be modified or canceled within 60 minutes of placement before they move to warehouse processing. Please share your Order ID immediately or click 'Cancel Order' in your confirmation email.",
        "keywords": ["cancel", "modify", "change", "edit order", "wrong item", "cancel order", "stop order"]
    },
    {
        "id": "faq_ord_3",
        "category": "Order Tracking",
        "question": "What should I do if an item is missing from my delivery?",
        "answer": "Sometimes items are dispatched in separate packages from different fulfillment centers. Please check your tracking link for multiple package numbers. If all packages show delivered, contact us with your Order ID and photo proof within 48 hours for immediate replacement.",
        "keywords": ["missing item", "incomplete order", "package missing", "forgot item", "didn't receive everything"]
    },

    # Shipping & Delivery
    {
        "id": "faq_shp_1",
        "category": "Shipping & Delivery",
        "question": "What are your shipping rates and estimated delivery times?",
        "answer": "Standard Shipping takes 3-5 business days ($4.99 or FREE for orders over $50). Express Shipping takes 1-2 business days ($12.99). International shipping takes 7-14 business days depending on customs clearance.",
        "keywords": ["shipping time", "delivery time", "shipping cost", "free shipping", "how long", "express shipping", "rates"]
    },
    {
        "id": "faq_shp_2",
        "category": "Shipping & Delivery",
        "question": "Do you offer international shipping?",
        "answer": "Yes! We ship to over 65 countries worldwide via DHL Express and FedEx. Customs duties and local import taxes are calculated at checkout so there are no surprise fees on arrival.",
        "keywords": ["international shipping", "ship worldwide", "deliver abroad", "overseas", "customs", "global"]
    },
    {
        "id": "faq_shp_3",
        "category": "Shipping & Delivery",
        "question": "My tracking shows 'Delivered' but I haven't received it. What should I do?",
        "answer": "Please check with household members or building reception, as carriers sometimes leave packages in safe spots. If you still cannot locate it after 24 hours, let us know and we will open a courier investigation or reship your parcel.",
        "keywords": ["lost package", "delivered but not here", "stolen", "haven't received", "where is it"]
    },

    # Returns, Refunds & Exchanges
    {
        "id": "faq_ret_1",
        "category": "Returns & Refunds",
        "question": "What is your return policy?",
        "answer": "We offer a 30-day hassle-free return policy on all unworn, undamaged items in their original packaging. Return shipping is free for domestic store exchanges or store credit, and an $8 handling fee applies for cash refunds.",
        "keywords": ["return policy", "how to return", "30 days", "exchange", "refund policy", "send back"]
    },
    {
        "id": "faq_ret_2",
        "category": "Returns & Refunds",
        "question": "How long does it take to receive my refund?",
        "answer": "Once our warehouse inspects the returned merchandise (usually within 2-3 business days of receipt), your refund will be processed to your original payment method. Depending on your bank, funds take 3-7 business days to reflect.",
        "keywords": ["refund time", "when do i get refund", "money back", "refund status", "how long refund"]
    },
    {
        "id": "faq_ret_3",
        "category": "Returns & Refunds",
        "question": "Can I exchange an item for a different size or color?",
        "answer": "Yes! Direct exchanges are completely free. Start an exchange request through our returns portal or tell me your Order ID and the preferred size/color you need.",
        "keywords": ["exchange size", "swap item", "change color", "different size", "exchange product"]
    },

    # Billing & Payments
    {
        "id": "faq_bil_1",
        "category": "Billing & Payments",
        "question": "What payment methods do you accept?",
        "answer": "We accept all major credit and debit cards (Visa, MasterCard, American Express, Discover), PayPal, Apple Pay, Google Pay, and flexible interest-free installments via Klarna and Afterpay.",
        "keywords": ["payment methods", "credit card", "paypal", "apple pay", "how to pay", "klarna", "installments"]
    },
    {
        "id": "faq_bil_2",
        "category": "Billing & Payments",
        "question": "Why was my payment declined?",
        "answer": "Common reasons include billing address mismatches, insufficient funds, or international transaction protection triggered by your bank. We recommend verifying your card details or trying PayPal / Apple Pay.",
        "keywords": ["payment declined", "card failed", "payment error", "transaction failed", "cannot pay"]
    },
    {
        "id": "faq_bil_3",
        "category": "Billing & Payments",
        "question": "How can I download a VAT receipt or invoice?",
        "answer": "Official VAT invoices are attached as PDF files to your order confirmation email. You can also download itemized receipts at any time under 'Account > Order History > Download Invoice'.",
        "keywords": ["invoice", "receipt", "vat", "tax invoice", "download invoice", "bill"]
    },

    # Account & Security
    {
        "id": "faq_acc_1",
        "category": "Account & Security",
        "question": "How do I reset my account password?",
        "answer": "Click on 'Forgot Password' on the login screen, enter your registered email address, and an instant secure password reset link will be sent to your inbox. The link is valid for 2 hours.",
        "keywords": ["reset password", "forgot password", "change password", "cannot login", "locked out"]
    },
    {
        "id": "faq_acc_2",
        "category": "Account & Security",
        "question": "How do I update my shipping address or phone number?",
        "answer": "You can update saved delivery addresses and contact information in your profile under 'Account Settings > Address Book'. If an order is already placed, contact us immediately with your Order ID to reroute it before dispatch.",
        "keywords": ["change address", "update address", "wrong address", "new address", "update phone"]
    },
    {
        "id": "faq_acc_3",
        "category": "Account & Security",
        "question": "How do I delete my account or request my data?",
        "answer": "In compliance with GDPR and CCPA privacy standards, you can request full account deletion or a copy of your personal data by submitting a request under 'Privacy & Security' in your account settings.",
        "keywords": ["delete account", "remove data", "gdpr", "privacy", "close account"]
    },

    # Technical Support & Warranty
    {
        "id": "faq_tec_1",
        "category": "Technical Support",
        "question": "What is the warranty coverage on purchased products?",
        "answer": "All electronic devices and hardware come with a comprehensive 12-month manufacturer warranty covering manufacturer defects and component failures. Accidental damage coverage can be added via our Care+ plan.",
        "keywords": ["warranty", "guarantee", "repair", "broken item", "defective", "malfunction"]
    },
    {
        "id": "faq_tec_2",
        "category": "Technical Support",
        "question": "How do I troubleshoot a malfunctioning product?",
        "answer": "We recommend: 1) Performing a factory reset by holding the power button for 10 seconds, 2) Checking for the latest firmware update via the companion app, and 3) Verifying battery charge. If the issue persists, our technical team will issue a warranty replacement.",
        "keywords": ["troubleshoot", "device not working", "reset device", "defect", "won't turn on", "hardware issue"]
    },
    {
        "id": "faq_tec_3",
        "category": "Technical Support",
        "question": "How can I speak to a live human support agent?",
        "answer": "Our live human customer care agents are available Monday through Sunday, 24/7. Type 'Speak to agent' or click the 'Escalate to Support Ticket' button, and our team will connect with you via live chat or follow up via email within 15 minutes.",
        "keywords": ["human agent", "talk to human", "customer service rep", "real person", "support representative", "escalate", "agent"]
    }
]

def stem_token(word: str) -> str:
    """Simple morphological normalization for customer support tokens."""
    w = word.lower().strip()
    for suffix in ['ing', 'ies', 'es', 's', 'ed']:
        if w.endswith(suffix) and len(w) > len(suffix) + 2:
            if suffix == 'ies':
                return w[:-3] + 'y'
            return w[:-len(suffix)]
    return w

def clean_tokens(text: str) -> List[str]:
    """Tokenize and clean text into normalized terms."""
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for',
        'of', 'and', 'or', 'do', 'does', 'did', 'i', 'my', 'me', 'you', 'your', 'we',
        'it', 'can', 'how', 'what', 'why', 'when', 'where', 'who', 'please'
    }
    raw_tokens = [t for t in cleaned.split() if len(t) > 1 and t not in stop_words]
    stemmed = [stem_token(t) for t in raw_tokens]
    return list(set(raw_tokens + stemmed))

class KnowledgeBase:
    def __init__(self):
        self._static_faqs = DEFAULT_FAQS

    def get_all_faqs(self) -> List[Dict[str, Any]]:
        """Retrieve static FAQs combined with any user-added custom database FAQs."""
        custom_rows = get_all_custom_faqs()
        custom_faqs = []
        for r in custom_rows:
            kw = [k.strip().lower() for k in (r.get("keywords") or "").split(",") if k.strip()]
            custom_faqs.append({
                "id": f"custom_{r['id']}",
                "category": r["category"],
                "question": r["question"],
                "answer": r["answer"],
                "keywords": kw
            })
        return self._static_faqs + custom_faqs

    def search(self, query: str, top_k: int = 3, threshold: float = 0.25) -> List[Dict[str, Any]]:
        """
        Search knowledge base using multi-factor token similarity, 
        phrase overlap, and keyword matching.
        Returns matched entries sorted by confidence score (0.0 to 1.0).
        """
        query_lower = query.lower().strip()
        query_tokens = set(clean_tokens(query_lower))
        
        if not query_tokens and not query_lower:
            return []

        all_faqs = self.get_all_faqs()
        results = []

        for faq in all_faqs:
            q_text = faq["question"].lower()
            q_tokens = set(clean_tokens(q_text))
            keywords = [k.lower() for k in faq.get("keywords", [])]
            
            # Exact phrase match boost
            exact_match_score = 0.0
            if q_text in query_lower or query_lower in q_text:
                exact_match_score = 0.50

            # Keyword matches
            keyword_score = 0.0
            matched_keywords = []
            for kw in keywords:
                kw_stem = stem_token(kw)
                if kw in query_lower or kw_stem in query_lower:
                    matched_keywords.append(kw)
                    keyword_score += 0.35
                else:
                    # Token overlap with keyword
                    kw_tokens = set(clean_tokens(kw))
                    if kw_tokens and kw_tokens.intersection(query_tokens):
                        matched_keywords.append(kw)
                        keyword_score += 0.25
            
            keyword_score = min(keyword_score, 0.70)

            # Token Jaccard / Overlap similarity with question
            token_intersection = query_tokens.intersection(q_tokens)
            token_overlap = (len(token_intersection) / len(query_tokens)) if query_tokens else 0.0

            # Combined weighted score
            total_score = (token_overlap * 0.40) + keyword_score + exact_match_score
            
            # Cap at 0.99
            score = round(min(total_score, 0.99), 3)

            if score >= threshold:
                results.append({
                    "faq": faq,
                    "score": score,
                    "matched_tokens": list(token_intersection),
                    "matched_keywords": matched_keywords
                })

        # Sort descending by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

# Singleton instance
kb = KnowledgeBase()
