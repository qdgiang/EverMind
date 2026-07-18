import { cookies } from "next/headers";
import { ApiError } from "@/components/dashboard/ApiError";
import { api } from "@/lib/api-client";
import { DEFAULT_PERSONA_HANDLE, PERSONA_COOKIE } from "@/lib/persona";
import type { DecisionSummary } from "@/lib/types";

export default async function DecisionsPage() {
  let decisions: DecisionSummary[] = [];
  let error: string | null = null;
  const persona = (await cookies()).get(PERSONA_COOKIE)?.value ?? DEFAULT_PERSONA_HANDLE;
  try {
    decisions = await api.get<DecisionSummary[]>("/decisions", persona);
  } catch (caught) {
    error = (caught as Error).message;
  }

  return (
    <div>
      <h1 className="mb-4 text-lg font-semibold">Decision log</h1>
      {error && <ApiError message={error} />}
      {!error && decisions.length === 0 && (
        <p className="text-sm text-slate-500">No active decisions yet.</p>
      )}
      <ul className="space-y-3">
        {decisions.map((decision) => (
          <li key={decision.id} className="rounded-md border border-slate-200 p-3 dark:border-slate-800">
            <div className="flex items-center justify-between gap-3 text-xs text-slate-500">
              <span className="uppercase">{decision.status}</span>
              <time dateTime={decision.ts}>{new Date(decision.ts).toLocaleString()}</time>
            </div>
            <p className="mt-2 text-sm">{decision.description}</p>
            <p className="mt-2 text-xs text-slate-500">Decided by {decision.decided_by}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
