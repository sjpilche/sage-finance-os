import type { Metadata } from "next";
import "./globals.css";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { ToastProvider } from "@/components/ui/Toast";
import { ThemeProvider } from "@/components/ui/ThemeToggle";

export const metadata: Metadata = {
  title: {
    default: "Sage Finance OS",
    template: "%s | Sage Finance OS",
  },
  description: "Finance intelligence platform that ingests from Sage Intacct and creates a trusted decision system. 43 API endpoints, 6-dimension quality gate, real-time analytics.",
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    title: "Sage Finance OS",
    description: "Finance intelligence platform for Sage Intacct — ETL pipeline, trust scoring, and analytics dashboard.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <ToastProvider>
            <LayoutShell>{children}</LayoutShell>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
