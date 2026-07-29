import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import "./globals.css";

// One family, used with real range (400/600/800/900) across both display and
// body — a deliberate minimal choice, not a serif+sans pairing. Rounded sans
// reads warm and approachable and stays highly legible at the large sizes
// Rose's companion screen needs.
const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin"],
  weight: ["400", "600", "700", "800", "900"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vessa",
  description: "A companion that remembers — and a calm view for the people who care about her.",
};

// Apply the saved (or system) theme before paint to avoid a flash.
const themeInit = `(function(){try{var t=localStorage.getItem('theme');var d=t?t==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;if(d)document.documentElement.classList.add('dark');}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${nunito.variable} h-full`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
