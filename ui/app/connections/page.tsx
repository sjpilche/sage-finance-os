"use client";

import { useState } from "react";
import { useApi, apiMutate } from "@/lib/api/client";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDateTime } from "@/lib/utils";
import { Plug, TestTube, Trash2, Plus, Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import type { Connection } from "@/lib/types/platform";

const statusVariant: Record<string, "success" | "warning" | "danger" | "default"> = {
  active: "success",
  pending: "default",
  failed: "danger",
  disabled: "warning",
};

export default function ConnectionsPage() {
  const { data, error, isLoading, mutate } = useApi<Connection[]>("/v1/connections");
  const [showCreate, setShowCreate] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    sender_id: "",
    sender_password: "",
    company_id: "",
    user_id: "",
    user_password: "",
  });
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);
  const [creating, setCreating] = useState(false);
  const { toast } = useToast();

  const connections = data?.data || [];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const { name, ...creds } = formData;
      await apiMutate("/v1/connections", "POST", { name, credentials: creds });
      setShowCreate(false);
      setFormData({ name: "", sender_id: "", sender_password: "", company_id: "", user_id: "", user_password: "" });
      mutate();
      toast("Connection created successfully", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to create connection", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleTest = async (id: string) => {
    setTesting(id);
    try {
      await apiMutate(`/v1/connections/${id}/test`, "POST");
      mutate();
      toast("Connection test passed", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Connection test failed", "error");
    } finally {
      setTesting(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await apiMutate(`/v1/connections/${deleteTarget.id}`, "DELETE");
      setDeleteTarget(null);
      mutate();
      toast("Connection deleted", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to delete connection", "error");
      setDeleteTarget(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="Connections"
        subtitle="Sage Intacct data source connections"
        actions={
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-[var(--accent)] hover:bg-[var(--accent-darker)] shadow-sm hover:shadow-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25 focus:ring-offset-2"
          >
            <Plus size={16} /> Add Connection
          </button>
        }
      />

      {isLoading && <LoadingState />}
      {error && <ErrorState message={error.message} />}

      {!isLoading && !error && connections.length === 0 && (
        <EmptyState message="No connections configured. Add a Sage Intacct connection to get started." icon={<Plug size={40} strokeWidth={1.5} />} />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {connections.map((conn) => (
          <Card key={conn.connection_id}>
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium text-slate-900">{conn.name}</div>
                <div className="text-xs text-slate-500 mt-0.5">{conn.provider}</div>
              </div>
              <Badge variant={statusVariant[conn.status] || "default"}>{conn.status}</Badge>
            </div>
            <div className="text-xs text-slate-500 mt-2">
              Last tested: {conn.last_tested_at ? formatDateTime(conn.last_tested_at) : "Never"}
            </div>
            <div className="flex gap-2 mt-3 pt-3 border-t border-slate-100">
              <button
                onClick={() => handleTest(conn.connection_id)}
                disabled={testing === conn.connection_id}
                className="flex items-center gap-1 px-2.5 py-1.5 text-xs rounded border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
              >
                <TestTube size={13} />
                {testing === conn.connection_id ? "Testing..." : "Test"}
              </button>
              <button
                onClick={() => setDeleteTarget({ id: conn.connection_id, name: conn.name })}
                className="flex items-center gap-1 px-2.5 py-1.5 text-xs rounded border border-red-200 text-red-600 hover:bg-red-50"
              >
                <Trash2 size={13} /> Delete
              </button>
            </div>
          </Card>
        ))}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Connection">
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Are you sure you want to delete <span className="font-semibold text-slate-900">{deleteTarget?.name}</span>? This action cannot be undone.
          </p>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setDeleteTarget(null)}
              className="px-3 py-2 text-sm rounded border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 text-sm rounded font-medium text-white bg-red-600 hover:bg-red-700 transition-colors"
            >
              Delete Connection
            </button>
          </div>
        </div>
      </Modal>

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Add Connection">
        <form onSubmit={handleCreate} className="space-y-3">
          {[
            { key: "name", label: "Connection Name", type: "text", autoComplete: "off" },
            { key: "sender_id", label: "Sender ID", type: "text", autoComplete: "off" },
            { key: "sender_password", label: "Sender Password", type: "password", autoComplete: "new-password" },
            { key: "company_id", label: "Company ID", type: "text", autoComplete: "off" },
            { key: "user_id", label: "User ID", type: "text", autoComplete: "off" },
            { key: "user_password", label: "User Password", type: "password", autoComplete: "new-password" },
          ].map((field) => (
            <div key={field.key}>
              <label htmlFor={`conn-${field.key}`} className="block text-sm text-slate-600 mb-1">{field.label}</label>
              <input
                id={`conn-${field.key}`}
                type={field.type}
                required
                autoComplete={field.autoComplete}
                value={formData[field.key as keyof typeof formData]}
                onChange={(e) => setFormData((f) => ({ ...f, [field.key]: e.target.value }))}
                className="w-full px-3 py-2 rounded border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/20 focus:border-[var(--accent)]"
              />
            </div>
          ))}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="px-3 py-2 text-sm rounded border border-slate-200 text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creating}
              className="flex items-center gap-2 px-4 py-2 text-sm rounded font-medium text-white bg-[var(--accent)] hover:bg-[var(--accent-light)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {creating && <Loader2 size={14} className="animate-spin" />}
              {creating ? "Creating..." : "Create"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
