import DOMPurify from "dompurify";
import { FileCode, Loader2, MessageSquare, Send, Sparkles } from "lucide-react";
import { marked } from "marked";
import { useState } from "react";

import type { AskResponse } from "../../types/repoIntel";

// Configure marked once: use synchronous rendering with GitHub-flavoured breaks.
marked.setOptions({ gfm: true, breaks: false });

/** Render Markdown to sanitised HTML. Safe to use with dangerouslySetInnerHTML. */
function renderMarkdown(text: string): string {
  // marked.parse returns string when not async (default with no async option)
  const raw = marked.parse(text) as string;
  return DOMPurify.sanitize(raw);
}

interface Turn {
  question: string;
  response: AskResponse;
}

const SAMPLE_QUESTIONS = [
  "How does this project fit together?",
  "Where is the API layer?",
  "What should I test before changing this?",
];

/** Renders a Markdown string as sanitised HTML styled to match the dark theme. */
function MarkdownAnswer({ text }: { text: string }) {
  const html = renderMarkdown(text);
  return (
    <div
      className="prose prose-invert prose-sm max-w-none text-[13px] leading-relaxed text-ink-200
        [&_code]:rounded [&_code]:bg-ink-900 [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-[11px]
        [&_pre]:overflow-x-auto [&_pre]:rounded-md [&_pre]:border [&_pre]:border-ink-700 [&_pre]:bg-ink-950 [&_pre]:p-2.5
        [&_pre_code]:bg-transparent [&_pre_code]:p-0
        [&_a]:text-amber-400 [&_a]:underline
        [&_strong]:text-ink-100
        [&_h1]:text-[14px] [&_h1]:font-semibold [&_h1]:text-ink-100
        [&_h2]:text-[13px] [&_h2]:font-semibold [&_h2]:text-ink-100
        [&_h3]:text-[12px] [&_h3]:font-medium [&_h3]:text-ink-200
        [&_li]:ml-4 [&_ul]:list-disc [&_ol]:list-decimal"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export default function AskPanel({
  onAsk,
}: {
  onAsk: (question: string) => Promise<AskResponse>;
}) {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(q: string) {
    const trimmed = q.trim();
    if (!trimmed || asking) return;
    setAsking(true);
    setError(null);
    try {
      const response = await onAsk(trimmed);
      setTurns((t) => [...t, { question: trimmed, response }]);
      setQuestion("");
    } catch {
      setError("Could not get an answer. Is the backend still running?");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        {turns.length === 0 && (
          <div className="rounded-md border border-dashed border-ink-700 p-4">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-ink-300">
              <MessageSquare size={13} /> Ask about this repository
            </p>
            <p className="mb-3 text-[12px] text-ink-500">
              Answers are grounded in the files from your last scan — DevPilot shows which excerpts it used.
            </p>
            <div className="flex flex-wrap gap-1.5">
              {SAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => submit(q)}
                  className="rounded-full border border-ink-700 px-2.5 py-1 text-[11px] text-ink-300 hover:border-amber-500/50 hover:text-amber-300"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {turns.map((turn, i) => (
          <div key={i} className="space-y-2">
            <p className="text-[13px] font-medium text-ink-100">{turn.question}</p>
            <div className="rounded-md border border-ink-800 bg-ink-850 p-3">
              <div className="mb-1.5 flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-ink-500">
                {turn.response.mode === "ai" && <Sparkles size={11} className="text-amber-400" />}
                {turn.response.mode === "ai"
                  ? "AI answer, grounded in repository excerpts"
                  : turn.response.mode === "retrieval"
                    ? "Repository excerpts (no AI model configured)"
                    : "No relevant excerpts found"}
              </div>
              <MarkdownAnswer text={turn.response.answer} />

              {turn.response.used_files.length > 0 && (
                <div className="mt-3 space-y-1 border-t border-ink-800 pt-2">
                  <p className="text-[10px] uppercase tracking-wide text-ink-500">Files used</p>
                  {turn.response.used_files.map((f, fi) => (
                    <p key={fi} className="flex items-center gap-1.5 font-mono text-[11px] text-ink-400">
                      <FileCode size={11} className="shrink-0" />
                      {f.path}:{f.start_line}-{f.end_line}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {error && <p className="text-xs text-signal-red">{error}</p>}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(question);
        }}
        className="mt-3 flex items-center gap-2 border-t border-ink-800 pt-3"
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="How does authentication work?"
          className="flex-1 rounded-md border border-ink-600 bg-ink-850 px-3 py-2 text-sm text-ink-100 placeholder:text-ink-500 focus:border-amber-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={asking || !question.trim()}
          className="flex items-center gap-1.5 rounded-md bg-amber-500 px-3 py-2 text-xs font-medium text-ink-950 transition-colors hover:bg-amber-400 disabled:opacity-50"
        >
          {asking ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
          Ask
        </button>
      </form>
    </div>
  );
}
