import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Send,
  Bot,
  User,
  Compass,
  ArrowRight,
  BookOpen,
  Calendar,
  Layers,
  MapPin,
  RefreshCw,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useTrip } from '../context/TripContext';
import aiService from '../services/aiService';
import LoadingSpinner from '../components/LoadingSpinner';

const SUGGESTED_PROMPTS = [
  'Plan a relaxed 2-day trip to Hyderabad with budget ₹5000',
  'Tell me about the acoustic clapping trick at Golconda Fort',
  'What are the most famous Hyderabadi Biryani places and food history?',
  'What is the history of Chowmahalla Palace Belgian chandeliers?',
  'How do I navigate Bengaluru peak traffic using Namma Metro?',
];

export default function AssistantPage() {
  const navigate = useNavigate();
  const { setCurrentItinerary, updatePlan, tripPlan } = useTrip();

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hello! I am your **TravelSenseAI Assistant** powered by LangGraph and ChromaDB RAG. I can help you plan multi-day itineraries, explain historical monuments, check live weather, and estimate travel budgets. How can I help with your journey today?",
      retrieved_sources: [],
      workflow_trace: ['Node 1: understand_request_node', 'Node 8: generate_explanation_node'],
    },
  ]);

  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showTrace, setShowTrace] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || loading) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text.trim(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await aiService.chatWithAssistant({
        message: text.trim(),
        conversationHistory: messages.slice(-6), // Send last 6 messages as context
        destinationHint: tripPlan.destination,
      });

      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.reply,
        retrieved_sources: response.retrieved_sources || [],
        itinerary: response.itinerary || null,
        extracted_preferences: response.extracted_preferences || null,
        workflow_trace: response.workflow_trace || [],
      };

      // If the AI assistant generated an itinerary, update trip context
      if (response.itinerary) {
        setCurrentItinerary(response.itinerary);
      }
      if (response.extracted_preferences?.destination) {
        updatePlan({ destination: response.extracted_preferences.destination });
      }

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `I apologize, but I encountered an error communicating with the AI service: ${err.message || 'Please try again.'}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#DCE6E3] pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#18B8A6] animate-pulse" />
            <h1 className="text-xl sm:text-2xl font-extrabold text-[#163B46] tracking-tight">
              AI Travel Assistant & RAG
            </h1>
            <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#18B8A6]/10 text-[#129889] border border-[#18B8A6]/20 font-bold uppercase">
              LangGraph 8-Node
            </span>
          </div>
          <p className="text-xs sm:text-sm text-[#52636A] mt-1">
            Grounded in curated cultural archives without hallucinating deterministic facts.
          </p>
        </div>

        <button
          onClick={() => setShowTrace(!showTrace)}
          className="text-xs text-[#52636A] hover:text-[#18B8A6] flex items-center space-x-1.5 self-start sm:self-auto font-medium transition-colors"
        >
          <Layers className="w-3.5 h-3.5 text-[#18B8A6]" />
          <span>{showTrace ? 'Hide Workflow Traces' : 'Show Workflow Traces'}</span>
        </button>
      </div>

      {/* Suggested Prompts Carousel */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-none text-xs">
        <span className="text-[#829196] text-[11px] font-semibold flex-shrink-0 flex items-center">
          <Sparkles className="w-3.5 h-3.5 mr-1 text-[#18B8A6]" /> Suggestions:
        </span>
        {SUGGESTED_PROMPTS.map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSendMessage(prompt)}
            className="flex-shrink-0 px-3.5 py-1.5 rounded-full bg-white border border-[#DCE6E3] hover:border-[#18B8A6] text-[#26383D] hover:text-[#18B8A6] text-xs font-medium transition-all shadow-xs"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div className="p-6 rounded-3xl bg-white border border-[#DCE6E3] shadow-soft min-h-[520px] max-h-[640px] overflow-y-auto space-y-6">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3.5 ${
                isUser ? 'flex-row-reverse space-x-reverse' : ''
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm ${
                  isUser
                    ? 'bg-[#163B46] text-white font-bold'
                    : 'bg-[#EEF3F1] text-[#18B8A6] border border-[#DCE6E3]'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-5 h-5" />}
              </div>

              {/* Message Bubble */}
              <div className={`space-y-3 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
                <div
                  className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed shadow-sm ${
                    isUser
                      ? 'bg-[#163B46] text-white rounded-tr-none'
                      : 'bg-[#F4F7F6] text-[#26383D] border border-[#DCE6E3] rounded-tl-none whitespace-pre-wrap'
                  }`}
                >
                  {msg.content}
                </div>

                {/* Optional Itinerary Action Banner */}
                {msg.itinerary && (
                  <div className="p-4 rounded-2xl bg-teal-50/70 border border-[#18B8A6]/30 flex items-center justify-between gap-4 text-xs shadow-xs">
                    <div>
                      <h4 className="font-bold text-[#163B46] flex items-center space-x-1.5">
                        <Calendar className="w-4 h-4 text-[#18B8A6]" />
                        <span>{msg.itinerary.total_days}-Day Itinerary Generated</span>
                      </h4>
                      <p className="text-[11px] text-[#52636A] mt-0.5">
                        Total Distance: {msg.itinerary.total_distance_km} km • Status:{' '}
                        <strong className="text-[#16A36A]">{msg.itinerary.feasibility_status}</strong>
                      </p>
                    </div>

                    <button
                      onClick={() => navigate('/itinerary')}
                      className="px-4 py-2 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold text-xs flex items-center space-x-1 shadow-soft transition-colors"
                    >
                      <span>View Schedule</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* Retrieved RAG Sources Citation Pill */}
                {msg.retrieved_sources && msg.retrieved_sources.length > 0 && (
                  <div className="p-3 rounded-xl bg-[#EEF3F1] border border-[#DCE6E3] text-[11px] text-[#52636A] space-y-1.5">
                    <span className="font-semibold text-[#163B46] flex items-center">
                      <BookOpen className="w-3.5 h-3.5 mr-1 text-[#18B8A6]" />
                      Verified Knowledge Base Sources:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.retrieved_sources.map((s, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-0.5 rounded bg-white border border-[#DCE6E3] text-[#26383D] font-medium"
                        >
                          {s.title} ({s.source})
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Workflow Trace Accordion */}
                {showTrace && msg.workflow_trace && msg.workflow_trace.length > 0 && (
                  <div className="p-3 rounded-xl bg-[#F4F7F6] border border-[#DCE6E3] text-[10px] font-mono text-[#52636A] space-y-1">
                    <span className="font-bold text-[#163B46]">LangGraph Execution Trace:</span>
                    <ol className="list-decimal list-inside space-y-0.5">
                      {msg.workflow_trace.map((step, idx) => (
                        <li key={idx} className="text-[#129889]">{step}</li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center space-x-3 text-[#52636A]">
            <div className="w-9 h-9 rounded-xl bg-[#EEF3F1] border border-[#DCE6E3] flex items-center justify-center text-[#18B8A6]">
              <Bot className="w-5 h-5 animate-pulse" />
            </div>
            <div className="p-3.5 rounded-2xl bg-[#F4F7F6] border border-[#DCE6E3] text-xs text-[#26383D] flex items-center space-x-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#18B8A6]" />
              <span>LangGraph agent orchestrating retrieval & response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Field */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="relative flex items-center bg-white border border-[#DCE6E3] focus-within:border-[#18B8A6] focus-within:ring-2 focus-within:ring-[#18B8A6]/20 rounded-2xl p-2 shadow-soft transition-all"
      >
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask a travel question or request a multi-day trip plan..."
          className="w-full bg-transparent border-none text-xs sm:text-sm text-[#26383D] px-4 py-2 focus:outline-none placeholder-[#829196]"
        />
        <button
          type="submit"
          disabled={loading || !inputMessage.trim()}
          className="p-2.5 rounded-xl bg-[#18B8A6] hover:bg-[#129889] text-white font-bold transition-all shadow-soft disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
