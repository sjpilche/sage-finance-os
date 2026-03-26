import type { Metadata } from "next";
import "./globals.css";

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
          {/* Sidebar */}
          <nav className="w-64 bg-slate-900 text-white p-4 flex flex-col gap-1">
            <div className="text-lg font-bold text-teal-400 mb-6 px-2">
              Sage Finance OS
            </div>

            <NavLink href="/" label="Dashboard" />
            <NavLink href="/connections" label="Connections" />
            <NavLink href="/sync" label="Sync Runs" />

            <div className="text-xs text-slate-500 uppercase mt-4 mb-1 px-2">Data</div>
            <NavLink href="/data/gl" label="General Ledger" />
            <NavLink href="/data/tb" label="Trial Balance" />
            <NavLink href="/data/ap" label="Accounts Payable" />
            <NavLink href="/data/ar" label="Accounts Receivable" />

            <div className="text-xs text-slate-500 uppercase mt-4 mb-1 px-2">Financials</div>
            <NavLink href="/financials/pl" label="Income Statement" />
            <NavLink href="/financials/bs" label="Balance Sheet" />

            <div className="text-xs text-slate-500 uppercase mt-4 mb-1 px-2">Analysis</div>
            <NavLink href="/analysis/aging" label="AR/AP Aging" />
            <NavLink href="/analysis/variance" label="Variance" />
            <NavLink href="/analysis/profitability" label="Profitability" />

            <div className="text-xs text-slate-500 uppercase mt-4 mb-1 px-2">Operations</div>
            <NavLink href="/quality" label="Quality" />
            <NavLink href="/close" label="Period Close" />
            <NavLink href="/settings" label="Settings" />
          </nav>

          {/* Main content */}
          <main className="flex-1 bg-slate-50 p-6 overflow-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="px-2 py-1.5 rounded text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
    >
      {label}
    </a>
  );
}
