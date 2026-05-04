import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChangeTools — Obsidian Group",
  description:
    "Agentic AI workflow that turns change-programme materials into a structured brief and slide deck.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
