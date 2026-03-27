import type { Metadata } from "next";
import "./globals.css";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { ToastProvider } from "@/components/ui/Toast";
import { ThemeProvider } from "@/components/ui/ThemeToggle";

export const metadata: Metadata = {
  title: "Sage Finance OS",
  description: "Finance intelligence platform for Sage Intacct",
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
