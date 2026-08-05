"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Home, Mic, Square, Volume2, VolumeX } from "lucide-react";

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
  const scrollRef = useRef<HTMLDivElement>(null);
  // A send optimistically appends the user turn and then the bot reply; the poll
  // reconciles against messages.length. If a poll lands in the window between the
  // backend committing the reply and /chat resolving here, it would append the
  // same reply a second time (no ids to dedup on). Skip polling while a send is
  // in flight — the next poll after it settles reconciles cleanly.
  const sendingRef = useRef(false);
  // Voice (preview): push-to-talk mic → /voice/transcribe → the SAME send() → and,
  // when voice is on, the reply is spoken via /voice/speak. Guardrails intact —
  // voice is just I/O around the existing /chat.
  const [voiceOn, setVoiceOn] = useState(false);
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/history?thread_id=${THREAD_ID}`)
      .then((r) => r.json())
      .then((data: Message[]) => setMessages(data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      if (sendingRef.current) return;
      try {
        const res = await fetch(
          `${API_URL}/poll?thread_id=${THREAD_ID}&known_count=${messages.length}`
        );
        const data = await res.json();
        if (!sendingRef.current && data.new_messages?.length) {
          setMessages((prev) => [...prev, ...data.new_messages]);
        }
      } catch {
        // transient poll errors aren't worth surfacing to Rose
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [messages.length]);

  useEffect(() => {
    // Scroll only the conversation container to the bottom — never the window.
    // (scrollIntoView would scroll every scrollable ancestor, including the page
    // itself, which pushed the header off-screen as the chat grew.)
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  async function send(textOverride?: string): Promise<string | undefined> {
    const text = (textOverride ?? input).trim();
    if (!text || sending) return;
    setInput("");
    sendingRef.current = true;
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
      return data.response as string;
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: "I didn't quite catch that — could you try again?" },
      ]);
      return undefined;
    } finally {
      sendingRef.current = false;
      setSending(false);
    }
  }

  async function speak(text: string) {
    try {
      const res = await fetch(`${API_URL}/voice/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) return;
      audioRef.current?.pause(); // never stack two replies
      const url = URL.createObjectURL(await res.blob());
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => URL.revokeObjectURL(url);
      await audio.play();
    } catch {
      // audio is a bonus — never let it break the conversation
    }
  }

  async function submitText(text: string) {
    const reply = await send(text);
    if (voiceOn && reply) speak(reply);
  }

  async function toggleRecording() {
    if (recording) {
      mediaRecorderRef.current?.stop();
      return;
    }
    audioRef.current?.pause(); // tap-to-interrupt: talking over Vessa stops her mid-reply
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => e.data.size && chunksRef.current.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size < 2000) return; // too short/empty — nothing worth transcribing
        const fd = new FormData();
        fd.append("file", blob, "audio.webm");
        try {
          const res = await fetch(`${API_URL}/voice/transcribe`, { method: "POST", body: fd });
          const { text } = await res.json();
          if (text?.trim()) await submitText(text);
        } catch {
          // transcription hiccup — user can just type instead
        }
      };
      mediaRecorderRef.current = mr;
      mr.start();
      setRecording(true);
    } catch {
      // mic permission denied — voice stays optional, text still works
      setRecording(false);
    }
  }

  return (
    <main className="flex h-dvh flex-col items-center overflow-hidden bg-background">
      <div className="flex min-h-0 w-full max-w-2xl flex-1 flex-col px-4">
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

        <div ref={scrollRef} className="min-h-0 flex-1 space-y-5 overflow-y-auto pb-4">
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
        </div>

        <div className="py-6">
          <div className="mb-2 flex justify-center">
            <button
              type="button"
              onClick={() => setVoiceOn((v) => !v)}
              aria-pressed={voiceOn}
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                voiceOn
                  ? "bg-clay text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
            >
              {voiceOn ? <Volume2 className="size-3.5" /> : <VolumeX className="size-3.5" />}
              Voice {voiceOn ? "on" : "off"} <span className="opacity-60">· preview</span>
            </button>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submitText(input);
            }}
            className="flex gap-3"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Hi Rose, how are you?"
              disabled={sending}
              aria-label="Talk to Vessa"
              className="h-16 flex-1 rounded-full bg-card px-6 text-xl"
            />
            {voiceOn && (
              <Button
                type="button"
                variant={recording ? "default" : "secondary"}
                onClick={toggleRecording}
                disabled={sending}
                aria-label={recording ? "Stop and send" : "Hold to talk"}
                className={`h-16 w-16 shrink-0 rounded-full p-0 ${
                  recording ? "bg-marigold text-primary-foreground motion-safe:animate-pulse" : ""
                }`}
              >
                {recording ? <Square className="size-6" /> : <Mic className="size-6" />}
              </Button>
            )}
            <Button
              type="submit"
              disabled={sending}
              className="h-16 shrink-0 rounded-full px-8 text-xl font-bold"
            >
              Send
            </Button>
          </form>
        </div>
      </div>
    </main>
  );
}
