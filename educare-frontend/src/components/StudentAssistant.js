import React, { useState, useEffect, useRef } from 'react';
import { askAssistant, getAssistantHistory } from '../services/api';

const STORAGE_KEY = 'educare_assistant_open';

function StudentAssistant({ studentId, fullName }) {
  const [isOpen, setIsOpen]          = useState(() =>
    localStorage.getItem(STORAGE_KEY) === 'true'
  );
  const [messages, setMessages]     = useState([]);
  const [input, setInput]           = useState('');
  const [thinking, setThinking]     = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [isRecording, setIsRecording]     = useState(false);
  const chatEndRef  = useRef(null);
  const inputRef    = useRef(null);
  const recognitionRef = useRef(null);

  // Open/close persistence
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(isOpen));
  }, [isOpen]);

  // Load conversation history
  useEffect(() => {
    if (!isOpen || !studentId || historyLoaded) return;
    getAssistantHistory(studentId)
      .then(data => {
        if (data.history && Array.isArray(data.history)) {
          setMessages(
            data.history.map(h => ({
              role:    'user',
              content: h.user_message,
              source:  h.source_citation,
            }))
          );
        }
      })
      .catch(() => {})
      .finally(() => setHistoryLoaded(true));
  }, [isOpen, studentId, historyLoaded]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, thinking]);

  // Auto-focus input on open
  useEffect(() => {
    if (isOpen && inputRef.current) inputRef.current.focus();
  }, [isOpen]);

  const handleSend = async () => {
    const q = input.trim();
    if (!q || !studentId) return;

    const userMsg = { role: 'user', content: q };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setThinking(true);

    try {
      const data = await askAssistant(q, studentId);
      setMessages(prev => [...prev, {
        role:    'assistant',
        content: data.answer || "I couldn't find a relevant answer in the curriculum. Try rephrasing your question.",
        source:  data.source_citation,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role:    'assistant',
        content: "Sorry, something went wrong. Please try again.",
        source:  '',
      }]);
    } finally {
      setThinking(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Web Speech API ──────────────────────────────────────────────
  const toggleRecording = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      alert('Speech recognition is not supported in this browser. Try Chrome.');
      return;
    }

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
        .map(r => r[0].transcript)
        .join('');
      setInput(prev => prev + (prev ? ' ' : '') + transcript);
      setIsRecording(false);
    };

    recog.onerror = () => {
      setIsRecording(false);
    };

    recog.onend = () => {
      setIsRecording(false);
    };

    recog.start();
    recognitionRef.current = recog;
    setIsRecording(true);
  };

  // ── Quick prompts ───────────────────────────────────────────────
  const quickPrompts = [
    'Explain limits with an example',
    'How do I solve quadratic equations?',
    'What is the formula for integration by parts?',
    'What topics do I need before integration?',
  ];

  const openNow = () => {
    setIsOpen(true);
    if (!isOpen) localStorage.setItem(STORAGE_KEY, 'true');
  };

  return (
    <>
      {/* Queries to hide scrollbar temporarily */}
      <style>{`
        .assistant-scrollbar::-webkit-scrollbar { width: 4px; }
        .assistant-scrollbar::-webkit-scrollbar-thumb { background: #c1d3e5; border-radius: 2px; }
      `}</style>

      {/* Floating chat bubble */}
      {!isOpen && (
        <button
          onClick={openNow}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-2xl flex items-center justify-center group"
          style={{ backgroundColor: '#2563eb' }}
          title="AI Learning Assistant"
        >
          <svg className="w-7 h-7 text-white group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
          <span className="absolute -top-8 right-0 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition">
            AI Learning Assistant
          </span>
        </button>
      )}

      {isOpen && (
        /* Chat Window */
        <div className="fixed bottom-6 right-6 z-50 flex flex-col"
             style={{ width: '400px', height: '560px', maxHeight: '80vh' }}>
          {/* Header */}
          <div className="rounded-t-2xl px-5 py-3 flex items-center justify-between shadow-lg"
               style={{ backgroundColor: '#2563eb' }}>
            <div className="flex items-center gap-2">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              <span className="text-white font-semibold">AI Learning Assistant</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200 transition p-1"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 bg-white overflow-y-auto assistant-scrollbar border-x border-gray-200 p-4 space-y-3"
               style={{ minHeight: '340px' }}>
            {messages.length === 0 && (
              <div className="text-center text-gray-500 text-sm mt-6">
                <div className="w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center"
                     style={{ backgroundColor: '#eef2ff' }}>
                  <svg className="w-6 h-6" style={{ color: '#2563eb' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <p className="font-medium text-gray-700 mb-1">Ask me anything!</p>
                <p className="text-xs text-gray-400 mb-3">I search your curriculum to give the best answer.</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {quickPrompts.map(p => (
                    <button
                      key={p}
                      onClick={() => { setInput(p); if (inputRef.current) inputRef.current.focus(); }}
                      className="text-xs px-2 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100 transition"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm ${
                    msg.role === 'user'
                      ? 'rounded-br-md'
                      : 'rounded-bl-md'
                  }`}
                  style={{
                    backgroundColor: msg.role === 'user' ? '#2563eb' : '#f3f4f6',
                    color: msg.role === 'user' ? 'white' : '#1f2937',
                  }}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  {msg.source && (
                    <p className="text-[10px] mt-1.5 italic"
                       style={{ color: msg.role === 'user' ? '#bfdbfe' : '#9ca3af' }}>
                      Source: {msg.source}
                    </p>
                  )}
                </div>
              </div>
            ))}

            {thinking && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-md">
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div className="bg-gray-50 border-t border-gray-200 px-3 py-3 rounded-b-2xl">
            <div className="flex items-end gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  rows={2}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a maths question..."
                  className="w-full px-3 py-2 text-sm rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  style={{ minHeight: '38px', maxHeight: '80px' }}
                />
              </div>
              <button
                onClick={toggleRecording}
                title={isRecording ? 'Stop voice input' : 'Start voice input'}
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition ${
                  isRecording ? 'bg-red-500 text-white animate-pulse' : 'text-gray-400 hover:text-gray-600'
                }`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </button>
              <button
                onClick={handleSend}
                disabled={!input.trim() || thinking}
                className="w-9 h-9 rounded-full flex items-center justify-center text-white flex-shrink-0 transition hover:opacity-90 disabled:opacity-40"
                style={{ backgroundColor: '#2563eb' }}
                title="Send"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
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
