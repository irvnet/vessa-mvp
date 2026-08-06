"use client";

import { useCallback, useEffect, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

/** Lets the About page be walked through like a deck: one section per screenful,
 *  with explicit controls to step between them.
 *
 *  Snapping alone wasn't enough — mandatory snap fights trackpad momentum, and
 *  proximity snap is too loose to land cleanly on demand. So the snap tidies up where
 *  a scroll comes to rest (globals.css) and these buttons do the actual stepping, which
 *  also gives keyboard and screen-reader users a real control instead of a scroll gesture.
 *
 *  The class goes on <html> rather than making the page its own scroll container, so
 *  Page Down, Space and the arrow keys keep working as they already do. */
export function ScrollSnapDeck() {
  const [sections, setSections] = useState<HTMLElement[]>([]);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    document.documentElement.classList.add("snap-deck");
    const found = Array.from(document.querySelectorAll<HTMLElement>("main section"));
    setSections(found);

    // Track which section is on screen so the counter and the disabled states stay
    // right however the reader got there — buttons, keyboard, or scrolling.
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) setIndex(found.indexOf(entry.target as HTMLElement));
        }
      },
      { threshold: 0.55 },
    );
    found.forEach((section) => observer.observe(section));

    return () => {
      observer.disconnect();
      document.documentElement.classList.remove("snap-deck");
    };
  }, []);

  const go = useCallback(
    (delta: number) => {
      const target = sections[index + delta];
      if (!target) return;
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      target.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    },
    [sections, index],
  );

  if (sections.length < 2) return null;

  const button =
    "flex size-14 items-center justify-center rounded-full border-2 border-clay bg-card text-clay shadow-sm transition-colors hover:bg-clay-soft/20 disabled:pointer-events-none disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background";

  return (
    <div className="fixed bottom-6 right-5 z-50 flex flex-col items-center gap-1.5 sm:bottom-8 sm:right-8">
      <button
        type="button"
        onClick={() => go(-1)}
        disabled={index === 0}
        aria-label="Previous section"
        className={button}
      >
        <ChevronUp className="size-7" />
      </button>
      <span className="text-base font-bold tabular-nums text-muted-foreground" aria-hidden="true">
        {index + 1}/{sections.length}
      </span>
      <button
        type="button"
        onClick={() => go(1)}
        disabled={index === sections.length - 1}
        aria-label="Next section"
        className={button}
      >
        <ChevronDown className="size-7" />
      </button>
    </div>
  );
}
