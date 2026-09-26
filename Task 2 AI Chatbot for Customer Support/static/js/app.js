/**
 * NOVA AI - Enterprise Customer Support Chatbot Client Logic
 * Features: NLU, Context Tracking, FAQ Search, Voice STT, TTS, Multilingual, Tickets
 */

// State Management
const state = {
  currentSessionId: null,
  activeLanguage: 'en',
  autoTts: false,
  isRecording: false,
  recognition: null,
  selectedVoice: null,
  speechRate: 1.0,
  sessions: [],
  tickets: [],
  faqs: [],
  currentFaqCategory: 'All',
  theme: localStorage.getItem('nova_theme') || 'dark'
};

// Language map for Web Speech API & TTS
const LANG_LOCALES = {
  en: 'en-US',
  es: 'es-ES',
  fr: 'fr-FR',
  de: 'de-DE',
  ur: 'ur-PK',
  hi: 'hi-IN',
  ar: 'ar-SA'
};

// DOM Elements
const chatMessagesContainer = document.getElementById('chatMessagesContainer');
const chatMessagesStream = document.getElementById('chatMessagesStream');
const chatInputField = document.getElementById('chatInputField');
const sendMessageBtn = document.getElementById('sendMessageBtn');
const voiceInputBtn = document.getElementById('voiceInputBtn');
const voiceWaveBar = document.getElementById('voiceWaveBar');
const stopVoiceBtn = document.getElementById('stopVoiceBtn');
const typingIndicator = document.getElementById('typingIndicator');
const newChatBtn = document.getElementById('newChatBtn');
const sessionsList = document.getElementById('sessionsList');
const languageSelector = document.getElementById('languageSelector');
const ttsAutoToggleBtn = document.getElementById('ttsAutoToggleBtn');
const themeToggleBtn = document.getElementById('themeToggleBtn');
const inspectorToggleBtn = document.getElementById('inspectorToggleBtn');
const closeInspectorBtn = document.getElementById('closeInspectorBtn');
const sidebarRight = document.getElementById('sidebarRight');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const sidebarLeft = document.getElementById('sidebarLeft');
const exportChatBtn = document.getElementById('exportChatBtn');
const toastNotification = document.getElementById('toastNotification');

// Inspector Elements
const inspectorIntentBadge = document.getElementById('inspectorIntentBadge');
const inspectorIntentText = document.getElementById('inspectorIntentText');
const inspectorConfidenceVal = document.getElementById('inspectorConfidenceVal');
const inspectorConfidenceFill = document.getElementById('inspectorConfidenceFill');
const inspectorConfidenceLabel = document.getElementById('inspectorConfidenceLabel');
const entityOrderId = document.getElementById('entityOrderId');
const entityCustomerName = document.getElementById('entityCustomerName');
const entityEmail = document.getElementById('entityEmail');
const entityLang = document.getElementById('entityLang');
const escalateTicketBtn = document.getElementById('escalateTicketBtn');
const ttsVoiceSelect = document.getElementById('ttsVoiceSelect');
const ttsRateSlider = document.getElementById('ttsRateSlider');
const ttsRateVal = document.getElementById('ttsRateVal');

// Modals
const faqModal = document.getElementById('faqModal');
const openFaqModalBtn = document.getElementById('openFaqModalBtn');
const closeFaqModalBtn = document.getElementById('closeFaqModalBtn');
const faqSearchInput = document.getElementById('faqSearchInput');
const faqCategoryPills = document.getElementById('faqCategoryPills');
const faqItemsList = document.getElementById('faqItemsList');
const toggleAddFaqBtn = document.getElementById('toggleAddFaqBtn');
const addFaqForm = document.getElementById('addFaqForm');
const saveFaqBtn = document.getElementById('saveFaqBtn');

const ticketsModal = document.getElementById('ticketsModal');
const openTicketsModalBtn = document.getElementById('openTicketsModalBtn');
const closeTicketsModalBtn = document.getElementById('closeTicketsModalBtn');
const ticketCountBadge = document.getElementById('ticketCountBadge');
const ticketsContainer = document.getElementById('ticketsContainer');
const submitTicketBtn = document.getElementById('submitTicketBtn');

const settingsModal = document.getElementById('settingsModal');
const openSettingsModalBtn = document.getElementById('openSettingsModalBtn');
const closeSettingsModalBtn = document.getElementById('closeSettingsModalBtn');
const llmProviderSelect = document.getElementById('llmProviderSelect');
const apiKeyGroup = document.getElementById('apiKeyGroup');
const llmApiKeyInput = document.getElementById('llmApiKeyInput');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const activeEngineText = document.getElementById('activeEngineText');

// =========================================================
// INITIALIZATION
// =========================================================
document.addEventListener('DOMContentLoaded', async () => {
  applyTheme(state.theme);
  initSpeechSynthesis();
  initSpeechRecognition();
  initEventListeners();
  
  await fetchSettings();
  await loadSessions();
  await loadTickets();
  
  if (!state.currentSessionId) {
    await startNewSession();
  }
});

// =========================================================
// THEME & UTILS
// =========================================================
function applyTheme(theme) {
  state.theme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('nova_theme', theme);
}

function showToast(message, duration = 3000) {
  toastNotification.textContent = message;
  toastNotification.classList.add('show');
  setTimeout(() => toastNotification.classList.remove('show'), duration);
}

// =========================================================
// SPEECH SYNTHESIS (TTS)
// =========================================================
function initSpeechSynthesis() {
  if (!('speechSynthesis' in window)) {
    console.warn('Speech Synthesis is not supported in this browser.');
    return;
  }

  function populateVoices() {
    const voices = window.speechSynthesis.getVoices();
    ttsVoiceSelect.innerHTML = '';
    
    voices.forEach((v, index) => {
      const opt = document.createElement('option');
      opt.value = index;
      opt.textContent = `${v.name} (${v.lang})`;
      if (v.default || v.lang.startsWith(state.activeLanguage)) {
        opt.selected = true;
        state.selectedVoice = v;
      }
      ttsVoiceSelect.appendChild(opt);
    });
  }

  populateVoices();
  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = populateVoices;
  }

  ttsVoiceSelect.addEventListener('change', (e) => {
    const voices = window.speechSynthesis.getVoices();
    state.selectedVoice = voices[e.target.value] || null;
  });

  ttsRateSlider.addEventListener('input', (e) => {
    state.speechRate = parseFloat(e.target.value);
    ttsRateVal.textContent = `${state.speechRate.toFixed(1)}x`;
  });
}

function speakText(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel(); // Stop any active speech

  // Clean markdown syntax for speech
  const clean = text.replace(/[*#_`\[\]()]/g, ' ').trim();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = state.speechRate;

  // Attempt to match voice for active language
  const voices = window.speechSynthesis.getVoices();
  const targetLocale = LANG_LOCALES[state.activeLanguage] || 'en-US';
  const matchedVoice = voices.find(v => v.lang.replace('_', '-').startsWith(state.activeLanguage)) || state.selectedVoice;
  
  if (matchedVoice) {
    utterance.voice = matchedVoice;
  }
  utterance.lang = targetLocale;

  window.speechSynthesis.speak(utterance);
}

// =========================================================
// SPEECH RECOGNITION (VOICE INPUT / STT)
// =========================================================
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceInputBtn.style.display = 'none';
    console.warn('Speech Recognition not supported in this browser.');
    return;
  }

  state.recognition = new SpeechRecognition();
  state.recognition.continuous = false;
  state.recognition.interimResults = true;
  state.recognition.lang = LANG_LOCALES[state.activeLanguage] || 'en-US';

  state.recognition.onstart = () => {
    state.isRecording = true;
    voiceInputBtn.classList.add('recording');
    voiceWaveBar.style.display = 'flex';
  };

  state.recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    chatInputField.value = transcript;
  };

  state.recognition.onerror = (event) => {
    console.warn('Speech recognition error:', event.error);
    stopRecording();
    showToast(`Voice error: ${event.error}`);
  };

  state.recognition.onend = () => {
    stopRecording();
    // Auto submit if text was transcribed
    const text = chatInputField.value.trim();
    if (text) {
      handleSendMessage();
    }
  };
}

function startRecording() {
  if (!state.recognition) return;
  try {
    state.recognition.lang = LANG_LOCALES[state.activeLanguage] || 'en-US';
    state.recognition.start();
  } catch (err) {
    console.error(err);
  }
}

function stopRecording() {
  state.isRecording = false;
  voiceInputBtn.classList.remove('recording');
  voiceWaveBar.style.display = 'none';
  if (state.recognition) {
    try { state.recognition.stop(); } catch (e) {}
  }
}

// =========================================================
// SESSION MANAGEMENT & API CALLS
// =========================================================
async function loadSessions() {
  try {
    const res = await fetch('/api/sessions');
    const data = await res.json();
    if (data.status === 'success') {
      state.sessions = data.sessions;
      renderSessionsList();
    }
  } catch (err) {
    console.error('Failed to load sessions:', err);
  }
}

function renderSessionsList() {
  sessionsList.innerHTML = '';
  if (state.sessions.length === 0) {
    sessionsList.innerHTML = '<div style="font-size:0.75rem;color:var(--text-faint);padding:8px;">No chat history yet.</div>';
    return;
  }

  state.sessions.forEach(s => {
    const item = document.createElement('div');
    item.className = `session-item ${s.id === state.currentSessionId ? 'active' : ''}`;
    item.innerHTML = `
      <div class="session-title-wrap">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span title="${s.title}">${s.title}</span>
      </div>
      <button class="delete-session-btn" title="Delete Session" data-id="${s.id}">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
        </svg>
      </button>
    `;

    item.addEventListener('click', (e) => {
      if (!e.target.closest('.delete-session-btn')) {
        switchSession(s.id);
      }
    });

    const deleteBtn = item.querySelector('.delete-session-btn');
    deleteBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      await deleteSession(s.id);
    });

    sessionsList.appendChild(item);
  });
}

async function startNewSession() {
  try {
    const res = await fetch('/api/sessions/new', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: state.activeLanguage })
    });
    const data = await res.json();
    if (data.status === 'success') {
      state.currentSessionId = data.session_id;
      await loadSessions();
      await switchSession(data.session_id);
    }
  } catch (err) {
    console.error('Failed to create session:', err);
  }
}

async function switchSession(sessionId) {
  state.currentSessionId = sessionId;
  renderSessionsList();

  // Close mobile menu if open
  sidebarLeft.classList.remove('open');

  try {
    const res = await fetch(`/api/sessions/${sessionId}/messages`);
    const data = await res.json();
    if (data.status === 'success') {
      chatMessagesStream.innerHTML = '';
      data.messages.forEach(msg => {
        appendMessageRow(msg.sender, msg.content, msg.intent, msg.confidence, msg.metadata);
      });
      scrollToBottom();

      // Update Inspector with latest bot message or session context
      if (data.session && data.session.context_data) {
        try {
          const ctx = JSON.parse(data.session.context_data);
          updateInspector(
            ctx.last_intent || 'greeting',
            ctx.last_confidence || 0.95,
            ctx,
            data.session.language || state.activeLanguage
          );
        } catch (e) {}
      }
    }
  } catch (err) {
    console.error('Failed to load messages:', err);
  }
}

async function deleteSession(sessionId) {
  try {
    await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
    state.sessions = state.sessions.filter(s => s.id !== sessionId);
    if (state.currentSessionId === sessionId) {
      if (state.sessions.length > 0) {
        await switchSession(state.sessions[0].id);
      } else {
        await startNewSession();
      }
    } else {
      renderSessionsList();
    }
    showToast('Session deleted.');
  } catch (err) {
    console.error('Error deleting session:', err);
  }
}

// =========================================================
// CHAT MESSAGING LOGIC
// =========================================================
async function handleSendMessage(overrideText = null) {
  const text = overrideText !== null ? overrideText : chatInputField.value.trim();
  if (!text) return;

  chatInputField.value = '';
  chatInputField.style.height = 'auto';

  // 1. Append User Message
  appendMessageRow('user', text);
  scrollToBottom();

  // 2. Show Typing Indicator
  typingIndicator.style.display = 'flex';
  scrollToBottom();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.currentSessionId,
        message: text,
        language: state.activeLanguage
      })
    });

    const data = await res.json();
    typingIndicator.style.display = 'none';

    if (data.status === 'success') {
      // Append Bot Reply
      appendMessageRow(
        'bot',
        data.response,
        data.intent,
        data.confidence,
        {
          suggest_escalation: data.suggest_escalation,
          provider: data.provider
        }
      );
      scrollToBottom();

      // Update Inspector Sidebar
      updateInspector(data.intent, data.confidence, data.entities, data.language);

      // Auto TTS if enabled
      if (state.autoTts) {
        speakText(data.response);
      }

      // Update Sessions list title if needed
      loadSessions();
    } else {
      appendMessageRow('bot', '⚠️ Sorry, there was an issue processing your request.');
    }
  } catch (err) {
    typingIndicator.style.display = 'none';
    appendMessageRow('bot', '⚠️ Network error. Please verify your connection.');
    console.error('Chat error:', err);
  }
}

function appendMessageRow(sender, content, intent = null, confidence = null, metadata = {}) {
  const row = document.createElement('div');
  row.className = `message-row ${sender}`;

  // Avatar
  const avatar = document.createElement('div');
  avatar.className = `avatar-badge ${sender === 'bot' ? 'bot-avatar' : 'user-avatar'}`;
  avatar.textContent = sender === 'bot' ? 'N' : 'U';
  row.appendChild(avatar);

  // Bubble Wrapper
  const bubbleWrap = document.createElement('div');
  bubbleWrap.className = 'message-bubble-wrap';

  // Meta tags (Bot messages only)
  if (sender === 'bot' && intent) {
    const metaBar = document.createElement('div');
    metaBar.className = 'message-meta-tags';

    const intentTag = document.createElement('span');
    intentTag.className = 'intent-tag';
    intentTag.innerHTML = `🎯 ${intent.replace(/_/g, ' ')}`;
    metaBar.appendChild(intentTag);

    if (confidence !== null && confidence !== undefined) {
      const confTag = document.createElement('span');
      const confPct = Math.round(confidence * 100);
      let confLevel = 'high';
      if (confidence < 0.6) confLevel = 'low';
      else if (confidence < 0.8) confLevel = 'medium';
      
      confTag.className = `confidence-tag ${confLevel}`;
      confTag.innerHTML = `⚡ ${confPct}% Confidence`;
      metaBar.appendChild(confTag);
    }

    bubbleWrap.appendChild(metaBar);
  }

  // Content Bubble (Markdown parsed)
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  if (typeof marked !== 'undefined') {
    bubble.innerHTML = marked.parse(content);
  } else {
    bubble.textContent = content;
  }
  bubbleWrap.appendChild(bubble);

  // Message Actions (Bot messages only)
  if (sender === 'bot') {
    const actionsBar = document.createElement('div');
    actionsBar.className = 'message-actions';

    // Speaker TTS Button
    const ttsBtn = document.createElement('button');
    ttsBtn.className = 'action-chip-btn';
    ttsBtn.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
      </svg>
      Read Aloud
    `;
    ttsBtn.addEventListener('click', () => speakText(content));
    actionsBar.appendChild(ttsBtn);

    // Copy Button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'action-chip-btn';
    copyBtn.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
      Copy
    `;
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(content);
      showToast('Copied to clipboard!');
    });
    actionsBar.appendChild(copyBtn);

    bubbleWrap.appendChild(actionsBar);

    // If escalation suggested, show inline ticket prompt
    if (metadata && metadata.suggest_escalation) {
      const escalateBox = document.createElement('div');
      escalateBox.className = 'escalate-inline-box';
      escalateBox.innerHTML = `
        <span class="escalate-inline-text">Need human support specialist?</span>
        <button class="inline-ticket-btn">Open Support Ticket</button>
      `;
      escalateBox.querySelector('.inline-ticket-btn').addEventListener('click', () => {
        openTicketModalWithContext();
      });
      bubbleWrap.appendChild(escalateBox);
    }
  }

  row.appendChild(bubbleWrap);
  chatMessagesStream.appendChild(row);
}

function scrollToBottom() {
  chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

// =========================================================
// CONTEXT & INSPECTOR LOGIC
// =========================================================
function updateInspector(intent, confidence, entities = {}, lang = 'en') {
  // Intent
  inspectorIntentText.textContent = intent || 'general_inquiry';
  
  // Confidence
  const conf = confidence !== null && confidence !== undefined ? confidence : 0.90;
  const pct = Math.round(conf * 100);
  inspectorConfidenceVal.textContent = `${pct}%`;
  inspectorConfidenceFill.style.width = `${pct}%`;

  inspectorConfidenceFill.className = 'confidence-bar-fill';
  if (conf >= 0.8) {
    inspectorConfidenceFill.classList.add('high-confidence');
    inspectorConfidenceLabel.textContent = 'High Confidence (Direct Match)';
  } else if (conf >= 0.6) {
    inspectorConfidenceFill.classList.add('medium-confidence');
    inspectorConfidenceLabel.textContent = 'Moderate Confidence';
  } else {
    inspectorConfidenceFill.classList.add('low-confidence');
    inspectorConfidenceLabel.textContent = 'Low Confidence (Human Escalation Suggested)';
  }

  // Entities
  entityOrderId.innerHTML = entities.order_id ? `<strong>${entities.order_id}</strong>` : '<span class="empty-val">None</span>';
  entityCustomerName.innerHTML = entities.customer_name ? `<strong>${entities.customer_name}</strong>` : '<span class="empty-val">None</span>';
  entityEmail.innerHTML = entities.email ? `<strong>${entities.email}</strong>` : '<span class="empty-val">None</span>';
  entityLang.textContent = lang.toUpperCase();
}

// =========================================================
// FAQ KNOWLEDGE BASE MODAL
// =========================================================
async function loadFaqs(query = '', category = 'All') {
  try {
    let url = `/api/faqs?q=${encodeURIComponent(query)}`;
    if (category && category !== 'All') {
      url += `&category=${encodeURIComponent(category)}`;
    }
    const res = await fetch(url);
    const data = await res.json();
    if (data.status === 'success') {
      state.faqs = data.faqs;
      renderFaqCategories(data.categories);
      renderFaqItems();
    }
  } catch (err) {
    console.error('Error loading FAQs:', err);
  }
}

function renderFaqCategories(categories) {
  faqCategoryPills.innerHTML = '';
  categories.forEach(cat => {
    const pill = document.createElement('button');
    pill.className = `cat-filter-pill ${cat === state.currentFaqCategory ? 'active' : ''}`;
    pill.textContent = cat;
    pill.addEventListener('click', () => {
      state.currentFaqCategory = cat;
      loadFaqs(faqSearchInput.value.trim(), cat);
    });
    faqCategoryPills.appendChild(pill);
  });
}

function renderFaqItems() {
  faqItemsList.innerHTML = '';
  if (state.faqs.length === 0) {
    faqItemsList.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-faint);">No matching FAQ articles found.</div>';
    return;
  }

  state.faqs.forEach(faq => {
    const card = document.createElement('div');
    card.className = 'faq-item-card';
    card.innerHTML = `
      <div class="faq-item-header">
        <span class="faq-item-question">${faq.question}</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
      <div class="faq-item-body" style="display: none;">
        <p>${faq.answer}</p>
        <button class="faq-ask-action-btn" data-question="${faq.question}">Ask in Chat</button>
      </div>
    `;

    const header = card.querySelector('.faq-item-header');
    const body = card.querySelector('.faq-item-body');
    header.addEventListener('click', () => {
      const isExpanded = body.style.display === 'block';
      body.style.display = isExpanded ? 'none' : 'block';
    });

    const askBtn = card.querySelector('.faq-ask-action-btn');
    askBtn.addEventListener('click', () => {
      faqModal.style.display = 'none';
      handleSendMessage(faq.question);
    });

    faqItemsList.appendChild(card);
  });
}

// =========================================================
// SUPPORT TICKETS MODAL & ESCALATION
// =========================================================
async function loadTickets() {
  try {
    const res = await fetch('/api/tickets');
    const data = await res.json();
    if (data.status === 'success') {
      state.tickets = data.tickets;
      ticketCountBadge.textContent = state.tickets.length;
      renderTicketsList();
    }
  } catch (err) {
    console.error('Error loading tickets:', err);
  }
}

function renderTicketsList() {
  ticketsContainer.innerHTML = '';
  if (state.tickets.length === 0) {
    ticketsContainer.innerHTML = '<div style="padding:14px;text-align:center;color:var(--text-faint);">No active support tickets.</div>';
    return;
  }

  state.tickets.forEach(t => {
    const card = document.createElement('div');
    card.className = 'ticket-item-card';
    card.innerHTML = `
      <div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
          <span class="ticket-id-tag">#${t.ticket_id}</span>
          <span class="ticket-priority-tag ${t.priority}">${t.priority}</span>
          <span style="font-size:0.75rem;color:var(--text-muted);">${t.category}</span>
        </div>
        <div style="font-size:0.82rem;font-weight:500;">${t.issue_summary}</div>
      </div>
      <div style="font-size:0.72rem;color:var(--accent-secondary);">${t.status}</div>
    `;
    ticketsContainer.appendChild(card);
  });
}

function openTicketModalWithContext() {
  ticketsModal.style.display = 'flex';
  const nameInput = document.getElementById('ticketCustomerName');
  const emailInput = document.getElementById('ticketEmail');
  const summaryInput = document.getElementById('ticketSummary');

  if (entityCustomerName.textContent !== 'None') {
    nameInput.value = entityCustomerName.textContent;
  }
  if (entityEmail.textContent !== 'None') {
    emailInput.value = emailInput.value || entityEmail.textContent;
  }
  summaryInput.value = `Assistance needed regarding current chat inquiry (Intent: ${inspectorIntentText.textContent})`;
}

// =========================================================
// SETTINGS MODAL & LLM ENGINE
// =========================================================
async function fetchSettings() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    if (data.status === 'success') {
      llmProviderSelect.value = data.provider;
      toggleApiKeyVisibility(data.provider);
      activeEngineText.textContent = `Engine: ${data.provider === 'local' ? 'Local NLP' : data.provider.toUpperCase()}`;
    }
  } catch (err) {
    console.error('Failed to load settings:', err);
  }
}

function toggleApiKeyVisibility(provider) {
  if (provider === 'local') {
    apiKeyGroup.style.display = 'none';
  } else {
    apiKeyGroup.style.display = 'flex';
  }
}

// =========================================================
// EVENT LISTENERS BINDING
// =========================================================
function initEventListeners() {
  // Chat Input Auto-Expand & Keyboard Submit
  chatInputField.addEventListener('input', () => {
    chatInputField.style.height = 'auto';
    chatInputField.style.height = `${Math.min(chatInputField.scrollHeight, 120)}px`;
  });

  chatInputField.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  sendMessageBtn.addEventListener('click', () => handleSendMessage());

  // Quick Action Pills
  document.querySelectorAll('.quick-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      handleSendMessage(pill.dataset.query);
    });
  });

  // Voice Input Toggle (STT)
  voiceInputBtn.addEventListener('click', () => {
    if (state.isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  stopVoiceBtn.addEventListener('click', () => stopRecording());

  // Auto TTS Toggle
  ttsAutoToggleBtn.addEventListener('click', () => {
    state.autoTts = !state.autoTts;
    ttsAutoToggleBtn.style.color = state.autoTts ? 'var(--accent-secondary)' : 'var(--text-muted)';
    showToast(state.autoTts ? 'Auto Read Aloud enabled' : 'Auto Read Aloud disabled');
  });

  // Theme Toggle
  themeToggleBtn.addEventListener('click', () => {
    const newTheme = state.theme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
  });

  // Language Selector
  languageSelector.addEventListener('change', (e) => {
    state.activeLanguage = e.target.value;
    if (state.recognition) {
      state.recognition.lang = LANG_LOCALES[state.activeLanguage] || 'en-US';
    }
    showToast(`Language set to ${languageSelector.options[languageSelector.selectedIndex].text}`);
  });

  // Sidebar Toggles
  mobileMenuBtn.addEventListener('click', () => {
    sidebarLeft.classList.toggle('open');
  });

  inspectorToggleBtn.addEventListener('click', () => {
    sidebarRight.classList.toggle('open');
  });

  closeInspectorBtn.addEventListener('click', () => {
    sidebarRight.classList.remove('open');
  });

  // New Chat & Export
  newChatBtn.addEventListener('click', () => startNewSession());

  exportChatBtn.addEventListener('click', async () => {
    try {
      const res = await fetch(`/api/sessions/${state.currentSessionId}/messages`);
      const data = await res.json();
      if (data.status === 'success') {
        const transcript = data.messages.map(m => `[${m.created_at}] ${m.sender.toUpperCase()}: ${m.content}`).join('\n\n');
        const blob = new Blob([transcript], { type: 'text/plain;charset=utf-8' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `nova-chat-transcript-${state.currentSessionId}.txt`;
        a.click();
        showToast('Transcript exported successfully.');
      }
    } catch (e) {
      showToast('Failed to export transcript.');
    }
  });

  // Escalation button in Inspector
  escalateTicketBtn.addEventListener('click', () => openTicketModalWithContext());

  // FAQ Modal Events
  openFaqModalBtn.addEventListener('click', () => {
    faqModal.style.display = 'flex';
    loadFaqs();
  });
  closeFaqModalBtn.addEventListener('click', () => faqModal.style.display = 'none');

  faqSearchInput.addEventListener('input', (e) => {
    loadFaqs(e.target.value.trim(), state.currentFaqCategory);
  });

  toggleAddFaqBtn.addEventListener('click', () => {
    const isShown = addFaqForm.style.display === 'flex';
    addFaqForm.style.display = isShown ? 'none' : 'flex';
  });

  saveFaqBtn.addEventListener('click', async () => {
    const category = document.getElementById('newFaqCategory').value.trim();
    const keywords = document.getElementById('newFaqKeywords').value.trim();
    const question = document.getElementById('newFaqQuestion').value.trim();
    const answer = document.getElementById('newFaqAnswer').value.trim();

    if (!question || !answer) {
      alert('Please fill out both question and answer.');
      return;
    }

    try {
      const res = await fetch('/api/faqs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, keywords, question, answer })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast('New FAQ added to knowledge base!');
        addFaqForm.style.display = 'none';
        document.getElementById('newFaqQuestion').value = '';
        document.getElementById('newFaqAnswer').value = '';
        loadFaqs();
      }
    } catch (e) {
      showToast('Error saving FAQ.');
    }
  });

  // Tickets Modal Events
  openTicketsModalBtn.addEventListener('click', () => {
    ticketsModal.style.display = 'flex';
    loadTickets();
  });
  closeTicketsModalBtn.addEventListener('click', () => ticketsModal.style.display = 'none');

  submitTicketBtn.addEventListener('click', async () => {
    const customer_name = document.getElementById('ticketCustomerName').value.trim();
    const email = document.getElementById('ticketEmail').value.trim();
    const category = document.getElementById('ticketCategory').value;
    const priority = document.getElementById('ticketPriority').value;
    const issue_summary = document.getElementById('ticketSummary').value.trim();

    if (!issue_summary) {
      alert('Please provide an issue summary.');
      return;
    }

    try {
      const res = await fetch('/api/tickets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: state.currentSessionId,
          customer_name,
          email,
          category,
          priority,
          issue_summary
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Ticket #${data.ticket_id} created!`);
        document.getElementById('ticketSummary').value = '';
        loadTickets();
        // Post confirmation into chat
        appendMessageRow('bot', `✅ **Support Ticket Created (${data.ticket_id})**\n\nYour priority support ticket has been escalated. An agent has received this issue and will follow up shortly.`);
        scrollToBottom();
      }
    } catch (e) {
      showToast('Failed to create ticket.');
    }
  });

  // Settings Modal Events
  openSettingsModalBtn.addEventListener('click', () => {
    settingsModal.style.display = 'flex';
    fetchSettings();
  });
  closeSettingsModalBtn.addEventListener('click', () => settingsModal.style.display = 'none');

  llmProviderSelect.addEventListener('change', (e) => {
    toggleApiKeyVisibility(e.target.value);
  });

  saveSettingsBtn.addEventListener('click', async () => {
    const provider = llmProviderSelect.value;
    const api_key = llmApiKeyInput.value.trim();

    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast('Settings saved successfully.');
        activeEngineText.textContent = `Engine: ${provider === 'local' ? 'Local NLP' : provider.toUpperCase()}`;
        settingsModal.style.display = 'none';
      }
    } catch (e) {
      showToast('Failed to update settings.');
    }
  });

  // Close modals clicking outside
  window.addEventListener('click', (e) => {
    if (e.target === faqModal) faqModal.style.display = 'none';
    if (e.target === ticketsModal) ticketsModal.style.display = 'none';
    if (e.target === settingsModal) settingsModal.style.display = 'none';
  });
}
