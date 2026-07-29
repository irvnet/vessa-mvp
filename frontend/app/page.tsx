import Link from "next/link";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const DESTINATIONS = [
  { href: "/companion", title: "Talk to Vessa", description: "The companion chat — Rose's view." },
  { href: "/care-team", title: "Care Team", description: "Reminders, today's activity, notifications." },
  { href: "/proof", title: "Proof", description: "Eval results and guardrail activity." },
];

export default function RootPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-8 bg-background px-4">
      <div className="text-center">
        <h1 className="font-heading text-4xl font-extrabold text-clay">Vessa</h1>
        <p className="mt-2 text-muted-foreground">
          A companion that remembers — and a calm view for the people who care about her.
        </p>
      </div>
      <div className="grid w-full max-w-2xl gap-4 sm:grid-cols-3">
        {DESTINATIONS.map((d) => (
          <Link key={d.href} href={d.href}>
            <Card className="vessel-shape-sm h-full transition-shadow hover:shadow-md">
              <CardHeader>
                <CardTitle>{d.title}</CardTitle>
                <CardDescription>{d.description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </main>
  );
}
