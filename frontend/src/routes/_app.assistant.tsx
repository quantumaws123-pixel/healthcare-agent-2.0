/**
 * /assistant — AI Health Assistant
 * Answers patient and doctor questions grounded in real Digital Twin data.
 */
import React, { useState, useRef, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, Loader2, User, Lightbulb, TrendingUp, Heart, Pill, Activity, Sparkles, ChevronDown, X } from "lucide-react";
import { useAuthContext } from "@/context/AuthContext";
import { askAssistant, type AssistantMessage, type AssistantResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/assistant")({ component: AssistantPage });

// ── Suggested questions by role ───────────────────────────────────────────

const PATIENT_SUGGESTIONS = [
  { icon: Heart,      text: "Why is my risk high?",                 color: "text-red-500" },
  { icon: TrendingUp, text: "Why did my recovery score decrease?",  color: "text-blue-500" },
  { icon: Pill,       text: "Did I miss medication?",               color: "text-amber-500" },
  { icon: Activity,   text: "What should I improve today?",         color: "text-green-500" },
  { icon: Lightbulb,  text: "Summarize my health this week.",       color: "text-purple-500" },
  { icon: Heart,      text: "Am I following my care plan?",         color: "text-primary-500" },
  { icon: Activity,   text: "How many steps should I walk today?",  color: "text-green-600" },
  { icon: TrendingUp, text: "What changed compared to yesterday?",  color: "text-blue-600" },
];

const DOCTOR_SUGGESTIONS = [
  { icon: Heart,      text: "Why is this patient high risk?",       color: "text-red-500" },
  { icon: TrendingUp, text: "What changed in the last 7 days?",    color: "text-blue-500" },
  { icon: Activity,   text: "Show compliance summary.",             color: "text-green-500" },
  { icon: Lightbulb,  text: "Summarize patient recovery.",         color: "text-purple-500" },
  { icon: Pill,       text: "What factors contributed most?",      color: "text-amber-500" },
  { icon: Heart,      text: "Explain the prediction.",             color: "text-primary-500" },
];

// ── Chat message component ────────────────────────────────────────────────

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end gap-3">
      <div className="max-w-[80%] bg-primary-500 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm shadow-sm">
        {text}
      </div>
      <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/40 flex items-center justify-center shrink-0">
        <User size={14} className="text-primary-600" />
      </div>
    </div>
  );
}

function AssistantBubble({ response }: { response: AssistantResponse }) {
  const [showEvidence, setShowEvidence] = useState(false);

  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-blue-600 flex items-center justify-center shrink-0 shadow-sm">
        <Bot size={14} className="text-white" />
      </div>
      <div className="max-w-[85%] space-y-2">
        {/* Main answer */}
        <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <div className="text-sm text-gray-900 dark:text-white whitespace-pre-line leading-relaxed">
            {response.answer.replace(/\*\*(.*?)\*\*/g, '$1')}
          </div>
        </div>

        {/* Recommendations */}
        {response.recommendations.length > 0 && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800/50 rounded-xl px-4 py-3">
            <p className="text-xs font-semibold text-green-700 dark:text-green-400 mb-2 flex items-center gap-1.5">
              <Lightbulb size={12} /> Recommendations
            </p>
            <ul className="space-y-1">
              {response.recommendations.map((r, i) => (
                <li key={i} className="text-xs text-gray-700 dark:text-gray-300 flex gap-2">
                  <span className="text-green-500 shrink-0 mt-0.5">→</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Expected improvement */}
        {response.expected_improvement && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/50 rounded-xl px-4 py-2.5">
            <p className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-1">
              📈 Expected Outcome
            </p>
            <p className="text-xs text-gray-700 dark:text-gray-300">{response.expected_improvement}</p>
          </div>
        )}

        {/* Evidence toggle */}
        {response.evidence.length > 0 && (
          <button
            onClick={() => setShowEvidence(v => !v)}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <ChevronDown size={12} className={cn("transition-transform", showEvidence && "rotate-180")} />
            {showEvidence ? "Hide" : "Show"} evidence ({response.evidence.length} data points)
          </button>
        )}

        <AnimatePresence>
          {showEvidence && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-gray-50 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-700 rounded-xl px-4 py-3 overflow-hidden"
            >
              <p className="text-xs font-semibold text-gray-500 mb-2">📊 Data Sources</p>
              <div className="grid grid-cols-2 gap-1.5">
                {response.evidence.map((e, i) => (
                  <div key={i} className="flex flex-col">
                    <span className="text-[10px] text-gray-400 uppercase tracking-wide">{e.label}</span>
                    <span className="text-xs font-semibold text-gray-800 dark:text-gray-200">{e.value}</span>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-gray-400 mt-2">
                Sources: {response.data_sources.join(", ")}
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-blue-600 flex items-center justify-center shrink-0">
        <Bot size={14} className="text-white" />
      </div>
      <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-5">
          {[0, 0.15, 0.3].map((delay, i) => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-primary-400"
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 0.6, delay, repeat: Infinity }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────

interface ChatEntry {
  type: "user" | "assistant";
  text?: string;
  response?: AssistantResponse;
}

export function AssistantPage() {
  const { user } = useAuthContext();
  const role = user?.role ?? "patient";
  const suggestions = role === "doctor" ? DOCTOR_SUGGESTIONS : PATIENT_SUGGESTIONS;

  const [input, setInput]     = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<AssistantMessage[]>([]);
  const [chat, setChat]       = useState<ChatEntry[]>([]);
  const [error, setError]     = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, loading]);

  const send = async (question: string) => {
    if (!question.trim() || loading) return;
    setError(null);
    const q = question.trim();
    setInput("");
    setChat(c => [...c, { type: "user", text: q }]);
    setLoading(true);

    try {
      const res = await askAssistant({ question: q, history });
      setHistory(h => [
        ...h,
        { role: "user", content: q },
        { role: "assistant", content: res.answer },
      ]);
      setChat(c => [...c, { type: "assistant", response: res }]);
    } catch (err: any) {
      setError(err?.message ?? "Unable to reach the assistant. Please try again.");
      setChat(c => c.slice(0, -1)); // remove the user message that failed
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    send(input);
  };

  const clearChat = () => {
    setChat([]);
    setHistory([]);
    setError(null);
  };

  const isEmpty = chat.length === 0;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-primary-500 to-blue-600 flex items-center justify-center shadow-md">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              Health Assistant
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300 uppercase tracking-wide">
                Beta
              </span>
            </h1>
            <p className="text-xs text-gray-500">Answers from your real health data · No hallucinations</p>
          </div>
        </div>
        {!isEmpty && (
          <button onClick={clearChat}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <X size={12} /> Clear
          </button>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto rounded-2xl bg-gray-50/50 dark:bg-gray-900/30 border border-gray-100 dark:border-gray-800 p-4 space-y-4">
        {isEmpty ? (
          /* Welcome screen */
          <div className="flex flex-col items-center justify-center h-full gap-6 py-8">
            <div className="text-center">
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-primary-500 to-blue-600 flex items-center justify-center mx-auto mb-4 shadow-lg">
                <Sparkles size={28} className="text-white" />
              </div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                {role === "doctor" ? "Clinical AI Assistant" : "Your Personal Health Coach"}
              </h2>
              <p className="text-sm text-gray-500 mt-1 max-w-sm">
                {role === "doctor"
                  ? "Ask questions about your patients grounded in their real Digital Twin data."
                  : "Ask me anything about your health — I answer from your real monitoring data, not generic advice."}
              </p>
              <p className="text-xs text-gray-400 mt-2 max-w-xs mx-auto">
                ⚡ All answers are grounded in your actual health records — zero hallucination
              </p>
            </div>

            <div className="w-full grid grid-cols-2 gap-2 max-w-lg">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => send(s.text)}
                  className="flex items-center gap-2.5 p-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all text-left group"
                >
                  <s.icon size={16} className={cn(s.color, "shrink-0")} />
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300 group-hover:text-primary-700 dark:group-hover:text-primary-300 leading-tight">
                    {s.text}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Messages */
          <>
            {chat.map((entry, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                {entry.type === "user"
                  ? <UserBubble text={entry.text!} />
                  : <AssistantBubble response={entry.response!} />
                }
              </motion.div>
            ))}
            {loading && <TypingIndicator />}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="mt-2 flex items-center gap-2 px-3 py-2 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs">
          <X size={12} className="shrink-0" />
          {error}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="mt-3 flex gap-2 shrink-0">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder={role === "doctor"
            ? "Ask about a patient's risk, compliance, or care plan…"
            : "Ask about your health, recovery, medication, or care plan…"}
          disabled={loading}
          className="flex-1 h-11 px-4 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="h-11 w-11 rounded-2xl bg-primary-500 hover:bg-primary-600 disabled:opacity-40 disabled:pointer-events-none transition-colors flex items-center justify-center shadow-sm"
        >
          {loading
            ? <Loader2 size={16} className="text-white animate-spin" />
            : <Send size={16} className="text-white" />
          }
        </button>
      </form>

      {/* Quick suggestions in chat */}
      {!isEmpty && !loading && (
        <div className="mt-2 flex gap-1.5 overflow-x-auto pb-1 shrink-0">
          {suggestions.slice(0, 4).map((s, i) => (
            <button
              key={i}
              onClick={() => send(s.text)}
              className="shrink-0 text-xs px-3 py-1.5 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-400 hover:border-primary-400 hover:text-primary-600 transition-colors whitespace-nowrap"
            >
              {s.text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
