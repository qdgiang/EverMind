// DSH-5 (half), owner: B. Blocker board grouped by party (SIG-2).
import Link from "next/link";
import { api } from "@/lib/api-client";
import { currentPersona } from "@/lib/persona";
import type { BlockersResponse } from "@/lib/types";

export default async function BlockersPage() {
  let board: BlockersResponse = { groups: [] };
  try {
    const persona = await currentPersona();
    const projects = await api.get<{ id: number }[]>("/projects", persona);
    if (projects[0]) board = await api.get<BlockersResponse>(`/blockers?project_id=${projects[0].id}`, persona);
  } catch {
    // backend not reachable
  }

  const groups = board.groups;

  return (
    <div>
      <h1 className="mb-4 text-lg font-semibold">Blocker radar</h1>
      {groups.length === 0 && <p className="text-sm text-slate-500">No open blockers.</p>}
      <div className="space-y-4">
        {groups.map((group) => (
          <div key={`${group.waiting_on.party_id}-${group.waiting_on.text}`} className="rounded-lg border border-amber-300 bg-amber-50 p-3 dark:border-amber-700 dark:bg-amber-950/30">
            <div className="mb-2 font-medium">
              {group.waiting_on.name ?? group.waiting_on.text ?? "Unspecified"} <span className="text-sm text-slate-500">· {group.tasks.length} task(s)</span>
            </div>
            <ul className="space-y-1">
              {group.tasks.map((t) => (
                <li key={t.task_id} className="text-sm">
                  <Link href={`/tasks/${t.task_id}`} className="hover:underline">
                    {t.description}
                  </Link>
                  {t.since && (
                    <span className="ml-2 text-xs text-slate-500">
                      since {new Date(t.since).toLocaleDateString()}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
