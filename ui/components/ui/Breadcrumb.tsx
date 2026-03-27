import Link from "next/link";
import { ChevronRight } from "lucide-react";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex items-center gap-1.5 text-sm text-[var(--text-tertiary)]">
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-1.5">
            {i > 0 && <ChevronRight size={14} className="text-[var(--text-tertiary)]" />}
            {item.href ? (
              <Link
                href={item.href}
                className="hover:text-[var(--accent)] transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span className="text-[var(--text-secondary)] font-medium">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
