"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { Moon, Sun } from "lucide-react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({ theme: "light", toggle: () => {} });

export function useTheme() {
  return useContext(ThemeContext);
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("sage-theme") as Theme | null;
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initial = stored || (prefersDark ? "dark" : "light");
    setTheme(initial);
    document.documentElement.classList.toggle("dark", initial === "dark");
    setMounted(true);
  }, []);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next = prev === "light" ? "dark" : "light";
      localStorage.setItem("sage-theme", next);
      document.documentElement.classList.toggle("dark", next === "dark");
      return next;
    });
  }, []);

  if (!mounted) return <>{children}</>;

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme();

  return (
    <button
      onClick={toggle}
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      className="p-2 rounded-lg hover:bg-slate-800/70 text-slate-400 hover:text-slate-200 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-teal-400/30 focus:ring-inset"
    >
      {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
    </button>
  );
}
