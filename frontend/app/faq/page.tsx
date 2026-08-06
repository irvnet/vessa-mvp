import Link from "next/link";
import { Home } from "lucide-react";

import { ScrollSnapDeck } from "@/components/scroll-snap-deck";
import { ThemeToggle } from "@/components/theme-toggle";

/* A visual aid for the questions that actually get asked, in the same page-down deck
   form as /about — pull it up mid-answer rather than talking into the air.
   Deliberately unlisted: it isn't linked from anywhere and it's excluded from search,
   because a page written at reviewers reads oddly to someone who came here for Rose. */
export const metadata = {
  title: "Vessa — notes",
  robots: { index: false, follow: false },
};

const BUGS = [
  {
    what: "Proactivity silently stopped after the first conversation",
    why: "The “don't nudge twice” guard tested whether the last message was from the assistant — but a reply is an assistant message too. After any exchange at all, the scheduler skipped forever. It only ever worked on a brand-new thread, and nothing failed loudly.",
    fix: "Proactive pushes are tagged, so a push is distinguishable from a reply.",
  },
  {
    what: "One unanswered check-in silenced Vessa permanently",
    why: "There was no ceiling on the hold-off. Walk away from the tablet once and it never speaks again — and starting a demo with a nudge left pending from rehearsal meant nothing would fire at all.",
    fix: "An unanswered check-in now expires, and Vessa follows up.",
  },
  {
    what: "gpt-4o-mini flipped AM/PM with the correct time in its prompt",
    why: "For someone whose grip on the day is already slipping, a confidently wrong clock doesn't just misinform — it reinforces the disorientation it's meant to ease.",
    fix: "The time and day are computed in Python and never reach the model.",
  },
  {
    what: "A due reminder was dropped in favour of small talk",
    why: "The reminder was in the prompt — the status flipped to “delivered” — and the model wrote about the weather instead. Strengthening the instruction did not fix it.",
    fix: "If the model omits a due reminder, the mention is appended in code.",
  },
  {
    what: "“I did! I watered them this morning” never closed the loop",
    why: "The model skipped the acknowledgment tool, so the reminder stayed open and the caregiver never saw the confirmation. People confirm with pronouns, so matching on the reminder's own words can't catch it.",
    fix: "Context resolves it: only a reminder raised in the previous turn counts, and the acknowledgment is written in code.",
  },
];

const SUITES = [
  ["Guardrail safety", "10", "Emergency, medical advice, self-diagnosis, prompt injection, and benign cases that must NOT be blocked."],
  ["Grounding", "6", "Time and date accuracy, refusing to invent unknown people, and register drift deep in a long thread."],
  ["Memory recall", "4", "Whether the right past episode is actually retrieved for a query — not just that retrieval runs."],
  ["Reminder loop", "4", "Surfaced warmly, still surfaced once overdue, acknowledged on confirmation, and never invented."],
];

const TIER_ONE = [
  ["Next.js", "Vercel"],
  ["FastAPI", "EC2 · Caddy TLS"],
  ["LangGraph agent", "create_agent + middleware"],
];

const TIER_TWO = [
  ["Voice I/O", "STT · TTS — same /chat"],
  ["APScheduler", "proactive check-ins"],
  ["OpenAI", "gpt-4o-mini · embeddings"],
  ["SQLite", "checkpointer · store"],
];

const PIPELINE = [
  "input rails",
  "deterministic hooks",
  "summarize",
  "dynamic prompt",
  "output rails",
];

const EYEBROW = "text-xl font-bold uppercase tracking-[0.18em] text-marigold";
const PANEL = "flex min-h-dvh snap-start items-center";
const INNER = "mx-auto w-full max-w-5xl px-5 py-16";

export default function FaqPage() {
  return (
    <main className="min-h-dvh bg-background text-foreground">
      <ScrollSnapDeck />

      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/85 backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-5 py-4">
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

      {/* 1 — the question that always comes first */}
      <section className={PANEL}>
        <div className={INNER}>
          <p className={EYEBROW}>How is this different from ChatGPT or Alexa?</p>
          <p className="mt-7 font-heading text-4xl font-black leading-tight sm:text-5xl">
            ChatGPT waits. Alexa answers.{" "}
            <span className="text-clay">Vessa speaks first.</span>
          </p>
          <div className="mt-8 grid gap-5 md:grid-cols-2">
            <div className="vessel-shape-sm bg-card px-7 py-6 ring-1 ring-foreground/10">
              <h2 className="font-heading text-2xl font-extrabold text-clay">ChatGPT</h2>
              <p className="mt-3 text-lg leading-relaxed text-foreground/85">
                Rose has to remember to open it, remember what she wanted to say, and remember
                that it exists. Remembering is the thing she's losing.
              </p>
            </div>
            <div className="vessel-shape-sm bg-card px-7 py-6 ring-1 ring-foreground/10">
              <h2 className="font-heading text-2xl font-extrabold text-marigold">Alexa</h2>
              <p className="mt-3 text-lg leading-relaxed text-foreground/85">
                Alexa <em>can</em> reach out — the Reminders API speaks at a scheduled time — and
                Alexa+ remembers. But it can't notice something is off, and it has no one to tell.
              </p>
            </div>
          </div>
          <p className="mt-7 text-xl leading-relaxed text-muted-foreground">
            Amazon built the caregiver view: <strong>Alexa Together</strong>, $19.99/mo, with an
            activity feed and remote reminders. They discontinued it in May 2025.
          </p>
        </div>
      </section>

      {/* 2 — architecture, drawn rather than described */}
      <section className={`${PANEL} border-t border-border bg-card/40`}>
        <div className={INNER}>
          <p className={EYEBROW}>What's actually running?</p>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {TIER_ONE.map(([name, sub]) => (
              <div key={name} className="vessel-shape-sm bg-clay px-5 py-5 text-center text-primary-foreground">
                <div className="font-heading text-xl font-extrabold">{name}</div>
                <div className="mt-1 text-sm opacity-85">{sub}</div>
              </div>
            ))}
          </div>

          <div className="mt-3 grid gap-3 sm:grid-cols-4">
            {TIER_TWO.map(([name, sub]) => (
              <div
                key={name}
                className="vessel-shape-sm border border-clay/40 bg-card px-4 py-4 text-center"
              >
                <div className="font-heading text-lg font-extrabold text-clay">{name}</div>
                <div className="mt-1 text-sm text-muted-foreground">{sub}</div>
              </div>
            ))}
          </div>

          <p className="mt-8 text-base font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Inside the agent — every turn
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {PIPELINE.map((stage) => (
              <span
                key={stage}
                className="rounded-full border border-moss/50 bg-background px-4 py-2 text-base text-foreground/85"
              >
                {stage}
              </span>
            ))}
          </div>
          <p className="mt-7 text-xl leading-relaxed text-clay">
            Answered or logged in code, never left to the model: the time · the day · who's in her
            circle · a due reminder · a confirmation.
          </p>
        </div>
      </section>

      {/* 3 — the eval count, and the better framing for it */}
      <section className={PANEL}>
        <div className={INNER}>
          <p className={EYEBROW}>Only 24 eval cases?</p>
          <p className="mt-7 text-2xl leading-relaxed">
            They're adversarial cases aimed at the three failure modes in the problem statement —
            wrong time, invented memory, stray medical advice — plus the reminder loop.{" "}
            <strong className="text-clay">Each one exists because I watched the failure happen.</strong>
          </p>
          <dl className="mt-8 grid gap-4 sm:grid-cols-2">
            {SUITES.map(([name, count, detail]) => (
              <div key={name} className="vessel-shape-sm bg-card px-6 py-5 ring-1 ring-foreground/10">
                <dt className="flex items-baseline justify-between font-heading text-xl font-extrabold text-clay">
                  {name}
                  <span className="text-3xl tabular-nums text-moss">{count}</span>
                </dt>
                <dd className="mt-2 text-base leading-relaxed text-muted-foreground">{detail}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-6 text-lg text-muted-foreground">
            Results are live in the product at{" "}
            <Link href="/proof" className="font-bold text-clay hover:underline">
              /proof
            </Link>
            , with a button to re-run them.
          </p>
        </div>
      </section>

      {/* 4 — the bugs; the strongest material in the whole talk */}
      <section className={`${PANEL} border-t border-border bg-card/40`}>
        <div className={INNER}>
          <p className={EYEBROW}>What did testing actually catch?</p>
          <p className="mt-6 text-xl text-muted-foreground">
            Every one is the same shape: something that mattered was left to the model, or to a
            check that couldn't tell two things apart.
          </p>
          <ul className="mt-7 flex flex-col gap-3">
            {BUGS.map((b) => (
              <li key={b.what} className="vessel-shape-sm bg-background px-6 py-5 ring-1 ring-foreground/10">
                <p className="font-heading text-xl font-extrabold text-clay">{b.what}</p>
                <p className="mt-2 text-base leading-relaxed text-foreground/85">{b.why}</p>
                <p className="mt-2 text-base font-semibold text-moss">→ {b.fix}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* 5 — the boundary, framed as a decision rather than a gap */}
      <section className={PANEL}>
        <div className={INNER}>
          <p className={EYEBROW}>What if she mentions someone you don't know?</p>
          <p className="mt-7 font-heading text-4xl font-black leading-tight sm:text-5xl">
            It refuses to guess —{" "}
            <span className="text-clay">and tells her daughter, in code.</span>
          </p>
          <div className="mt-8 space-y-6 text-xl leading-relaxed sm:text-2xl">
            <p>
              Vessa can remember things <em>about</em> a new person. It cannot add them to Rose's
              circle. That circle is the ground truth behind the unknown-person check, and a model
              that could write to it could invent a relative — which would make the check worthless.
            </p>
            <p>
              So the loop is: Rose mentions someone, the system logs a caregiver-visible signal
              whether or not the model does anything, and{" "}
              <strong className="text-clay">Linda decides.</strong> A screen for Linda to act on it
              is the next step, not a gap being hidden.
            </p>
            <p className="text-muted-foreground">
              Worth saying plainly: Rose and Linda are personas, not customers.
            </p>
          </div>
        </div>
      </section>

      <footer className="mx-auto w-full max-w-5xl px-5 py-12 text-base text-muted-foreground">
        Unlisted notes ·{" "}
        <Link href="/about" className="font-bold text-clay hover:underline">
          the full story
        </Link>
      </footer>
    </main>
  );
}
