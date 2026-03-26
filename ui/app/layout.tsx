import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";

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
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 bg-slate-50 p-6 overflow-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
