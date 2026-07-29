"use client";

import { useEffect, useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";
const POLL_INTERVAL_MS = 15000;

type EventItem = { type: string; summary: string; at: string; is_concern: boolean };
type Today = { name: string; status: "ok" | "attention"; events: EventItem[] };
type Reminder = { id: string; subject: string; due_at: string; status: string };

const REMINDER_STATUS_STYLE: Record<string, string> = {
  pending: "bg-secondary text-secondary-foreground",
  delivered: "bg-clay-soft/40 text-clay",
  acknowledged: "bg-moss-soft text-moss",
  missed: "bg-marigold-soft text-marigold",
};

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString([], { dateStyle: "short", timeStyle: "short" });
}

export default function CareTeamPage() {
  const [today, setToday] = useState<Today | null>(null);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [subject, setSubject] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadToday() {
    const res = await fetch(`${API_URL}/today`);
    setToday(await res.json());
  }

  async function loadReminders() {
    const res = await fetch(`${API_URL}/reminders`);
    setReminders(await res.json());
  }

  useEffect(() => {
    loadToday();
    loadReminders();
    const interval = setInterval(() => {
      loadToday();
      loadReminders();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  async function addReminder(e: React.FormEvent) {
    e.preventDefault();
    if (!subject.trim() || !dueAt || submitting) return;
    setSubmitting(true);
    try {
      await fetch(`${API_URL}/reminders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject, due_at: dueAt }),
      });
      setSubject("");
      setDueAt("");
      await Promise.all([loadReminders(), loadToday()]);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-dvh bg-background">
      <div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-6">
        <header className="flex items-center justify-between">
          <h1 className="font-heading text-lg font-bold text-clay">Vessa · Care Team</h1>
          <ThemeToggle />
        </header>

        <section className="vessel-shape-sm bg-card px-5 py-4 ring-1 ring-border">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold">{today?.name ?? "Rose"} · Today</h2>
            <span
              className={`vessel-shape-sm px-3 py-1 text-xs font-bold ${
                today?.status === "attention"
                  ? "bg-marigold-soft text-marigold"
                  : "bg-moss-soft text-moss"
              }`}
            >
              {today?.status === "attention" ? "⚠️ Needs attention" : "🟢 OK"}
            </span>
          </div>

          <ul className="mt-4 flex flex-col gap-1.5">
            {(today?.events ?? []).map((e, i) => (
              <li
                key={i}
                className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm ${
                  e.is_concern ? "bg-marigold-soft text-marigold" : "text-foreground/85"
                }`}
              >
                <span>{e.is_concern ? "⚠️" : e.type === "reminder_acknowledged" ? "✓" : "•"}</span>
                <span className="flex-1 truncate">{e.summary}</span>
                <span className="shrink-0 text-xs text-muted-foreground">{formatTime(e.at)}</span>
              </li>
            ))}
            {today && today.events.length === 0 && (
              <li className="px-2.5 py-1.5 text-sm text-muted-foreground">Nothing yet today.</li>
            )}
          </ul>
        </section>

        <section className="vessel-shape-sm bg-card px-5 py-4 ring-1 ring-border">
          <h2 className="text-base font-bold">Reminders</h2>

          <ul className="mt-3 flex flex-col gap-2">
            {reminders.map((r) => (
              <li
                key={r.id}
                className="flex items-center justify-between gap-2 rounded-lg bg-background px-3 py-2 text-sm"
              >
                <span className="truncate">
                  {r.subject} — due {formatDateTime(r.due_at)}
                </span>
                <span
                  className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    REMINDER_STATUS_STYLE[r.status] ?? "bg-secondary text-secondary-foreground"
                  }`}
                >
                  {r.status}
                </span>
              </li>
            ))}
            {reminders.length === 0 && (
              <li className="px-3 py-2 text-sm text-muted-foreground">No reminders yet.</li>
            )}
          </ul>

          <form onSubmit={addReminder} className="mt-4 flex flex-col gap-2">
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Take morning vitamins"
              className="h-10 rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            />
            <div className="flex gap-2">
              <input
                type="datetime-local"
                value={dueAt}
                onChange={(e) => setDueAt(e.target.value)}
                className="h-10 flex-1 rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
              />
              <button
                type="submit"
                disabled={submitting}
                className="h-10 shrink-0 rounded-lg bg-primary px-4 text-sm font-bold text-primary-foreground disabled:opacity-50"
              >
                + Add
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
