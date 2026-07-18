"use client";

import { useState } from "react";
import { DEFAULT_PERSONA_HANDLE, PERSONA_COOKIE } from "@/lib/persona";

export default function QAPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<{ answer: string; citations: { decision_id: number; message_ids: number[] }[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  async function ask(event: React.FormEvent) {
    event.preventDefault(); setError(null);
    const raw = document.cookie.split("; ").find((item) => item.startsWith(`${PERSONA_COOKIE}=`));
    const persona = raw ? decodeURIComponent(raw.split("=")[1]) : DEFAULT_PERSONA_HANDLE;
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/qa`, { method: "POST", headers: { "Content-Type": "application/json", "X-Persona": persona }, body: JSON.stringify({ question }) });
    if (!response.ok) { setError(`Request failed: ${response.status}`); return; }
    setAnswer(await response.json());
  }
  return (
    <div>
      <h1 className="mb-4 text-lg font-semibold">Ask EverMind</h1>
      <form onSubmit={ask} className="space-y-3"><input value={question} onChange={(event) => setQuestion(event.target.value)} required className="w-full rounded border p-2" placeholder="Ask about a current decision" /><button className="rounded bg-brand-coral px-4 py-2 text-white">Ask</button></form>
      {error && <p role="alert" className="mt-3 text-red-700">{error}</p>}
      {answer && <div className="mt-4"><p>{answer.answer}</p><p className="text-sm text-slate-500">Receipts: {answer.citations.map((citation) => `decision #${citation.decision_id}: messages ${citation.message_ids.join(", ")}`).join("; ") || "none"}</p></div>}
    </div>
  );
}
