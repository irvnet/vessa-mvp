import { AppShell } from "@/components/app-shell";

export default function CaregiverLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
