"use client";

// Ported from frontend_ref/index.html topbar (search trigger + persona avatar).
// Persona switcher (DSH-1, "modeled, not enforced" — architecture.md §Trust
// boundaries #3) is the ONLY identity control; there is no login.
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { DEFAULT_PERSONA_HANDLE, PERSONA_COOKIE } from "@/lib/persona";
import type { Persona } from "@/lib/types";

export function Topbar() {
  const router = useRouter();
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [persona, setPersona] = useState(DEFAULT_PERSONA_HANDLE);

  useEffect(() => {
    const cookie = document.cookie
      .split("; ")
      .find((item) => item.startsWith(`${PERSONA_COOKIE}=`));
    if (cookie) setPersona(decodeURIComponent(cookie.split("=")[1]));

    api.get<Persona[]>("/personas")
      .then(setPersonas)
      .catch(() => setPersonas([]));
  }, []);

  function selectPersona(handle: string) {
    setPersona(handle);
    document.cookie = `${PERSONA_COOKIE}=${encodeURIComponent(handle)}; path=/; SameSite=Lax`;
    router.refresh();
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 px-4 dark:border-slate-800">
      <button className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-500 dark:border-slate-800">
        <span>Tìm task, decision hoặc evidence…</span>
        <kbd className="rounded bg-slate-100 px-1 text-xs dark:bg-slate-800">⌘K</kbd>
      </button>

      <select
        value={persona}
        onChange={(e) => selectPersona(e.target.value)}
        aria-label="Persona switcher"
        className="rounded-md border border-slate-200 bg-transparent px-2 py-1.5 text-sm dark:border-slate-800"
      >
        {(personas.length ? personas : [{
          id: 0, handle: DEFAULT_PERSONA_HANDLE, name: "Linh", role_rank: 3, status: "active" as const,
        }]).map((p) => (
          <option key={p.handle} value={p.handle}>
            {p.name} ({p.handle})
          </option>
        ))}
      </select>
    </header>
  );
}
