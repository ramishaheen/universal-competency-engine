"use client";

import { use, useState } from 'react';
import useSWR from 'swr';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function ExecutionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, error, mutate } = useSWR(['execution', id], () => api.getExecution(id));
  const { data: audit } = useSWR(['exec-audit', id], () => api.audit({ run_id: id }));
  const [busy, setBusy] = useState(false);

  if (error) return <div className="text-danger">{String(error.message)}</div>;
  if (!data) return <div className="text-muted">Loading…</div>;

  async function approve(approved: boolean) {
    setBusy(true);
    try {
      await api.approveExecution(id, approved);
      await mutate();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <Link href="/executions" className="text-xs text-muted hover:underline">← all executions</Link>
          <h1 className="text-2xl font-semibold tracking-tight mono">{data.id}</h1>
          <div className="text-xs text-muted">competency: <Link href={`/competencies/${data.competency_id}`} className="mono hover:underline">{data.competency_id}</Link></div>
        </div>
        <span className={`pill ${data.status === 'succeeded' ? 'pill-success' : data.status === 'failed' || data.status === 'denied' ? 'pill-danger' : data.status === 'pending_approval' ? 'pill-warn' : ''}`}>
          {data.status}
        </span>
      </div>

      {data.status === 'pending_approval' && data.pending_approval && (
        <div className="card p-4 space-y-3 border-yellow-400">
          <div className="label">Pending approval</div>
          <pre className="mono text-xs whitespace-pre-wrap">{JSON.stringify(data.pending_approval, null, 2)}</pre>
          <div className="flex gap-2">
            <button className="btn btn-primary" onClick={() => approve(true)} disabled={busy}>Approve</button>
            <button className="btn btn-danger" onClick={() => approve(false)} disabled={busy}>Reject</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="tokens in" value={data.tokens_in} />
        <Stat label="tokens out" value={data.tokens_out} />
        <Stat label="cost (USD)" value={`$${(data.cost_usd || 0).toFixed(4)}`} />
        <Stat label="latency (ms)" value={data.latency_ms} />
      </div>

      <Section title="Inputs"><pre className="mono text-xs overflow-x-auto">{JSON.stringify(data.inputs, null, 2)}</pre></Section>
      <Section title="Outputs"><pre className="mono text-xs overflow-x-auto whitespace-pre-wrap">{JSON.stringify(data.outputs, null, 2)}</pre></Section>
      {data.plan && (
        <Section title="Plan">
          <div className="text-sm space-y-1">
            <div>confidence: <span className="mono">{(data.plan.confidence * 100).toFixed(0)}%</span></div>
            <div>risk: <span className="mono">{(data.plan.risk_score * 100).toFixed(0)}%</span></div>
            <div>alignment: <span className="mono">{(data.plan.alignment_score * 100).toFixed(0)}%</span></div>
          </div>
          <pre className="mono text-xs mt-3 overflow-x-auto whitespace-pre-wrap">{JSON.stringify(data.plan.steps, null, 2)}</pre>
        </Section>
      )}
      {data.error && <Section title="Error"><pre className="mono text-xs text-danger">{data.error}</pre></Section>}

      <Section title="Audit trail">
        <div className="space-y-1 max-h-96 overflow-y-auto text-xs mono">
          {(audit || []).map((e) => (
            <div key={e.id} className="flex gap-2 py-1 border-b border-border">
              <span className="text-muted">{new Date(e.created_at).toLocaleTimeString()}</span>
              <span className="font-medium">{e.event_type}</span>
              <span>{e.action}</span>
              {e.decision && <span className="pill">{e.decision}</span>}
              {e.error && <span className="text-danger">{e.error}</span>}
            </div>
          ))}
          {audit && audit.length === 0 && <div className="text-muted">no events</div>}
        </div>
      </Section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="card p-3">
      <div className="label">{label}</div>
      <div className="text-lg font-medium mono mt-1">{value}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-4">
      <div className="label mb-2">{title}</div>
      {children}
    </div>
  );
}
