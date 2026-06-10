import React, { useState, useEffect, useRef } from 'react';
import { askAssistant, getAssistantHistory, clearAssistantHistory } from '../services/api';
import MathText from './MathText';

const STORAGE_KEY = 'educare_assistant_open';
const SUGGESTED_QUESTIONS = [
  'Help me solve 3x - 7 = 11',
  'Explain limits with an example',
  'What is integration?',
  'How do I solve age word problems?',
  'Find lim(x→2) (x²-4)/(x-2)',
  'Explain the derivative of x²',
];

const GREETING = `👋 Hi! I'm your EDUCARE Math Assistant.

I can help you with:
• Algebra (equations, functions, quadratics)
• Limits and continuity
• Derivatives and calculus
• Integration
• Word problems
• Exam preparation

Ask me any math question from your textbooks!

Examples:
• 'How do I solve 2x + 5 = 15?'
• 'Explain limits with an example'
• 'Help me with integration by parts'
• 'How do I solve age word problems?'

I can also answer basic greetings like 'hi' and 'how are you'!`;

function StudentAssistant({ studentId, fullName }) {
  const [isOpen, setIsOpen] = useState(() =>
    localStorage.getItem(STORAGE_KEY) === 'true'
  );
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const chatEndRef   = useRef(null);
  const inputRef     = useRef(null);
  const recognitionRef = useRef(null);

  // Open/close persistence
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(isOpen));
    if (isOpen && inputRef.current) inputRef.current.focus();
  }, [isOpen]);

  // Load conversation history
  useEffect(() => {
    if (!isOpen || !studentId || historyLoaded) return;
    getAssistantHistory(studentId)
      .then(data => {
        if (data.history && Array.isArray(data.history) && data.history.length > 0) {
          const paired = [];
          data.history.forEach(h => {
            paired.push({ role: 'user', content: h.user_message });
            if (h.ai_response) {
              paired.push({
                role: 'assistant',
                content: h.ai_response,
                source: h.source_citation || '',
              });
            }
          });
          setMessages(paired);
          setShowWelcome(false);
        }
      })
      .catch(() => {})
      .finally(() => setHistoryLoaded(true));
  }, [isOpen, studentId, historyLoaded]);

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking, showWelcome]);

  const handleSend = async () => {
    const q = input.trim();
    if (!q || !studentId || thinking) return;

    setShowWelcome(false);
    const userMsg = { role: 'user', content: q };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setThinking(true);

    try {
      const data = await askAssistant(q, studentId);
      const answer = data.answer || "I couldn't find a relevant answer. Try rephrasing your question.";
      setMessages(prev => [...prev, {
        role:    'assistant',
        content: answer,
        source:  data.source_citation || '',
        confidence: data.confidence || '',
        topic:   data.topic || '',
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role:    'assistant',
        content: "Sorry, something went wrong. Please try again.",
        source:  '',
      }]);
    } finally {
      setThinking(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = async () => {
    if (!studentId) return;
    try {
      await clearAssistantHistory(studentId);
    } catch {}
    setMessages([]);
    setShowWelcome(true);
  };

  const handleSuggestion = (prompt) => {
    setInput(prompt);
    inputRef.current?.focus();
  };

  // ── Web Speech API ──────────────────────────────────────────────────────
  const toggleRecording = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('Speech recognition not supported. Try Chrome.'); return; }
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
      return;
    }
    const recog = new SR();
    recog.lang = 'en-US';
    recog.interimResults = false;
    recog.maxAlternatives = 1;
    recog.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(r => r[0].transcript).join('');
      setInput(prev => prev + (prev ? ' ' : '') + transcript);
      setIsRecording(false);
    };
    recog.onerror = () => setIsRecording(false);
    recog.onend    = () => setIsRecording(false);
    recog.start();
    recognitionRef.current = recog;
    setIsRecording(true);
  };

  const openAssistant = () => { setIsOpen(true); };

  // ── Helpers ─────────────────────────────────────────────────────────────
  const isMathContent = (role) => role !== 'user';

  return (
    <>
      <style>{`
        .assistant-scrollbar::-webkit-scrollbar { width: 4px; }
        .assistant-scrollbar::-webkit-scrollbar-thumb { background: #c1d3e5; border-radius: 4px; }
        .chat-source-tag { display:block; font-size:10px; color:#6b7280; margin-top:4px;
                           font-style:italic; border-top:1px solid #e5e7eb; padding-top:2px; }
        .chat-bubble-user { background:#2563eb; color:white; border-bottom-right-radius:6px; }
        .chat-bubble-bot  { background:#f3f4f6; color:#1f2937; border-bottom-left-radius:6px; }
        .typing-dot { width:7px;height:7px;border-radius:50%;background:#9ca3af;
                      animation:dotBounce 1.2s infinite ease-in-out; }
        .typing-dot:nth-child(2){animation-delay:0.15s}
        .typing-dot:nth-child(3){animation-delay:0.3s}
        @keyframes dotBounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-6px)} }
        .suggested-btn { font-size:11px; padding:4px 10px; border-radius:9999px;
                         background:#eff6ff; border:1px solid #bfdbfe; color:#1d4ed8;
                         cursor:pointer; transition:all 0.15s; white-space:nowrap; }
        .suggested-btn:hover { background:#dbeafe; }
      `}</style>

      {/* ── Floating Chat Bubble ── */}
      {!isOpen && (
        <button
          onClick={openAssistant}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-2xl flex items-center justify-center group transition-transform hover:scale-110"
          style={{ backgroundColor: '#2563eb' }}
          title="AI Math Assistant"
        >
          <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span className="absolute -top-8 right-0 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition pointer-events-none">
            AI Math Assistant
          </span>
        </button>
      )}

      {/* ── Chat Window ── */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col shadow-2xl rounded-2xl overflow-hidden"
             style={{ width: '420px', maxHeight: '80vh', height: '600px', backgroundColor: '#fff' }}>

          {/* Header */}
          <div className="px-5 py-3 flex items-center justify-between shadow-md" style={{ backgroundColor: '#2563eb' }}>
            <div className="flex items-center gap-2">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span className="text-white font-semibold text-sm">AI Math Assistant</span>
              <span className="bg-white/20 text-white text-[10px] px-1.5 py-0.5 rounded-full ml-1">Beta</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={handleClearChat}
                title="Clear chat"
                className="p-1.5 text-white/70 hover:text-white hover:bg-white/10 rounded-md transition"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-white/70 hover:text-white hover:bg-white/10 rounded-md transition"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto assistant-scrollbar px-4 py-3 space-y-3"
               style={{ backgroundColor: '#f9fafb', minHeight: '300px' }}>

            {/* ── Welcome screen (before first message) ── */}
            {showWelcome && messages.length === 0 && (
              <div className="text-center px-2 py-6">
                <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-blue-50 flex items-center justify-center">
                  <svg className="w-7 h-7 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <p className="text-xs text-gray-400 mb-4">I search all 6 textbooks to give you the best answer.</p>
                <div className="flex flex-wrap gap-1.5 justify-center">
                  {SUGGESTED_QUESTIONS.map(p => (
                    <button
                      key={p}
                      onClick={() => handleSuggestion(p)}
                      className="suggested-btn"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* ── Message list ── */}
            {messages.map((msg, i) => {
              const isUser = msg.role === 'user';
              const content = msg.content || '';
              const lines = content.split('\n');
              return (
                <div key={i} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[88%] px-3.5 py-2.5 rounded-2xl text-[13px] leading-relaxed whitespace-pre-wrap ${
                      isUser ? 'chat-bubble-user rounded-br-md' : 'chat-bubble-bot rounded-bl-md'
                    }`}
                  >
                    {isUser ? (
                      <p>{content}</p>
                    ) : (
                      <MathText text={content} />
                    )}
                    {!isUser && (msg.confidence === 'high' || msg.source || msg.topic) && (
                      <div className="chat-source-tag">
                        {msg.topic             && <span className="font-semibold text-blue-600">{msg.topic}</span>}
                        {msg.topic && msg.source && <span> · </span>}
                        {msg.source            && <span>{msg.source}</span>}
                        {msg.confidence === 'high' && (!msg.source) && (
                          <span className="text-green-600">(High confidence)</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* ── Typing indicator ── */}
            {thinking && (
              <div className="flex justify-start">
                <div className="bg-white px-4 py-3 rounded-2xl rounded-bl-md shadow-sm border border-gray-100 flex items-end gap-1.5">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* ── Input Area ── */}
          <div className="bg-white border-t border-gray-200 px-3 py-2.5 rounded-b-2xl">
            {/* Suggested pills (only when chat is empty or just started) */}
            {messages.length === 0 && !showWelcome && (
              <div className="flex gap-1.5 overflow-x-auto pb-2">
                {SUGGESTED_QUESTIONS.map(p => (
                  <button key={p} onClick={() => handleSuggestion(p)} className="suggested-btn flex-shrink-0">
                    {p}
                  </button>
                ))}
              </div>
            )}

            <div className="flex items-center gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  rows={1}
                  value={input}
                  onChange={e => {
                    setInput(e.target.value);
                    // Auto-grow
                    e.target.style.height = 'auto';
                    e.target.style.height = Math.min(e.target.scrollHeight, 80) + 'px';
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask me a math question or say hi..."
                  className="w-full px-3 py-2 text-[13px] rounded-xl border border-gray-300
                             focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                             resize-none transition text-gray-800"
                  style={{ minHeight: '36px', maxHeight: '80px' }}
                />
              </div>

              {/* Voice input */}
              <button
                onClick={toggleRecording}
                title={isRecording ? 'Stop voice input' : 'Start voice input'}
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition ${
                  isRecording
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                }`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </button>

              {/* Send */}
              <button
                onClick={handleSend}
                disabled={!input.trim() || thinking}
                className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition hover:opacity-90 disabled:opacity-40"
                style={{ backgroundColor: '#2563eb' }}
                title="Send"
              >
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default StudentAssistant;
