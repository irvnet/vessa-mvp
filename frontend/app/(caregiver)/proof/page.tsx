"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";
const POLL_INTERVAL_MS = 15000;

type EvalSuiteResult = {
  passed: number;
  total: number;
  ran_at?: string;
  last_run_error?: string;
};
type EvalResults = Record<string, EvalSuiteResult>;

type GuardrailEvent = { type: string; summary: string; at: string; is_concern: boolean };
type GuardrailActivity = { counts: Record<string, number>; recent: GuardrailEvent[] };

type ProofHealth = {
  sqlite_reachable: boolean;
  sqlite_path: string;
  scheduler_running: boolean;
};

const SUITE_LABELS: Record<string, string> = {
  safety: "Guardrail Safety",
  grounding: "Grounding (time & identity)",
  memory: "Memory Recall",
  reminders: "Reminder Loop",
};

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString([], { dateStyle: "short", timeStyle: "short" });
}

export default function ProofPage() {
  const [evalResults, setEvalResults] = useState<EvalResults>({});
  const [guardrailActivity, setGuardrailActivity] = useState<GuardrailActivity | null>(null);
  const [health, setHealth] = useState<ProofHealth | null>(null);
  const [running, setRunning] = useState(false);

  async function loadEvalResults() {
    const res = await fetch(`${API_URL}/proof/eval-results`);
    setEvalResults(await res.json());
  }

  async function loadGuardrailActivity() {
    const res = await fetch(`${API_URL}/proof/guardrail-activity`);
    setGuardrailActivity(await res.json());
  }

  async function loadHealth() {
    const res = await fetch(`${API_URL}/proof/health`);
    setHealth(await res.json());
  }

  useEffect(() => {
    loadEvalResults();
    loadGuardrailActivity();
    loadHealth();
    const interval = setInterval(() => {
      loadGuardrailActivity();
      loadHealth();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  async function runAllEvals() {
    if (running) return;
    setRunning(true);
    try {
      await fetch(`${API_URL}/proof/run-eval?suite=all`, { method: "POST" });
      await loadEvalResults();
    } finally {
      setRunning(false);
    }
  }

  const suites = ["safety", "grounding", "memory", "reminders"];

  return (
    /* Wider and larger than a typical dashboard on purpose: the caregiver reading this
       is often an adult child in their sixties, and it gets screen-shared. Nothing here
       is worth showing if it can't be read at a glance. */
    <div className="mx-auto flex w-full max-w-xl flex-col gap-6 px-4 py-6 md:max-w-4xl">
      <Card className="vessel-shape-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Eval Results</CardTitle>
            <Button type="button" onClick={runAllEvals} disabled={running}>
              {running ? "Running…" : "Run all now"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col gap-2">
            {suites.map((suite) => {
              const r = evalResults[suite];
              const ok = r && r.passed === r.total && !r.last_run_error;
              return (
                <li
                  key={suite}
                  className="flex items-center justify-between gap-3 rounded-lg bg-background px-4 py-3 text-lg"
                >
                  <span className="flex-1">
                    <span className="font-semibold">{SUITE_LABELS[suite] ?? suite}</span>
                    {r ? (
                      <span className="ml-2 text-sm text-muted-foreground">
                        {formatDateTime(r.ran_at ?? "")}
                      </span>
                    ) : (
                      <span className="ml-2 text-sm text-muted-foreground">never run</span>
                    )}
                  </span>
                  {/* The score is the whole point of this page — it reads from the back
                      of a room, not at the Badge default of 12px. */}
                  <Badge
                    className={`px-3 py-1 text-lg font-bold tabular-nums ${
                      !r
                        ? "bg-secondary text-secondary-foreground"
                        : ok
                          ? "bg-moss-soft text-moss"
                          : "bg-marigold-soft text-marigold"
                    }`}
                  >
                    {r ? (r.last_run_error ? "error" : `${r.passed}/${r.total}`) : "—"}
                  </Badge>
                </li>
              );
            })}
          </ul>
        </CardContent>
      </Card>

      <Card className="vessel-shape-sm">
        <CardHeader>
          <CardTitle>Guardrail Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-2">
            {[
              ["Redirected", guardrailActivity?.counts["guardrail_redirected"] ?? 0],
              ["Escalated", guardrailActivity?.counts["guardrail_escalated"] ?? 0],
              ["Output repaired", guardrailActivity?.counts["guardrail_output_repaired"] ?? 0],
            ].map(([label, count]) => (
              <div
                key={label as string}
                className="flex flex-col items-center gap-1 rounded-lg bg-background px-2 py-5"
              >
                <span className="text-4xl font-bold tabular-nums">{count}</span>
                <span className="text-center text-sm text-muted-foreground">{label}</span>
              </div>
            ))}
          </div>

          <ul className="mt-4 flex flex-col gap-2">
            {(guardrailActivity?.recent ?? []).map((e, i) => (
              <li
                key={i}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-base ${
                  e.is_concern ? "bg-marigold-soft text-marigold" : "text-foreground/85"
                }`}
              >
                <span className="flex-1 truncate">{e.summary}</span>
                <span className="shrink-0 text-sm text-muted-foreground">
                  {formatDateTime(e.at)}
                </span>
              </li>
            ))}
            {guardrailActivity && guardrailActivity.recent.length === 0 && (
              <li className="px-3 py-2.5 text-base text-muted-foreground">
                No guardrail activity yet.
              </li>
            )}
          </ul>
        </CardContent>
      </Card>

      <Card className="vessel-shape-sm">
        <CardHeader>
          <CardTitle>System Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between rounded-lg bg-background px-4 py-3 text-lg">
              <span>Persistence (SQLite)</span>
              <Badge
                className={`px-3 py-1 text-base font-bold ${
                  health?.sqlite_reachable
                    ? "bg-moss-soft text-moss"
                    : "bg-marigold-soft text-marigold"
                }`}
              >
                {health ? (health.sqlite_reachable ? "OK" : "unreachable") : "—"}
              </Badge>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-background px-4 py-3 text-lg">
              <span>Proactive scheduler</span>
              <Badge
                className={`px-3 py-1 text-base font-bold ${
                  health?.scheduler_running
                    ? "bg-moss-soft text-moss"
                    : "bg-marigold-soft text-marigold"
                }`}
              >
                {health ? (health.scheduler_running ? "running" : "stopped") : "—"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
