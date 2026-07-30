import Link from "next/link";
import { Home, ArrowUpRight } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";

export const metadata = {
  title: "About Vessa",
  description:
    "A companion for an older adult living with early memory loss — and a calm view for the people caring for her. Built to prove it's trustworthy, not just claim it.",
};

// Verb labels, not 01/02/03 — the three capabilities are parallel, not a
// sequence. Each owns a color from the app's own semantics (moss = calm,
// marigold = the attention signal), so the About page speaks the product's
// visual language back to it.
const CAPABILITIES = [
  {
    verb: "Remembers",
    accent: "text-clay",
    dot: "bg-clay",
    body:
      "Vessa carries a real profile of who Rose is, holds onto what she mentions from one conversation to the next, and — through an actual scheduler — checks in on her first, unprompted. Not a chatbot waiting to be spoken to.",
    href: "/companion",
    cta: "Talk to Vessa",
  },
  {
    verb: "Closes the loop",
    accent: "text-marigold",
    dot: "bg-marigold",
    body:
      "A caregiver sets a reminder. Vessa weaves it into conversation warmly, the way a friend nudges you — never “REMINDER:”. Rose confirms in her own words. The caregiver sees the acknowledgment. One loop, fully closed.",
    href: "/care-team",
    cta: "See the Care Team view",
  },
  {
    verb: "Keeps the caregiver close",
    accent: "text-moss",
    dot: "bg-moss",
    body:
      "A calm “Today” — check-ins, reminders, and the occasional gentle signal worth a caregiver's attention — mostly a byproduct of the companion's own day. A window, not a clinical dashboard. No alarm theater.",
    href: "/care-team",
    cta: "See a day at rest",
  },
];

const STACK = [
  ["Agent", "LangGraph create_agent + composable middleware"],
  ["Model", "gpt-4o-mini"],
  ["Memory", "Embedding-based episodic recall"],
  ["Proactivity", "APScheduler — real, scheduled check-ins"],
  ["Persistence", "SQLite — survives restarts"],
  ["Backend", "FastAPI on EC2, Caddy for TLS"],
  ["Frontend", "Next.js on Vercel"],
];

const EXPLORE = [
  { href: "/companion", label: "Talk to Vessa", sub: "The companion chat — Rose's view" },
  { href: "/care-team", label: "Care Team", sub: "Reminders, today's activity, notifications" },
  { href: "/proof", label: "Proof", sub: "Live eval results and guardrail activity" },
];

export default function AboutPage() {
  return (
    <main className="min-h-dvh bg-background text-foreground">
      <header className="mx-auto flex w-full max-w-3xl items-center justify-between px-5 py-5">
        <Link
          href="/"
          className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
          aria-label="Back to home"
        >
          <Home className="size-5" />
        </Link>
        <span className="font-heading text-lg font-extrabold text-clay">Vessa</span>
        <ThemeToggle />
      </header>

      {/* Hero — the thesis: a vessel holds what matters and brings it back. */}
      <section className="mx-auto w-full max-w-3xl px-5 pt-10 pb-16 sm:pt-16">
        <p className="text-sm font-bold uppercase tracking-[0.2em] text-marigold motion-safe:animate-in motion-safe:fade-in">
          A companion that remembers
        </p>
        <h1 className="mt-5 font-heading text-4xl font-black leading-[1.08] tracking-tight sm:text-6xl motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2">
          Something to hold what matters —{" "}
          <span className="text-clay">and remember to bring it back.</span>
        </h1>
        <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
          Vessa is an AI companion for an older adult living with early memory loss, and a
          calm view for the people caring for her. The name is the whole idea: a vessel, something
          that holds and carries.
        </p>
      </section>

      {/* The stakes */}
      <section className="border-t border-border bg-card/40">
        <div className="mx-auto w-full max-w-3xl px-5 py-16">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-muted-foreground">
            Why it has to be trustworthy
          </p>
          <div className="mt-6 space-y-5 text-lg leading-relaxed">
            <p>
              Rose is 84. She lives alone, still independent, with early dementia — the kind where
              the day of the week slips, or a worry loops quietly back around.
            </p>
            <p>
              A companion for someone like Rose can't just <em>sound</em> caring. A wrong time, an
              invented memory, a stray piece of medical advice — here, that isn't a harmless glitch.
              It can reinforce the very disorientation it's meant to ease, and trust, once lost, may
              not come back.
            </p>
            <p className="font-semibold text-clay">
              So Vessa is built to prove it's trustworthy, not just claim it.
            </p>
          </div>
        </div>
      </section>

      {/* What it does — three parallel capabilities */}
      <section className="mx-auto w-full max-w-3xl px-5 py-16">
        <p className="text-sm font-bold uppercase tracking-[0.2em] text-muted-foreground">
          What Vessa does
        </p>
        <div className="mt-8 flex flex-col gap-5">
          {CAPABILITIES.map((c) => (
            <div
              key={c.verb}
              className="vessel-shape-sm bg-card px-6 py-6 ring-1 ring-foreground/10 sm:px-8 sm:py-7"
            >
              <div className="flex items-center gap-2.5">
                <span className={`size-2.5 rounded-full ${c.dot}`} aria-hidden />
                <h2 className={`font-heading text-xl font-extrabold ${c.accent}`}>{c.verb}</h2>
              </div>
              <p className="mt-3 text-base leading-relaxed text-foreground/85 sm:text-lg">{c.body}</p>
              <Link
                href={c.href}
                className="mt-4 inline-flex items-center gap-1 text-sm font-bold text-clay hover:underline"
              >
                {c.cta}
                <ArrowUpRight className="size-4" />
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Proven, not claimed */}
      <section className="border-t border-border bg-card/40">
        <div className="mx-auto w-full max-w-3xl px-5 py-16">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-marigold">
            Proven, not claimed
          </p>
          <div className="mt-6 space-y-5 text-lg leading-relaxed">
            <p>
              Two things back the trust up. <strong>Layered guardrails</strong> keep Vessa on the
              right side of the medical line — fast deterministic checks first, an LLM judgment call
              for the nuance, on both what Rose says and what Vessa is about to say.
            </p>
            <p>
              And where an answer is <strong>computable</strong> — the time, the day, whether someone
              is in Rose's circle — Vessa answers in code, not from the model. A fact shouldn't be
              left to a guess.
            </p>
            <p>
              All of it sits on a real <strong>eval suite</strong>: golden-set tests for safety,
              grounding, and memory, every case traced back to a real bug found in testing. And the
              results aren't buried in a terminal — they're visible live, in the app.
            </p>
          </div>
          <Link
            href="/proof"
            className="mt-8 inline-flex items-center gap-1.5 rounded-full bg-clay px-6 py-3 text-base font-bold text-primary-foreground hover:bg-clay/90"
          >
            See the proof
            <ArrowUpRight className="size-4" />
          </Link>
        </div>
      </section>

      {/* Under the hood */}
      <section className="mx-auto w-full max-w-3xl px-5 py-16">
        <p className="text-sm font-bold uppercase tracking-[0.2em] text-muted-foreground">
          Under the hood
        </p>
        <dl className="mt-8 grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
          {STACK.map(([k, v]) => (
            <div key={k} className="flex flex-col border-t border-border pt-3">
              <dt className="text-xs font-bold uppercase tracking-wider text-marigold">{k}</dt>
              <dd className="mt-1 text-base text-foreground/85">{v}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Explore */}
      <section className="border-t border-border bg-card/40">
        <div className="mx-auto w-full max-w-3xl px-5 py-16">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-muted-foreground">
            See it for yourself
          </p>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
            {EXPLORE.map((e) => (
              <Link
                key={e.href}
                href={e.href}
                className="vessel-shape-sm group flex flex-col bg-card px-5 py-5 ring-1 ring-foreground/10 transition-shadow hover:shadow-md"
              >
                <span className="flex items-center justify-between font-heading text-lg font-extrabold text-clay">
                  {e.label}
                  <ArrowUpRight className="size-4 text-muted-foreground transition-colors group-hover:text-clay" />
                </span>
                <span className="mt-1 text-sm text-muted-foreground">{e.sub}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <footer className="mx-auto w-full max-w-3xl px-5 py-12 text-sm text-muted-foreground">
        Vessa — an AI-engineering capstone. Built to be a companion you could actually trust.
      </footer>
    </main>
  );
}
