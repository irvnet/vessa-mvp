import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";

/* Two people arrive here, not three. Rose has one door and it is the page; the care
   team's doors are for someone comfortable with a screen. The old layout gave all
   three equal weight, which read as a router rather than a front door — and set
   16px body text on the one product whose user has failing eyesight and memory. */

const CARE_TEAM = [
  {
    href: "/care-team",
    title: "Care Team",
    description: "Reminders, today's activity, and what Vessa noticed.",
  },
  {
    href: "/proof",
    title: "Proof",
    description: "Eval results and guardrail activity, live.",
  },
];

export default function RootPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center bg-background px-5 py-14">
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-3xl">
        <header className="text-center motion-safe:animate-in motion-safe:fade-in">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-marigold">
            A companion that remembers
          </p>
          <h1 className="mt-4 font-heading text-6xl font-black tracking-tight text-clay sm:text-8xl">
            Vessa
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-muted-foreground sm:text-2xl">
            Something to hold what matters — and remember to bring it back.
          </p>
        </header>

        {/* The vessel: Rose's door. Primary by size and by the weight of its edge, not
            by filling it in — a saturated block that large fights the calm the rest of
            the product is built around. */}
        <Link
          href="/companion"
          className="vessel-shape group mt-12 flex items-center gap-6 border-2 border-clay bg-clay-soft/15 px-8 py-9 shadow-sm transition-colors hover:bg-clay-soft/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-4 focus-visible:ring-offset-background sm:px-12 sm:py-11 motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-3"
        >
          <span className="flex-1">
            <span className="block font-heading text-3xl font-extrabold text-clay sm:text-4xl">
              Talk to Vessa
            </span>
            <span className="mt-2 block text-base leading-snug text-muted-foreground sm:text-lg">
              It remembers what matters, and checks in on its own.
            </span>
          </span>
          <ArrowRight className="size-8 shrink-0 text-clay transition-transform motion-safe:group-hover:translate-x-1" />
        </Link>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {CARE_TEAM.map((d) => (
            <Link
              key={d.href}
              href={d.href}
              className="vessel-shape-sm border border-border bg-card px-6 py-6 transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <span className="block font-heading text-xl font-extrabold text-clay">
                {d.title}
              </span>
              <span className="mt-1.5 block text-base leading-snug text-muted-foreground">
                {d.description}
              </span>
            </Link>
          ))}
        </div>

        <p className="mt-10 text-center">
          <Link
            href="/about"
            className="rounded-full text-base font-bold text-clay hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            About Vessa &amp; the story →
          </Link>
        </p>
      </div>
    </main>
  );
}
