import json
import random
from typing import Dict, Any, Tuple, Optional
from database import get_session, update_session, create_ticket
from knowledge_base import kb
from nlp_engine import nlp

# Multi-lingual conversational response templates
MULTILINGUAL_GREETINGS = {
    "en": "Hello! Welcome to Customer Support. How can I assist you today? You can ask about order tracking, returns, shipping, billing, or speak with an agent.",
    "es": "¡Hola! Bienvenido a Atención al Cliente. ¿Cómo puedo ayudarte hoy? Puedes consultar sobre el seguimiento de pedidos, devoluciones, envíos, facturación o hablar con un agente.",
    "fr": "Bonjour ! Bienvenue au service client. Comment puis-je vous aider aujourd'hui ? Vous pouvez vous renseigner sur le suivi de commande, les retours, la livraison ou parler à un conseiller.",
    "de": "Hallo! Willkommen beim Kundenservice. Wie kann ich Ihnen heute helfen? Sie können nach Bestellstatus, Rücksendungen, Versand oder Rechnungen fragen.",
    "ur": "السلام علیکم! کسٹمر سپورٹ میں خوش آمدید۔ آج میں آپ کی کیا مدد کر سکتا ہوں؟ آپ آرڈر ٹریکنگ، واپسی، بلنگ یا نمائندے سے بات کرنے کے بارے میں پوچھ سکتے ہیں۔",
    "hi": "नमस्ते! ग्राहक सेवा में आपका स्वागत है। आज मैं आपकी क्या सहायता कर सकता हूँ? आप ऑर्डर ट्रैकिंग, रिफंड, शिपिंग या बिलिंग के बारे میں पूछ सकते हैं।",
    "ar": "مرحبا بك في خدمة العملاء! كيف يمكنني مساعدتك اليوم؟ يمكنك الاستفسار عن تتبع الطلبات، الإرجاع، الشحن، الفواتير أو التحدث مع ممثل الدعم."
}

MULTILINGUAL_GOODBYES = {
    "en": "Thank you for contacting Customer Support! Have a wonderful day, and please reach out anytime if you need anything else.",
    "es": "¡Gracias por comunicarte con Atención al Cliente! Que tengas un excelente día y no dudes en contactarnos si necesitas algo más.",
    "fr": "Merci d'avoir contacté notre service client ! Passez une excellente journée et n'hésitez pas à revenir vers nous.",
    "de": "Vielen Dank für Ihre Kontaktaufnahme! Ich wünsche Ihnen einen schönen Tag. Melden Sie sich gerne jederzeit wieder.",
    "ur": "کسٹمر سپورٹ سے رابطہ کرنے کا شکریہ! آپ کا دن اچھا گزرے، کسی بھی وقت دوبارہ رابطہ کر سکتے ہیں۔",
    "hi": "ग्राहक सेवा से संपर्क करने के लिए धन्यवाद! आपका दिन शुभ हो, किसी भी सहायता के लिए फिर संपर्क करें।",
    "ar": "شكراً لتواصلك مع خدمة العملاء! نتمنى لك يوماً رائعاً، ولا تتردد في التواصل معنا في أي وقت."
}

MULTILINGUAL_ASK_ORDER_ID = {
    "en": "I'd be happy to check your order status! Could you please provide your Order ID (for example, ORD-12345 or #54321)?",
    "es": "¡Con gusto consulto el estado de tu pedido! ¿Podrías indicarme tu número de pedido (por ejemplo, ORD-12345)?",
    "fr": "Je serais ravi de vérifier votre commande ! Pourriez-vous me fournir votre numéro de commande (ex. ORD-12345) ?",
    "de": "Gerne überprüfe ich Ihren Bestellstatus! Könnten Sie mir bitte Ihre Bestellnummer mitteilen (z. B. ORD-12345)?",
    "ur": "میں آپ کے آرڈر کا اسٹیٹس خوشی سے چیک کر سکتا ہوں۔ براہ کرم اپنا آرڈر نمبر بتائیں (مثلاً ORD-12345)؟",
    "hi": "मुझे आपके ऑर्डर की स्थिति जांचने में खुशी होगी! कृपया अपना ऑर्डर नंबर प्रदान करें (जैसे ORD-12345)?",
    "ar": "يسعدني التحقق من حالة طلبك! هل يمكنك تزويدي برقم الطلب (مثال: ORD-12345)؟"
}

# Simulated realistic order tracking database
MOCK_ORDERS = {
    "ORD-10001": {"status": "Delivered", "courier": "DHL Express", "eta": "Delivered yesterday at 2:15 PM", "items": "Wireless Noise-Canceling Headphones"},
    "ORD-10002": {"status": "Out for Delivery", "courier": "FedEx Ground", "eta": "Today by 6:00 PM", "items": "Ergonomic Mechanical Keyboard"},
    "ORD-10003": {"status": "In Transit", "courier": "UPS Express", "eta": "Tomorrow by 2:00 PM", "items": "4K Ultra-HD Web Camera"},
    "ORD-10004": {"status": "Processing in Warehouse", "courier": "USPS Priority", "eta": "Estimated dispatch in 24 hours", "items": "USB-C Dual Display Dock"}
}

def generate_mock_order_status(order_id: str, lang: str = "en") -> str:
    """Generate or retrieve simulated tracking info for any order ID."""
    order_id_clean = order_id.upper()
    data = MOCK_ORDERS.get(order_id_clean)
    if not data:
        statuses = ["In Transit with Courier", "Departed Regional Sort Facility", "Out for Delivery"]
        couriers = ["DHL Express", "FedEx", "UPS Priority"]
        status = random.choice(statuses)
        courier = random.choice(couriers)
        eta = "In 2 business days"
        data = {"status": status, "courier": courier, "eta": eta, "items": "Online Order Items"}

    if lang == "es":
        return f"📦 **Actualización de Pedido ({order_id_clean})**:\n- **Estado:** {data['status']}\n- **Transportista:** {data['courier']}\n- **Fecha estimada:** {data['eta']}\n- **Artículos:** {data['items']}\n\n¿Deseas ayuda adicional con este envío?"
    elif lang == "fr":
        return f"📦 **Statut de votre commande ({order_id_clean})**:\n- **Statut :** {data['status']}\n- **Transporteur :** {data['courier']}\n- **Livraison estimée :** {data['eta']}\n- **Articles :** {data['items']}\n\nAvez-vous besoin d'autre chose ?"
    elif lang == "de":
        return f"📦 **Sendungsstatus ({order_id_clean})**:\n- **Status:** {data['status']}\n- **Versanddienst:** {data['courier']}\n- **Voraussichtliche Ankunft:** {data['eta']}\n- **Artikel:** {data['items']}\n\nKann ich Ihnen sonst noch helfen?"
    elif lang == "ur":
        return f"📦 **آپ کے آرڈر کا اسٹیٹس ({order_id_clean})**:\n- **حالت:** {data['status']}\n- **کورئیر:** {data['courier']}\n- **متوقع ڈیلیوری:** {data['eta']}\n- **سامان:** {data['items']}\n\nکیا آپ کو اس حوالے سے مزید مدد درکار ہے؟"
    elif lang == "hi":
        return f"📦 **ऑर्डर ट्रैकिंग विवरण ({order_id_clean})**:\n- **स्थिति:** {data['status']}\n- **कूरियर:** {data['courier']}\n- **अनुमानित समय:** {data['eta']}\n- **सामान:** {data['items']}\n\nक्या आपको कोई और सहायता चाहिए?"
    elif lang == "ar":
        return f"📦 **تحديث حالة الطلب ({order_id_clean})**:\n- **الحالة:** {data['status']}\n- **شركة الشحن:** {data['courier']}\n- **الموعد المتوقع:** {data['eta']}\n- **المنتجات:** {data['items']}\n\nهل تحتاج إلى مساعدة إضافية بخصوص هذا الطلب؟"

    return f"📦 **Order Tracking Details ({order_id_clean})**:\n- **Status:** {data['status']}\n- **Courier:** {data['courier']}\n- **Estimated Delivery:** {data['eta']}\n- **Package Contents:** {data['items']}\n\nWould you like me to assist you with anything else regarding this order?"

class ContextManager:
    """Maintains multi-turn conversation memory, slot filling, and fallback escalation."""

    def __init__(self):
        pass

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Fetch session context from database."""
        session = get_session(session_id)
        if not session:
            return {}
        try:
            return json.loads(session.get("context_data", "{}"))
        except Exception:
            return {}

    def save_context(self, session_id: str, context: Dict[str, Any], lang: str = None):
        """Update session context."""
        update_session(session_id, language=lang, context_data=context)

    def process_turn(self, session_id: str, user_text: str, current_lang: str = "en") -> Dict[str, Any]:
        """
        Process a multi-turn user message in context:
        1. Natural language understanding: intent & entity extraction.
        2. Context slot retention & pending slot filling.
        3. Knowledge base FAQ lookup.
        4. Multi-language response formulation.
        5. Confidence score calculation & human escalation trigger.
        """
        context = self.get_context(session_id)
        
        # Detect language or use user-selected language
        detected_lang = nlp.detect_language(user_text)
        active_lang = current_lang if current_lang and current_lang != "en" else detected_lang
        
        # 1. NLU Extraction
        intent, raw_confidence, nlu_meta = nlp.classify_intent(user_text)
        entities = nlu_meta.get("entities", {})

        # Merge extracted entities into persistent context
        for k, v in entities.items():
            if v:
                context[k] = v

        pending_slot = context.get("pending_slot")
        response_text = ""
        final_intent = intent
        confidence_score = raw_confidence
        action = None
        ticket_data = None
        suggest_escalation = False

        # --- Check pending slot resolution ---
        if pending_slot == "order_id":
            # Check if user just supplied an order ID or number
            order_id = entities.get("order_id")
            if not order_id:
                # Try raw digits or token
                digits_match = re.search(r'\b\d{4,8}\b', user_text)
                if digits_match:
                    order_id = f"ORD-{digits_match.group(0)}"
                    context["order_id"] = order_id

            if order_id:
                context["order_id"] = order_id
                context["pending_slot"] = None
                final_intent = "order_tracking"
                confidence_score = 0.96
                response_text = generate_mock_order_status(order_id, active_lang)
                self.save_context(session_id, context, active_lang)
                return {
                    "response": response_text,
                    "intent": final_intent,
                    "confidence": confidence_score,
                    "entities": context,
                    "language": active_lang,
                    "suggest_escalation": False,
                    "action": "order_tracked"
                }

        # --- Handle Core Intents with Context ---

        # 1. Greeting
        if intent == "greeting":
            response_text = MULTILINGUAL_GREETINGS.get(active_lang, MULTILINGUAL_GREETINGS["en"])
            confidence_score = 0.95

        # 2. Goodbye
        elif intent == "goodbye":
            response_text = MULTILINGUAL_GOODBYES.get(active_lang, MULTILINGUAL_GOODBYES["en"])
            confidence_score = 0.94

        # 3. Human Escalation Intent
        elif intent == "human_escalation":
            confidence_score = 0.95
            suggest_escalation = True
            action = "offer_ticket"
            if active_lang == "es":
                response_text = "Entiendo perfectamente. Me comunico con nuestro equipo humano de soporte. Puedes crear un ticket prioritario a continuación o un agente se unirá en breve."
            elif active_lang == "fr":
                response_text = "Je comprends tout à fait. Je vous mets en relation avec un conseiller humain. Vous pouvez générer un ticket prioritaire ci-dessous."
            elif active_lang == "de":
                response_text = "Ich verstehe vollkommen. Ich leite Sie an unser Support-Team weiter. Sie können unten ein Support-Ticket erstellen."
            elif active_lang == "ur":
                response_text = "میں آپ کی بات سمجھ گیا ہوں۔ میں آپ کو ایک حقیقی نمائندے سے جوڑ رہا ہوں۔ آپ نیچے دیئے گئے بٹن سے ترجیحی سپورٹ ٹکٹ بنا سکتے ہیں۔"
            elif active_lang == "hi":
                response_text = "मैं समझ गया। मैं आपको एक मानव सहायता एजेंट से जोड़ रहा हूँ। आप नीचे एक प्राथमिकता सहायता टिकट बना सकते हैं।"
            elif active_lang == "ar":
                response_text = "أنا أفهمك تماماً. سأقوم بتوجيهك إلى ممثل دعم بشري. يمكنك فتح تذكرة دعم ذات أولوية أدناه."
            else:
                response_text = "I completely understand. I'm connecting you with our human support team. You can submit a priority support ticket using the quick form below, and an agent will respond promptly."

        # 4. Order Tracking Flow
        elif intent == "order_tracking":
            order_id = context.get("order_id")
            if order_id:
                confidence_score = 0.95
                response_text = generate_mock_order_status(order_id, active_lang)
            else:
                context["pending_slot"] = "order_id"
                context["last_intent"] = "order_tracking"
                confidence_score = 0.90
                response_text = MULTILINGUAL_ASK_ORDER_ID.get(active_lang, MULTILINGUAL_ASK_ORDER_ID["en"])

        # 5. Bot Info
        elif intent == "bot_info":
            confidence_score = 0.96
            if active_lang == "es":
                response_text = "Soy el **Asistente Virtual de Atención al Cliente** impulsado por IA. Puedo rastrear pedidos, gestionar devoluciones, responder preguntas frecuentes sobre envíos y facturación, o conectarte con un agente humano."
            elif active_lang == "fr":
                response_text = "Je suis l'**Assistant Virtuel de Support Client** propulsé par l'IA. Je peux vous aider à suivre vos commandes, gérer vos retours, répondre à vos questions et contacter un conseiller."
            elif active_lang == "de":
                response_text = "Ich bin der **KI-Kundenservice-Assistent**. Ich kann Bestellungen verfolgen, Rücksendungen bearbeiten, Fragen zu Versand & Abrechnung beantworten oder Sie mit einem Mitarbeiter verbinden."
            elif active_lang == "ur":
                response_text = "میں ایک **مصنوعی ذہانت کسٹمر سپورٹ اسسٹنٹ** ہوں۔ میں آپ کے آرڈرز ٹریک کر سکتا ہوں، واپسیوں اور ریفنڈ میں مدد کر سکتا ہوں، عمومی سوالات کے جوابات دے سکتا ہوں، یا لائیو نمائندے سے رابطہ کرا سکتا ہوں۔"
            elif active_lang == "hi":
                response_text = "मैं एक **एआई ग्राहक सहायता सहायक** हूँ। मैं आपके ऑर्डर ट्रैक कर सकता हूँ, रिटर्न में मदद कर सकता हूँ, अक्सर पूछे जाने वाले प्रश्नों के उत्तर दे सकता हूँ।"
            elif active_lang == "ar":
                response_text = "أنا **المساعد الافتراضي الذكي لخدمة العملاء**. يمكنني مساعدتك في تتبع الطلبات، إدارة المرتجعات، الإجابة عن الاستفسارات، أو ربطك بموظف دعم بشري."
            else:
                response_text = "I am your **AI Customer Support Assistant**. I can help you track orders, process returns & refunds, answer questions about shipping, billing, and warranty, or transfer you to a human representative."

        # 6. FAQ Knowledge Base Lookup for other intents or inquiries
        if not response_text:
            faq_matches = kb.search(user_text, top_k=2, threshold=0.35)
            if faq_matches:
                top_match = faq_matches[0]
                faq_data = top_match["faq"]
                faq_score = top_match["score"]
                
                # Boost confidence if FAQ score is strong
                confidence_score = max(raw_confidence, faq_score)
                response_text = f"**{faq_data['question']}**\n\n{faq_data['answer']}"
                action = f"faq_category:{faq_data.get('category')}"
            else:
                # If no FAQ found and confidence is moderate/low
                if raw_confidence < 0.60:
                    confidence_score = round(raw_confidence, 2)
                    suggest_escalation = True
                    if active_lang == "es":
                        response_text = "No estoy completamente seguro de haber entendido los detalles. ¿Deseas que transfiera tu consulta a un representante humano de soporte?"
                    elif active_lang == "fr":
                        response_text = "Je ne suis pas tout à fait certain d'avoir compris votre demande. Souhaitez-vous que je transmette votre dossier à un conseiller ?"
                    elif active_lang == "de":
                        response_text = "Ich bin mir nicht ganz sicher, ob ich Ihr Anliegen richtig verstanden habe. Möchten Sie, dass ich Sie an einen Mitarbeiter weiterleite?"
                    elif active_lang == "ur":
                        response_text = "معذرت، میں آپ کا سوال مکمل طور پر نہیں سمجھ سکا۔ کیا آپ لائیو ایجنٹ کے لیے سپورٹ ٹکٹ بنانا چاہیں گے؟"
                    elif active_lang == "hi":
                        response_text = "क्षमा करें, मैं आपका प्रश्न पूरी तरह से नहीं समझ पाया। क्या आप मानव प्रतिनिधि से सहायता चाहते हैं?"
                    elif active_lang == "ar":
                        response_text = "عذراً، لست متأكداً تماماً من تفاصيل استفسارك. هل ترغب في تحويلك إلى ممثل خدمة عملاء بشري؟"
                    else:
                        response_text = "I'm not entirely certain I have the complete answer for that specific request. Would you like me to connect you with a live human support specialist, or could you clarify your question?"
                else:
                    confidence_score = round(raw_confidence, 2)
                    response_text = f"Thank you for your inquiry regarding {intent.replace('_', ' ')}. Our customer care team is reviewing this topic. Please feel free to provide any relevant order number or account email."

        # Save updated context
        context["last_intent"] = final_intent
        context["last_confidence"] = confidence_score
        self.save_context(session_id, context, active_lang)

        return {
            "response": response_text,
            "intent": final_intent,
            "confidence": confidence_score,
            "entities": context,
            "language": active_lang,
            "suggest_escalation": suggest_escalation,
            "action": action
        }

# Singleton instance
context_mgr = ContextManager()
