import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ImpactLens AI",
  description: "Evidence-backed test plans for every code change.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
