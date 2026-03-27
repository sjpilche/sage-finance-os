interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between pb-4 mb-6 border-b border-[var(--border)]">
      <div className="mb-3 sm:mb-0">
        <h1 className="text-3xl font-bold tracking-tight text-[var(--text)]">{title}</h1>
        {subtitle && <p className="text-sm text-[var(--text-secondary)] mt-0.5">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}
