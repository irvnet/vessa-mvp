"use client";

import { useEffect, useState } from "react";
import { Pencil, Trash2, Check } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";
const POLL_INTERVAL_MS = 15000;

type EventItem = { type: string; summary: string; at: string; is_concern: boolean };
type Today = { name: string; status: "ok" | "attention"; summary: string; events: EventItem[] };
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
    <div className="mx-auto flex w-full max-w-xl flex-col gap-6 px-4 py-6 md:max-w-4xl">
      {today?.summary && (
        <Card className="vessel-shape-sm bg-clay-soft/10 ring-1 ring-clay/15">
          <CardContent className="flex items-start justify-between gap-4 py-5">
            <div className="flex-1">
              <p className="text-sm font-bold uppercase tracking-wider text-clay">
                {today.name} today, from Vessa
              </p>
              <p className="mt-2 text-xl leading-relaxed text-foreground">{today.summary}</p>
            </div>
            <Badge
              className={`shrink-0 px-3 py-1 text-base font-bold ${
                today.status === "attention"
                  ? "bg-marigold-soft text-marigold"
                  : "bg-moss-soft text-moss"
              }`}
            >
              {today.status === "attention" ? "⚠️ Needs attention" : "🟢 OK"}
            </Badge>
          </CardContent>
        </Card>
      )}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 md:items-start">
        <Card className="vessel-shape-sm">
          <CardHeader>
            <CardTitle>Reminders</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-2">
              {reminders.map((r) =>
                editingId === r.id ? (
                  <li key={r.id} className="flex flex-col gap-2 rounded-lg bg-background px-3 py-2">
                    <Input value={editSubject} onChange={(e) => setEditSubject(e.target.value)} />
                    <div className="flex gap-2">
                      <Input
                        type="datetime-local"
                        value={editDueAt}
                        onChange={(e) => setEditDueAt(e.target.value)}
                        className="flex-1"
                      />
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => saveEdit(r.id)}
                        disabled={actionBusyId === r.id}
                      >
                        Save
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => setEditingId(null)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </li>
                ) : (
                  <li
                    key={r.id}
                    className="flex items-center justify-between gap-2 rounded-lg bg-background px-4 py-3 text-lg"
                  >
                    <span className="truncate">
                      {r.subject} — due {formatDateTime(r.due_at)}
                    </span>
                    <span className="flex shrink-0 items-center gap-1">
                      <Badge className={`px-2.5 py-1 text-sm font-bold ${REMINDER_STATUS_STYLE[r.status] ?? "bg-secondary text-secondary-foreground"}`}>
                        {r.status}
                      </Badge>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => startEdit(r)}
                        disabled={actionBusyId === r.id}
                        aria-label="Edit reminder"
                      >
                        <Pencil />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => deleteReminder(r.id)}
                        disabled={actionBusyId === r.id}
                        aria-label="Delete reminder"
                      >
                        <Trash2 />
                      </Button>
                      {r.status !== "acknowledged" && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => acknowledgeReminder(r.id)}
                          disabled={actionBusyId === r.id}
                          aria-label="Mark acknowledged"
                        >
                          <Check />
                        </Button>
                      )}
                    </span>
                  </li>
                )
              )}
              {reminders.length === 0 && (
                <li className="px-4 py-3 text-lg text-muted-foreground">No reminders yet.</li>
              )}
            </ul>

            <form onSubmit={addReminder} className="mt-4 flex flex-col gap-2">
              <Input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Take morning vitamins"
              />
              <div className="flex gap-2">
                <Input
                  type="datetime-local"
                  value={dueAt}
                  onChange={(e) => setDueAt(e.target.value)}
                  className="flex-1"
                />
                <Button type="submit" disabled={submitting}>
                  + Add
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card className="vessel-shape-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{today?.name ?? "Rose"} · Today</CardTitle>
              <Badge
                className={`px-3 py-1 text-base font-bold ${
                  today?.status === "attention"
                    ? "bg-marigold-soft text-marigold"
                    : "bg-moss-soft text-moss"
                }`}
              >
                {today?.status === "attention" ? "⚠️ Needs attention" : "🟢 OK"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-1.5">
              {(today?.events ?? []).map((e, i) => (
                <li
                  key={i}
                  className={`flex items-center gap-2 rounded-lg px-3 py-3 text-lg ${
                    e.is_concern ? "bg-marigold-soft text-marigold" : "text-foreground/85"
                  }`}
                >
                  <span>{e.is_concern ? "⚠️" : e.type === "reminder_acknowledged" ? "✓" : "•"}</span>
                  <span className="flex-1 truncate">{e.summary}</span>
                  <span className="shrink-0 text-sm text-muted-foreground">{formatTime(e.at)}</span>
                </li>
              ))}
              {today && today.events.length === 0 && (
                <li className="px-3 py-3 text-lg text-muted-foreground">Nothing yet today.</li>
              )}
            </ul>

            <div className="mt-4 border-t border-border pt-3">
              <h3 className="text-lg font-bold text-muted-foreground">Notifications</h3>
              <ul className="mt-2 flex flex-col gap-1.5">
                {[...notifications].reverse().map((n, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-2 rounded-lg px-3 py-3 text-lg text-foreground/85"
                  >
                    <span className="flex-1 truncate">{n.message}</span>
                    <span className="shrink-0 text-sm text-muted-foreground">{formatTime(n.at)}</span>
                  </li>
                ))}
                {notifications.length === 0 && (
                  <li className="px-3 py-3 text-lg text-muted-foreground">No notifications yet.</li>
                )}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
