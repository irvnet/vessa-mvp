"use client";

import { useEffect, useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";
const POLL_INTERVAL_MS = 15000;

type EventItem = { type: string; summary: string; at: string; is_concern: boolean };
type Today = { name: string; status: "ok" | "attention"; events: EventItem[] };
type Reminder = { id: string; subject: string; due_at: string; status: string };
type CaregiverNotification = { message: string; at: string };

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

function toDatetimeLocalValue(iso: string) {
  // datetime-local inputs want "YYYY-MM-DDTHH:mm" — due_at is a full isoformat().
  return iso.slice(0, 16);
}

export default function CareTeamPage() {
  const [today, setToday] = useState<Today | null>(null);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [notifications, setNotifications] = useState<CaregiverNotification[]>([]);
  const [subject, setSubject] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editSubject, setEditSubject] = useState("");
  const [editDueAt, setEditDueAt] = useState("");
  const [actionBusyId, setActionBusyId] = useState<string | null>(null);

  async function loadToday() {
    const res = await fetch(`${API_URL}/today`);
    setToday(await res.json());
  }

  async function loadReminders() {
    const res = await fetch(`${API_URL}/reminders`);
    setReminders(await res.json());
  }

  async function loadNotifications() {
    const res = await fetch(`${API_URL}/notifications`);
    setNotifications(await res.json());
  }

  useEffect(() => {
    loadToday();
    loadReminders();
    loadNotifications();
    const interval = setInterval(() => {
      loadToday();
      loadReminders();
      loadNotifications();
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

  function startEdit(r: Reminder) {
    setEditingId(r.id);
    setEditSubject(r.subject);
    setEditDueAt(toDatetimeLocalValue(r.due_at));
  }

  async function saveEdit(id: string) {
    if (!editSubject.trim() || !editDueAt) return;
    setActionBusyId(id);
    try {
      await fetch(`${API_URL}/reminders/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject: editSubject, due_at: editDueAt }),
      });
      setEditingId(null);
      await Promise.all([loadReminders(), loadToday()]);
    } finally {
      setActionBusyId(null);
    }
  }

  async function deleteReminder(id: string) {
    setActionBusyId(id);
    try {
      await fetch(`${API_URL}/reminders/${id}`, { method: "DELETE" });
      await Promise.all([loadReminders(), loadToday()]);
    } finally {
      setActionBusyId(null);
    }
  }

  async function acknowledgeReminder(id: string) {
    setActionBusyId(id);
    try {
      await fetch(`${API_URL}/reminders/${id}/acknowledge`, { method: "POST" });
      await Promise.all([loadReminders(), loadToday()]);
    } finally {
      setActionBusyId(null);
    }
  }

  return (
    <main className="min-h-dvh bg-background">
      <div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-6 md:max-w-4xl">
        <header className="flex items-center justify-between">
          <h1 className="font-heading text-lg font-bold text-clay">Vessa · Care Team</h1>
          <ThemeToggle />
        </header>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 md:items-start">
        <section className="vessel-shape-sm bg-card px-5 py-4 ring-1 ring-border">
          <h2 className="text-base font-bold">Reminders</h2>

          <ul className="mt-3 flex flex-col gap-2">
            {reminders.map((r) =>
              editingId === r.id ? (
                <li key={r.id} className="flex flex-col gap-2 rounded-lg bg-background px-3 py-2">
                  <input
                    value={editSubject}
                    onChange={(e) => setEditSubject(e.target.value)}
                    className="h-9 rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
                  />
                  <div className="flex gap-2">
                    <input
                      type="datetime-local"
                      value={editDueAt}
                      onChange={(e) => setEditDueAt(e.target.value)}
                      className="h-9 flex-1 rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
                    />
                    <button
                      type="button"
                      onClick={() => saveEdit(r.id)}
                      disabled={actionBusyId === r.id}
                      className="h-9 shrink-0 rounded-lg bg-primary px-3 text-xs font-bold text-primary-foreground disabled:opacity-50"
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingId(null)}
                      className="h-9 shrink-0 rounded-lg bg-secondary px-3 text-xs font-bold text-secondary-foreground"
                    >
                      Cancel
                    </button>
                  </div>
                </li>
              ) : (
                <li
                  key={r.id}
                  className="flex items-center justify-between gap-2 rounded-lg bg-background px-3 py-2 text-sm"
                >
                  <span className="truncate">
                    {r.subject} — due {formatDateTime(r.due_at)}
                  </span>
                  <span className="flex shrink-0 items-center gap-1">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        REMINDER_STATUS_STYLE[r.status] ?? "bg-secondary text-secondary-foreground"
                      }`}
                    >
                      {r.status}
                    </span>
                    <button
                      type="button"
                      onClick={() => startEdit(r)}
                      disabled={actionBusyId === r.id}
                      className="rounded-md px-1.5 py-0.5 text-xs disabled:opacity-50"
                      aria-label="Edit reminder"
                    >
                      ✎
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteReminder(r.id)}
                      disabled={actionBusyId === r.id}
                      className="rounded-md px-1.5 py-0.5 text-xs disabled:opacity-50"
                      aria-label="Delete reminder"
                    >
                      🗑
                    </button>
                    {r.status !== "acknowledged" && (
                      <button
                        type="button"
                        onClick={() => acknowledgeReminder(r.id)}
                        disabled={actionBusyId === r.id}
                        className="rounded-md px-1.5 py-0.5 text-xs disabled:opacity-50"
                        aria-label="Mark acknowledged"
                      >
                        ✓
                      </button>
                    )}
                  </span>
                </li>
              )
            )}
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

          <div className="mt-4 border-t border-border pt-3">
            <h3 className="text-sm font-bold text-muted-foreground">Notifications</h3>
            <ul className="mt-2 flex flex-col gap-1.5">
              {[...notifications].reverse().map((n, i) => (
                <li
                  key={i}
                  className="flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm text-foreground/85"
                >
                  <span className="flex-1 truncate">{n.message}</span>
                  <span className="shrink-0 text-xs text-muted-foreground">{formatTime(n.at)}</span>
                </li>
              ))}
              {notifications.length === 0 && (
                <li className="px-2.5 py-1.5 text-sm text-muted-foreground">No notifications yet.</li>
              )}
            </ul>
          </div>
        </section>
        </div>
      </div>
    </main>
  );
}
