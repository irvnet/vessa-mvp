"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Home } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ThemeToggle } from "@/components/theme-toggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";
// Must match app.scheduler.companion_thread_id("team-rose") on the backend —
// one stable, ongoing thread per receiver, not a fresh one per page load.
const THREAD_ID = "companion-team-rose";
const POLL_INTERVAL_MS = 15000;

type Message = { role: "user" | "bot"; content: string };

export default function CompanionPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API_URL}/history?thread_id=${THREAD_ID}`)
      .then((r) => r.json())
      .then((data: Message[]) => setMessages(data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(
          `${API_URL}/poll?thread_id=${THREAD_ID}&known_count=${messages.length}`
        );
        const data = await res.json();
        if (data.new_messages?.length) {
          setMessages((prev) => [...prev, ...data.new_messages]);
        }
      } catch {
        // transient poll errors aren't worth surfacing to Rose
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [messages.length]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: THREAD_ID, message: text }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "bot", content: data.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: "I didn't quite catch that — could you try again?" },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="flex h-dvh flex-col items-center bg-background">
      <div className="flex w-full max-w-2xl flex-1 flex-col px-4">
        <header className="relative flex items-center justify-center py-6">
          <Link
            href="/"
            className="absolute left-0 rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Back to home"
          >
            <Home className="size-5" />
          </Link>
          <h1 className="font-heading text-2xl font-extrabold text-clay">Vessa</h1>
          <div className="absolute right-0">
            <ThemeToggle />
          </div>
        </header>

        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto pb-4">
          {messages.map((m, i) =>
            m.role === "bot" ? (
              <div
                key={i}
                className="vessel-shape max-w-[85%] bg-card px-6 py-5 text-2xl leading-snug text-card-foreground shadow-sm ring-1 ring-clay/15 motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2"
              >
                {m.content}
              </div>
            ) : (
              <div
                key={i}
                className="ml-auto max-w-[80%] rounded-2xl bg-secondary px-5 py-4 text-xl leading-snug text-secondary-foreground"
              >
                {m.content}
              </div>
            )
          )}
          <div ref={bottomRef} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex gap-3 py-6"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Good morning..."
            disabled={sending}
            aria-label="Talk to Vessa"
            className="h-16 flex-1 rounded-full bg-card px-6 text-xl"
          />
          <Button
            type="submit"
            disabled={sending}
            className="h-16 shrink-0 rounded-full px-8 text-xl font-bold"
          >
            Send
          </Button>
        </form>
      </div>
    </main>
  );
}
