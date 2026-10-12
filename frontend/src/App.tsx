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

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export default function App() {
  const [request, setRequest] = useState("Find old promotional emails and recommend safe cleanup actions.");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generatePlan() {
    setLoading(true);
    setError("");
    setPlan(null);
    setSelected([]);
    try {
      const response = await fetch(`${API_BASE}/cleanup/plan/gmail`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request, max_candidates: 20 })
      });
      if (!response.ok) throw new Error(`API returned ${response.status}`);
      setPlan(await response.json() as Plan);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  const eligible = (plan?.candidates ?? []).filter(
    c => c.proposed_action === "trash"
      && !c.is_sent && !c.is_draft
      && !c.is_work_related && !c.is_personally_protected
      && c.classification_confident
  );

  function toggle(id: string) {
    setSelected(old => old.includes(id) ? old.filter(x => x !== id) : [...old, id]);
  }

  return (
    <main style={{ maxWidth: 1000, margin: "2rem auto", padding: "0 1rem", fontFamily: "system-ui" }}>
      <h1>Email Intelligence & Safe Inbox Cleaner</h1>
      <p>
        Read-only Gmail intelligence. Messages are reviewed conservatively;
        no email modifications are executed.
      </p>

      <section style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16, marginBottom: 16 }}>
        <h2>Inbox cleanup planner</h2>
        <label htmlFor="request">Describe what you want to find</label>
        <textarea id="request" value={request} onChange={e => setRequest(e.target.value)}
          rows={3} style={{ display: "block", width: "100%", margin: "8px 0" }} />
        <button disabled={loading || request.trim().length < 3} onClick={generatePlan}>
          {loading ? "Planning..." : "Generate dry-run plan"}
        </button>
        {error && <p role="alert">{error}</p>}
        {plan && <p>{plan.message} Request ID: <code>{plan.request_id}</code></p>}
      </section>

      <section style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16, marginBottom: 16 }}>
        <h2>Review candidates</h2>
        <p>Protected and uncertain messages are not selectable. This scaffold cannot delete email.</p>
        {eligible.length > 0 && (
          <label>
            <input
              type="checkbox"
              checked={eligible.every(c => selected.includes(c.message_id))}
              onChange={e => setSelected(e.target.checked ? eligible.map(c => c.message_id) : [])}
            /> Select all eligible
          </label>
        )}
        {plan?.candidates.map(candidate => {
          const canSelect = eligible.some(c => c.message_id === candidate.message_id);
          return (
            <article key={candidate.message_id} style={{ borderTop: "1px solid #eee", padding: "12px 0" }}>
              <label>
                <input type="checkbox" disabled={!canSelect}
                  checked={selected.includes(candidate.message_id)}
                  onChange={() => toggle(candidate.message_id)} />
                <strong> {candidate.subject}</strong> â€” {candidate.sender}
              </label>
              <div>Category: {candidate.category}; proposed action: {candidate.proposed_action}</div>
              <div>Policy: {candidate.policy_reason}</div>
              <small>Status: {candidate.final_status}</small>
            </article>
          );
        })}
        <p>Selected: {selected.length}. Deletion execution is disabled in this scaffold; no Gmail write endpoint exists.</p>
      </section>

      <section style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16 }}>
        <h2>Ask my emails (RAG)</h2>
        <p>
          RAG integration is still in progress. Answers will be enabled after
          Weaviate retrieval and source-grounding are verified.
        </p>
      </section>
    </main>
  );
}
