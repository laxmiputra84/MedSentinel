'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/authContext';
import api from '@/lib/api';

interface SourceCitation {
  dataset_id?: number;
  document_id?: number;
  title: string;
  confidence: number;
  hospital_id?: number;
}

interface Message {
  id?: number | string;
  sender: 'user' | 'assistant';
  content: string;
  tools_used?: string[] | string;
  sources?: SourceCitation[];
  found_in_private_data?: boolean;
  suggested_actions?: Array<{
    label: string;
    action: string;
    url?: string;
    appointment_id?: number;
  }>;
  created_at?: string;
}

interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  message_count: number;
}

export const AIAssistantModal: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  // Chat Modes: strict_private or internal_assistant
  const [chatMode, setChatMode] = useState<'strict_private' | 'internal_assistant'>('strict_private');

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [showHistoryDropdown, setShowHistoryDropdown] = useState(false);
  const [errorMessage, setErrorMessage] = useState<{ code?: string; message: string } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedQuestions = [
    'Find cardiology hospitals in Bengaluru with ICU availability',
    'Why is my claim under review?',
    'What government schemes can cover tertiary surgeries?',
    'Show my upcoming doctor consultations',
    'What documents are pending verification in my medical vault?',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const fetchConversations = async () => {
    if (!isAuthenticated) return;
    try {
      const res = await api.get<ConversationSummary[]>('/ai/conversations');
      setConversations(res.data || []);
    } catch (err) {
      console.error('Error fetching AI conversations:', err);
    }
  };

  useEffect(() => {
    if (isOpen && isAuthenticated) {
      fetchConversations();
    }
  }, [isOpen, isAuthenticated]);

  const loadConversation = async (id: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.get(`/ai/conversations/${id}`);
      const history = res.data.map((m: any) => ({
        id: m.id,
        sender: m.sender,
        content: m.content,
        tools_used: m.tools_used ? JSON.parse(m.tools_used) : [],
        created_at: m.created_at,
      }));
      setMessages(history);
      setConversationId(id);
      setShowHistoryDropdown(false);
    } catch (err: any) {
      setErrorMessage({
        code: 'CONVERSATION_LOAD_ERROR',
        message: err.response?.data?.detail || 'Failed to load conversation history.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartNewChat = () => {
    setConversationId(null);
    setMessages([]);
    setShowHistoryDropdown(false);
    setErrorMessage(null);
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/ai/conversations/${id}`);
      setConversations(conversations.filter((c) => c.id !== id));
      if (conversationId === id) {
        handleStartNewChat();
      }
    } catch (err) {
      console.error('Error deleting conversation:', err);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text || !text.trim() || isLoading) return;

    if (!isAuthenticated) {
      router.push('/login?redirect=/');
      return;
    }

    const userMsg: Message = {
      id: Date.now(),
      sender: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.post(
        chatMode === 'strict_private' ? '/ai/private-chat' : '/ai/chat',
        {
          message: text,
          conversation_id: conversationId || undefined,
          mode: chatMode,
        }
      );

      const assistantMsg: Message = {
        id: Date.now() + 1,
        sender: 'assistant',
        content: res.data.response,
        tools_used: res.data.tools_used || [],
        sources: res.data.sources || [],
        found_in_private_data: res.data.found_in_private_data !== false,
        suggested_actions: res.data.suggested_actions || [],
        created_at: new Date().toISOString(),
      };

      setConversationId(res.data.conversation_id);
      setMessages((prev) => [...prev, assistantMsg]);
      fetchConversations();
    } catch (err: any) {
      const errDetail = err.response?.data?.detail;
      if (typeof errDetail === 'object' && errDetail !== null) {
        setErrorMessage({
          code: errDetail.code || 'AI_ERROR',
          message: errDetail.message || 'An unexpected error occurred.',
        });
      } else if (typeof errDetail === 'string') {
        setErrorMessage({ code: 'AI_ERROR', message: errDetail });
      } else {
        setErrorMessage({
          code: 'NETWORK_ERROR',
          message: 'Unable to connect to the MedSentinel Private Knowledge Service. Please check backend status.',
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionClick = (actionObj: { label: string; action: string; url?: string }) => {
    if (actionObj.url) {
      setIsOpen(false);
      router.push(actionObj.url);
    }
  };

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce hover:animate-none">
          <button
            onClick={() => setIsOpen(true)}
            className="group relative flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 text-white rounded-full shadow-2xl hover:shadow-purple-500/30 hover:scale-105 transition-all duration-300 border border-white/20"
          >
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm group-hover:rotate-12 transition-transform">
              <span className="material-symbols-outlined text-xl">neurology</span>
            </div>
            <div className="text-left hidden sm:block pr-1">
              <div className="text-xs font-extrabold tracking-wide flex items-center gap-1.5">
                <span>Private Clinical AI</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              </div>
              <div className="text-[10px] text-purple-200">Verified Enterprise RAG</div>
            </div>
          </button>
        </div>
      )}

      {/* Main AI Chat Drawer */}
      {isOpen && (
        <div
          className={`fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50 w-[calc(100vw-2rem)] sm:w-[460px] ${
            isMinimized ? 'h-14' : 'h-[640px] max-h-[88vh]'
          } bg-gray-950/95 backdrop-blur-2xl border border-purple-500/30 rounded-3xl shadow-2xl flex flex-col justify-between overflow-hidden transition-all duration-300 animate-in fade-in zoom-in-95`}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-900/40 via-purple-900/40 to-black p-3.5 border-b border-white/10 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow">
                <span className="material-symbols-outlined text-white text-lg">neurology</span>
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <h3 className="text-xs font-bold text-white font-['Manrope']">MedSentinel Private AI</h3>
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-extrabold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Private RAG
                  </span>
                </div>
                <p className="text-[10px] text-gray-400">Zero Hallucination Enterprise Intelligence</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {isAuthenticated && (
                <div className="relative">
                  <button
                    onClick={() => setShowHistoryDropdown(!showHistoryDropdown)}
                    title="Chat History"
                    className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10"
                  >
                    <span className="material-symbols-outlined text-base">forum</span>
                  </button>

                  {showHistoryDropdown && (
                    <div className="absolute right-0 mt-2 w-64 bg-gray-900 border border-white/15 rounded-2xl shadow-2xl p-3 z-50 space-y-2 text-xs">
                      <div className="flex items-center justify-between pb-1 border-b border-white/10">
                        <span className="font-bold text-white text-[11px]">Chat History</span>
                        <button
                          onClick={handleStartNewChat}
                          className="text-blue-400 hover:underline text-[10px] font-semibold flex items-center gap-0.5"
                        >
                          <span className="material-symbols-outlined text-xs">add</span>
                          <span>New Session</span>
                        </button>
                      </div>

                      <div className="max-h-48 overflow-y-auto space-y-1">
                        {conversations.length === 0 ? (
                          <div className="text-center py-4 text-gray-500 text-[11px]">No past sessions.</div>
                        ) : (
                          conversations.map((c) => (
                            <div
                              key={c.id}
                              onClick={() => loadConversation(c.id)}
                              className={`p-2 rounded-xl border flex items-center justify-between gap-2 cursor-pointer transition-all ${
                                conversationId === c.id
                                  ? 'bg-purple-900/30 border-purple-500/40 text-white'
                                  : 'bg-white/5 border-white/5 text-gray-300 hover:bg-white/10'
                              }`}
                            >
                              <span className="truncate text-[11px] font-medium">{c.title || 'Consultation'}</span>
                              <button
                                onClick={(e) => handleDeleteConversation(c.id, e)}
                                className="text-gray-500 hover:text-red-400 p-0.5"
                              >
                                <span className="material-symbols-outlined text-xs">delete</span>
                              </button>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <button
                onClick={handleStartNewChat}
                title="New Chat"
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10"
              >
                <span className="material-symbols-outlined text-base">restart_alt</span>
              </button>

              <button
                onClick={() => setIsMinimized(!isMinimized)}
                title={isMinimized ? 'Expand' : 'Minimize'}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10"
              >
                <span className="material-symbols-outlined text-base">
                  {isMinimized ? 'unfold_more' : 'minimize'}
                </span>
              </button>

              <button
                onClick={() => setIsOpen(false)}
                title="Close"
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10"
              >
                <span className="material-symbols-outlined text-base">close</span>
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Mode Switcher Banner */}
              <div className="bg-black/60 border-b border-white/10 px-3 py-1.5 flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-1.5 text-gray-400">
                  <span className="material-symbols-outlined text-xs text-purple-400">tune</span>
                  <span>Mode:</span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setChatMode('strict_private')}
                    className={`px-2 py-0.5 rounded-md font-bold text-[10px] transition-all ${
                      chatMode === 'strict_private'
                        ? 'bg-purple-600 text-white shadow'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Strict Private (RAG Only)
                  </button>
                  <button
                    onClick={() => setChatMode('internal_assistant')}
                    className={`px-2 py-0.5 rounded-md font-bold text-[10px] transition-all ${
                      chatMode === 'internal_assistant'
                        ? 'bg-blue-600 text-white shadow'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Clinical Co-Pilot (+ Tools)
                  </button>
                </div>
              </div>

              {/* Chat Message Scrollport */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
                {messages.length === 0 && (
                  <div className="space-y-4">
                    <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 border border-purple-500/20 rounded-2xl p-4 text-center space-y-2">
                      <div className="w-10 h-10 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center mx-auto">
                        <span className="material-symbols-outlined text-xl">shield_lock</span>
                      </div>
                      <h4 className="font-bold text-white text-xs">MedSentinel Private Knowledge Vault</h4>
                      <p className="text-[11px] text-gray-300 leading-relaxed">
                        This AI answers strictly using verified MedSentinel datasets, empanelled hospital registries, policy rules, and your authorized medical records.
                      </p>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider block mb-2">
                        Suggested Private Inquiries
                      </span>
                      <div className="space-y-1.5">
                        {suggestedQuestions.map((q) => (
                          <button
                            key={q}
                            onClick={() => handleSendMessage(q)}
                            className="w-full text-left p-2.5 rounded-xl bg-white/5 hover:bg-purple-600/20 border border-white/10 hover:border-purple-500/40 text-gray-300 hover:text-white transition-all text-xs flex items-center justify-between group"
                          >
                            <span className="line-clamp-1">{q}</span>
                            <span className="material-symbols-outlined text-xs text-gray-500 group-hover:text-purple-400">
                              arrow_forward
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Message Thread */}
                {messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-[90%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                        m.sender === 'user'
                          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-br-none shadow-md'
                          : 'bg-gray-900/90 border border-white/10 text-gray-200 rounded-bl-none shadow'
                      }`}
                    >
                      {/* Verified Internal Data Badge */}
                      {m.sender === 'assistant' && (
                        <div className="flex items-center justify-between gap-2 mb-2 pb-1.5 border-b border-white/10">
                          <span className="text-[9px] font-extrabold uppercase text-emerald-400 flex items-center gap-1">
                            <span className="material-symbols-outlined text-[12px]">verified</span>
                            <span>{m.found_in_private_data ? 'Verified Internal Knowledge' : 'Knowledge Search Result'}</span>
                          </span>
                        </div>
                      )}

                      <div className="whitespace-pre-line font-normal">{m.content}</div>

                      {/* Source Citations Section */}
                      {m.sources && m.sources.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-white/10 space-y-1">
                          <span className="text-[9px] font-extrabold uppercase text-purple-400 flex items-center gap-1">
                            <span className="material-symbols-outlined text-[11px]">source</span>
                            <span>Knowledge Citations:</span>
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {m.sources.map((s, sIdx) => (
                              <span
                                key={sIdx}
                                className="px-2 py-0.5 rounded bg-purple-900/40 text-purple-300 text-[9px] font-medium border border-purple-500/30 truncate max-w-[220px]"
                                title={`Document #${s.document_id} (${Math.round(s.confidence * 100)}% match)`}
                              >
                                {s.title} ({Math.round(s.confidence * 100)}%)
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      {m.suggested_actions && m.suggested_actions.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-white/10 flex flex-wrap gap-1.5">
                          {m.suggested_actions.map((act, actIdx) => (
                            <button
                              key={actIdx}
                              onClick={() => handleActionClick(act)}
                              className="px-2.5 py-1 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 border border-blue-400/40 text-blue-300 text-[10px] font-bold transition-all flex items-center gap-1"
                            >
                              <span>{act.label}</span>
                              <span className="material-symbols-outlined text-[10px]">open_in_new</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                    <span className="text-[9px] text-gray-500 mt-1 px-1">
                      {m.sender === 'user' ? 'You' : 'MedSentinel Verified AI'}
                    </span>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex items-center gap-2 text-xs text-gray-400 bg-gray-900/60 p-3 rounded-2xl border border-white/10 w-fit">
                    <span className="material-symbols-outlined text-sm text-purple-400 animate-spin">
                      progress_activity
                    </span>
                    <span>Retrieving authorized private datasets & verifying citations...</span>
                  </div>
                )}

                {/* Accurate Error Banner */}
                {errorMessage && (
                  <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-300 space-y-1">
                    <div className="flex items-center justify-between font-bold">
                      <div className="flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-sm text-red-400">error</span>
                        <span>{errorMessage.code || 'System Notification'}</span>
                      </div>
                      <button onClick={() => setErrorMessage(null)} className="text-gray-400 hover:text-white">
                        <span className="material-symbols-outlined text-xs">close</span>
                      </button>
                    </div>
                    <p className="text-[11px] text-gray-300">{errorMessage.message}</p>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Bar */}
              <div className="p-3 border-t border-white/10 bg-black/40 flex-shrink-0">
                {!isAuthenticated ? (
                  <div className="text-center py-2">
                    <Link href="/login" className="text-xs text-purple-400 font-bold hover:underline">
                      Sign In to Access Authorized Private Knowledge Base →
                    </Link>
                  </div>
                ) : (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendMessage();
                    }}
                    className="flex items-center gap-2"
                  >
                    <input
                      type="text"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      placeholder={
                        chatMode === 'strict_private'
                          ? 'Query private datasets, hospital records, and schemes...'
                          : 'Ask clinical assistant with claims and appointments...'
                      }
                      className="flex-1 bg-gray-900 border border-white/15 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                    />
                    <button
                      type="submit"
                      disabled={!inputMessage.trim() || isLoading}
                      className="p-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg hover:shadow-purple-500/20 disabled:opacity-30 disabled:pointer-events-none transition-all"
                    >
                      <span className="material-symbols-outlined text-base">send</span>
                    </button>
                  </form>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
};
