import Link from "next/link";
import { ArrowRight, ArrowUpRight, Home } from "lucide-react";

import { ScrollSnapDeck } from "@/components/scroll-snap-deck";
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

// Same doors, same words, same weighting as the landing page — Rose's door is the
// product, the other two are for whoever is looking after her.
const EXPLORE_PRIMARY = {
  href: "/companion",
  label: "Talk to Vessa",
  sub: "It remembers what matters, and checks in on its own.",
};

const EXPLORE_SECONDARY = [
  {
    href: "/care-team",
    label: "Care Team",
    sub: "Reminders, today's activity, and what Vessa noticed.",
  },
  { href: "/proof", label: "Proof", sub: "Eval results and guardrail activity, live." },
];

export default function AboutPage() {
  return (
    <main className="min-h-dvh bg-background text-foreground">
      <ScrollSnapDeck />
      {/* Sticky: every section is a full screenful, so a header that scrolls away with
          the hero strands the reader six panels down with no way home. */}
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/85 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between px-5 py-4">
          <Link
            href="/"
            className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Back to home"
          >
            <Home className="size-6" />
          </Link>
          <span className="font-heading text-xl font-extrabold text-clay">Vessa</span>
          <ThemeToggle />
        </div>
      </header>

      {/* Hero — the thesis: a vessel holds what matters and brings it back. */}
      <section className="mx-auto flex min-h-dvh w-full max-w-3xl snap-start flex-col justify-center px-5 pb-16 pt-4">
        <p className="text-xl font-bold uppercase tracking-[0.18em] text-marigold motion-safe:animate-in motion-safe:fade-in">
          A companion that remembers
        </p>
        <h1 className="mt-5 font-heading text-5xl font-black leading-[1.08] tracking-tight sm:text-7xl motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2">
          Something to hold what matters —{" "}
          <span className="text-clay">and remember to bring it back.</span>
        </h1>
        <p className="mt-7 max-w-2xl text-xl leading-relaxed text-muted-foreground sm:text-2xl">
          Vessa is an AI companion for an older adult living with early memory loss, and a
          calm view for the people caring for her. The name is the whole idea: a vessel, something
          that holds and carries.
        </p>
      </section>

      {/* The stakes */}
      <section className="flex min-h-dvh snap-start items-center border-t border-border bg-card/40">
        <div className="mx-auto w-full max-w-3xl px-5 py-16">
          <p className="text-xl font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Why it has to be trustworthy
          </p>
          <div className="mt-7 space-y-6 text-xl leading-relaxed sm:text-2xl">
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
      {/* Side by side, not stacked: the three are parallel, so showing them in parallel
          is both truer and cuts the section's height by two thirds. Cards stretch to a
          shared height and the links sit on a common baseline, which is what made the
          stacked version read as ragged. */}
      <section className="mx-auto flex min-h-dvh w-full max-w-6xl snap-start flex-col justify-center px-5 py-16">
        <p className="text-xl font-bold uppercase tracking-[0.18em] text-muted-foreground">
          What Vessa does
        </p>
        <div className="mt-8 grid gap-5 md:grid-cols-3">
          {CAPABILITIES.map((c) => (
            <div
              key={c.verb}
              className="vessel-shape-sm flex flex-col bg-card px-6 py-6 ring-1 ring-foreground/10 sm:px-7 sm:py-7"
            >
              <div className="flex items-center gap-2.5">
                <span className={`size-2.5 shrink-0 rounded-full ${c.dot}`} aria-hidden />
                <h2 className={`font-heading text-2xl font-extrabold ${c.accent}`}>{c.verb}</h2>
              </div>
              <p className="mt-3 text-lg leading-relaxed text-foreground/85">{c.body}</p>
              <Link
                href={c.href}
                className="mt-auto inline-flex items-center gap-1.5 pt-5 text-base font-bold text-clay hover:underline"
              >
                {c.cta}
                <ArrowUpRight className="size-4" />
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Proven, not claimed */}
      <section className="flex min-h-dvh snap-start items-center border-t border-border bg-card/40">
        <div className="mx-auto w-full max-w-3xl px-5 py-16">
          <p className="text-xl font-bold uppercase tracking-[0.18em] text-marigold">
            Proven, not claimed
          </p>
          <div className="mt-7 space-y-6 text-xl leading-relaxed sm:text-2xl">
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
              grounding, memory, and the reminder loop, every case traced back to a real bug found
              in testing. And the results aren't buried in a terminal — they're visible live, in
              the app.
            </p>
          </div>
          <Link
            href="/proof"
            className="mt-8 inline-flex items-center gap-1.5 rounded-full bg-clay px-7 py-3.5 text-lg font-bold text-primary-foreground hover:bg-clay/90"
          >
            See the proof
            <ArrowUpRight className="size-4" />
          </Link>
        </div>
      </section>

      {/* Does she know it's an AI? */}
      <section className="mx-auto flex min-h-dvh w-full max-w-3xl snap-start flex-col justify-center px-5 py-16">
        <p className="text-xl font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Does Rose know she's talking to an AI?
        </p>
        <div className="mt-7 space-y-6 text-xl leading-relaxed sm:text-2xl">
          <p>
            <strong>Yes.</strong> Vessa never claims to be a person, never says it&rsquo;s a friend
            or a nurse, and never pretends to have visited. If she asks what it is, it tells her.
          </p>
          <p>
            There is one thing it won&rsquo;t do, and it&rsquo;s deliberate: Rose talks about her
            late husband Walt, sometimes as though he&rsquo;s still here. Vessa doesn&rsquo;t
            correct her. That isn&rsquo;t deception — it&rsquo;s the same judgment a kind visitor
            would make. Honesty about what Vessa <em>is</em> and gentleness about what Rose
            remembers are different questions, and only the first one is about trust.
          </p>
        </div>
      </section>

      {/* Under the hood */}
      <section className="mx-auto flex min-h-dvh w-full max-w-3xl snap-start flex-col justify-center px-5 py-16">
        <p className="text-xl font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Under the hood
        </p>
        <dl className="mt-8 grid grid-cols-1 gap-x-12 gap-y-6 sm:grid-cols-2">
          {STACK.map(([k, v]) => (
            <div key={k} className="flex flex-col border-t border-border pt-4">
              <dt className="text-lg font-bold uppercase tracking-wider text-marigold">{k}</dt>
              <dd className="mt-2 text-2xl text-foreground/85">{v}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Explore */}
      <section className="flex min-h-dvh snap-start items-center border-t border-border bg-card/40">
        <div className="mx-auto w-full max-w-3xl px-5 py-16">
          <p className="text-xl font-bold uppercase tracking-[0.18em] text-muted-foreground">
            See it for yourself
          </p>
          <Link
            href={EXPLORE_PRIMARY.href}
            className="vessel-shape group mt-8 flex items-center gap-6 border-2 border-clay bg-clay-soft/15 px-8 py-9 transition-colors hover:bg-clay-soft/25 sm:px-12"
          >
            <span className="flex-1">
              <span className="block font-heading text-3xl font-extrabold text-clay sm:text-4xl">
                {EXPLORE_PRIMARY.label}
              </span>
              <span className="mt-2 block text-lg leading-snug text-muted-foreground">
                {EXPLORE_PRIMARY.sub}
              </span>
            </span>
            <ArrowRight className="size-8 shrink-0 text-clay transition-transform motion-safe:group-hover:translate-x-1" />
          </Link>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {EXPLORE_SECONDARY.map((e) => (
              <Link
                key={e.href}
                href={e.href}
                className="vessel-shape-sm border border-border bg-card px-6 py-6 transition-shadow hover:shadow-md"
              >
                <span className="block font-heading text-xl font-extrabold text-clay">
                  {e.label}
                </span>
                <span className="mt-1.5 block text-base leading-snug text-muted-foreground">
                  {e.sub}
                </span>
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
