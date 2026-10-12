import { useState } from "react";

type Candidate = {
  message_id: string;
  sender: string;
  subject: string;
  category: string;
  is_sent: boolean;
  is_draft: boolean;
  is_work_related: boolean;
  is_personally_protected: boolean;
  classification_confident: boolean;
  proposed_action: string;
  policy_allowed_without_approval: boolean;
  policy_reason: string;
  final_status: string;
};

type Plan = {
  request_id: string;
  mode: string;
  message: string;
  candidates: Candidate[];
  actions_executed: number;
  approval_required: boolean;
};

type RagSource = {
  source_id: string;
  message_id: string;
  subject: string;
  date: string;
  chunk_index: number;
};

type RagAnswer = {
  answer: string;
  sources: RagSource[];
  grounded: boolean;
};

type AssistResponse = {
  cleanup_plan: Plan;
  related_context: RagAnswer;
  gmail_indexing?: {
    status: string;
    messages_fetched: number;
    messages_indexed: number;
    chunks_indexed: number;
    skipped_empty: number;
    gmail_read_only: boolean;
  };
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export default function App() {
  const [request, setRequest] = useState(
    "Find old promotional emails and recommend safe cleanup actions.",
  );
  const [question, setQuestion] = useState("");
  const [refreshRag, setRefreshRag] = useState(true);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [ragAnswer, setRagAnswer] = useState<RagAnswer | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  async function generatePlan() {
    setLoading(true);
    setError("");
    setStatus("");
    setPlan(null);
    setRagAnswer(null);
    setSelected([]);

    try {
      const response = await fetch(`${API_BASE}/cleanup/assist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request,
          question: question.trim() || request,
          max_candidates: 3,
          use_gmail_metadata: true,
          index_gmail_for_rag: refreshRag,
          gmail_max_results: 3,
        }),
      });
      if (!response.ok) throw new Error(`Inbox analysis returned ${response.status}`);

      const result = await response.json() as AssistResponse;
      setPlan(result.cleanup_plan);
      setRagAnswer(result.related_context);

      if (result.gmail_indexing) {
        const indexed = result.gmail_indexing;
        setStatus(
          `Read-only Gmail indexing: fetched ${indexed.messages_fetched}, ` +
          `indexed ${indexed.messages_indexed} messages into ${indexed.chunks_indexed} chunks.`,
        );
      } else {
        setStatus("Cleanup metadata reviewed; RAG used the existing local index.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Inbox analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const eligible = (plan?.candidates ?? []).filter(
    candidate => candidate.proposed_action === "trash"
      && !candidate.is_sent && !candidate.is_draft
      && !candidate.is_work_related && !candidate.is_personally_protected
      && candidate.classification_confident,
  );

  function toggle(id: string) {
    setSelected(old => old.includes(id) ? old.filter(item => item !== id) : [...old, id]);
  }

  return (
    <main style={{ maxWidth: 1000, margin: "2rem auto", padding: "0 1rem", fontFamily: "system-ui" }}>
      <h1>Email Intelligence &amp; Safe Inbox Cleaner</h1>
      <p>
        Read-only Gmail intelligence. One prompt runs cleanup planning and grounded RAG;
        no email modifications are executed.
      </p>

      <section style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16, marginBottom: 16 }}>
        <h2>Cleanup prompt and email context</h2>
        <label htmlFor="request">What should the inbox cleaner find or review?</label>
        <textarea
          id="request"
          value={request}
          onChange={event => setRequest(event.target.value)}
          rows={3}
          style={{ display: "block", width: "100%", margin: "8px 0" }}
        />

        <label htmlFor="question">Optional RAG question (defaults to the cleanup prompt)</label>
        <textarea
          id="question"
          value={question}
          onChange={event => setQuestion(event.target.value)}
          placeholder={request}
          rows={2}
          style={{ display: "block", width: "100%", margin: "8px 0" }}
        />

        <label style={{ display: "block", margin: "12px 0" }}>
          <input
            type="checkbox"
            checked={refreshRag}
            onChange={event => setRefreshRag(event.target.checked)}
          />{" "}
          Refresh local RAG context from up to 3 recent Inbox messages (read-only; message text is stored locally)
        </label>

        <button disabled={loading || request.trim().length < 3} onClick={generatePlan}>
          {loading ? "Analyzing inbox..." : "Run cleanup + RAG review"}
        </button>
        {error && <p role="alert">{error}</p>}
        {status && <p role="status">{status}</p>}
        {plan && <p>{plan.message} Request ID: <code>{plan.request_id}</code></p>}
      </section>

      <section style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16, marginBottom: 16 }}>
        <h2>Cleanup recommendations</h2>
        <p>Uncertain and protected messages remain unchanged. This UI cannot delete email.</p>
        {eligible.length > 0 && (
          <label>
            <input
              type="checkbox"
              checked={eligible.every(candidate => selected.includes(candidate.message_id))}
              onChange={event => setSelected(event.target.checked ? eligible.map(candidate => candidate.message_id) : [])}
            /> Select all eligible
          </label>
        )}
        {plan?.candidates.map(candidate => {
          const canSelect = eligible.some(item => item.message_id === candidate.message_id);
          return (
            <article key={candidate.message_id} style={{ borderTop: "1px solid #eee", padding: "12px 0" }}>
              <label>
                <input
                  type="checkbox"
                  disabled={!canSelect}
                  checked={selected.includes(candidate.message_id)}
                  onChange={() => toggle(candidate.message_id)}
                />
                <strong> {candidate.subject}</strong> - {candidate.sender}
              </label>
              <div>Category: {candidate.category}; proposed action: {candidate.proposed_action}</div>
              <div>Policy: {candidate.policy_reason}</div>
              <small>Status: {candidate.final_status}</small>
            </article>
          );
        })}
        <p>Selected: {selected.length}. No Gmail write endpoint exists; actions executed: {plan?.actions_executed ?? 0}.</p>
      </section>

      <section style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16 }}>
        <h2>Grounded RAG response</h2>
        {!ragAnswer && <p>Run the cleanup prompt to retrieve related email context.</p>}
        {ragAnswer && (
          <div>
            <p>{ragAnswer.answer}</p>
            <small>Grounded: {ragAnswer.grounded ? "yes" : "no"}</small>
            {ragAnswer.sources.length > 0 && (
              <ul>
                {ragAnswer.sources.map(source => (
                  <li key={`${source.source_id}-${source.message_id}-${source.chunk_index}`}>
                    {source.source_id}: {source.subject || source.message_id} ({source.date})
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
