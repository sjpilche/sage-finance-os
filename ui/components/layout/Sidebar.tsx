"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Plug,
  RefreshCw,
  BookOpen,
  Scale,
  Receipt,
  FileText,
  TrendingUp,
  BarChart3,
  PieChart,
  Timer,
  ShieldCheck,
  CalendarCheck,
  Settings,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

const iconSize = 16;

const sections: NavSection[] = [
  {
    items: [
      { href: "/", label: "Dashboard", icon: <LayoutDashboard size={iconSize} /> },
      { href: "/connections", label: "Connections", icon: <Plug size={iconSize} /> },
      { href: "/sync", label: "Sync Runs", icon: <RefreshCw size={iconSize} /> },
    ],
  },
  {
    title: "Data",
    items: [
      { href: "/data/gl", label: "General Ledger", icon: <BookOpen size={iconSize} /> },
      { href: "/data/tb", label: "Trial Balance", icon: <Scale size={iconSize} /> },
      { href: "/data/ap", label: "Accounts Payable", icon: <Receipt size={iconSize} /> },
      { href: "/data/ar", label: "Accounts Receivable", icon: <FileText size={iconSize} /> },
    ],
  },
  {
    title: "Financials",
    items: [
      { href: "/financials/pl", label: "Income Statement", icon: <TrendingUp size={iconSize} /> },
      { href: "/financials/bs", label: "Balance Sheet", icon: <BarChart3 size={iconSize} /> },
    ],
  },
  {
    title: "Analysis",
    items: [
      { href: "/analysis/aging", label: "AR/AP Aging", icon: <Timer size={iconSize} /> },
      { href: "/analysis/variance", label: "Variance", icon: <BarChart3 size={iconSize} /> },
      { href: "/analysis/profitability", label: "Profitability", icon: <PieChart size={iconSize} /> },
    ],
  },
  {
    title: "Operations",
    items: [
      { href: "/quality", label: "Quality", icon: <ShieldCheck size={iconSize} /> },
      { href: "/close", label: "Period Close", icon: <CalendarCheck size={iconSize} /> },
      { href: "/settings", label: "Settings", icon: <Settings size={iconSize} /> },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="w-64 bg-slate-900 text-white p-4 flex flex-col gap-0.5 shrink-0">
      <div className="text-lg font-bold text-teal-400 mb-6 px-2">
        Sage Finance OS
      </div>

      {sections.map((section, i) => (
        <div key={i}>
          {section.title && (
            <div className="text-xs text-slate-500 uppercase mt-4 mb-1 px-2">
              {section.title}
            </div>
          )}
          {section.items.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2.5 px-2 py-1.5 rounded text-sm transition-colors",
                  isActive
                    ? "bg-slate-800 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                )}
              >
                <span className={cn("opacity-60", isActive && "opacity-100")}>
                  {item.icon}
                </span>
                {item.label}
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}
