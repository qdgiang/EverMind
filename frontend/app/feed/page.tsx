// DSH-2, owner: B. Feed (SRF-1) + Inbox (SRF-2).
import Link from "next/link";
import { cookies } from "next/headers";
import { ApiError } from "@/components/dashboard/ApiError";
import { api } from "@/lib/api-client";
import { DEFAULT_PERSONA_HANDLE, PERSONA_COOKIE } from "@/lib/persona";
import type { FeedEntry, InboxItem } from "@/lib/types";

export default async function FeedPage() {
  let feed: FeedEntry[] = [];
  let inbox: InboxItem[] = [];
  let error: string | null = null;
  const persona = (await cookies()).get(PERSONA_COOKIE)?.value ?? DEFAULT_PERSONA_HANDLE;
  try {
    [feed, inbox] = await Promise.all([
      api.get<FeedEntry[]>("/feed", persona),
      api.get<InboxItem[]>("/inbox", persona),
    ]);
  } catch (caught) {
    error = (caught as Error).message;
  }

  return (
    <div className="grid grid-cols-2 gap-6">
      {error && <div className="col-span-2"><ApiError message={error} /></div>}
      <section>
        <h1 className="mb-4 text-lg font-semibold">Feed</h1>
        {feed.length === 0 && <p className="text-sm text-slate-500">No entries yet.</p>}
        <ul className="space-y-2">
          {feed.map((entry) => (
            <li key={entry.id} className="rounded-md border border-slate-200 p-3 text-sm dark:border-slate-800">
              <div className="flex items-center justify-between">
                <span>{entry.kind}</span>
                <span className="text-xs text-slate-400">{new Date(entry.ts).toLocaleString()}</span>
              </div>
              {entry.task_id != null && (
                <Link href={`/tasks/${entry.task_id}`} className="text-xs text-brand-coral hover:underline">
                  task #{entry.task_id}
                </Link>
              )}
              {entry.superseded_by_entry != null && (
                <span className="ml-2 text-xs text-amber-600">↩ retracted</span>
              )}
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h1 className="mb-4 text-lg font-semibold">Inbox</h1>
        {inbox.length === 0 && <p className="text-sm text-slate-500">Nothing pending.</p>}
        <ul className="space-y-2">
          {inbox.map((item) => (
            <li key={item.id} className="rounded-md border border-slate-200 p-3 text-sm dark:border-slate-800">
              <div className="flex items-center justify-between">
                <span>{item.kind}</span>
                <span className="text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</span>
              </div>
              {item.resolved_at && (
                <span className="text-xs text-emerald-600">resolved: {item.resolution}</span>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
