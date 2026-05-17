"use client";

import { use, useState } from 'react';
import useSWR from 'swr';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function CompetencyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: comp, error } = useSWR(['competency', id], () => api.getCompetency(id));
  const { data: perf } = useSWR(['perf', id], () => api.performance(id));
  const { data: execs, mutate: refreshExecs } = useSWR(['execs', id], () => api.listExecutions(id));

  const [inputs, setInputs] = useState('{"request": "Buy 25 monitors for the design team", "budget_usd": 12000}');
  const [runPlan, setRunPlan] = useState(true);
  const [running, setRunning] = useState(false);
  const [runErr, setRunErr] = useState<string | null>(null);

  async function run() {
    setRunning(true); setRunErr(null);
    try {
      const parsed = JSON.parse(inputs);
      await api.execute(id, { inputs: parsed, run_plan: runPlan });
      await refreshExecs();
    } catch (e: any) {
      setRunErr(e.message || String(e));
    } finally {
      setRunning(false);
    }
  }

  if (error) return <div className="text-danger">{String(error.message)}</div>;
  if (!comp) return <div className="text-muted">Loading…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link href="/competencies" className="text-xs text-muted hover:underline">← all competencies</Link>
          <h1 className="text-2xl font-semibold tracking-tight">{comp.name}</h1>
          <div className="text-xs text-muted mono">{comp.id} · v{comp.version} · {comp.domain || '—'}</div>
        </div>
        <span className={`pill ${comp.risk_level === 'critical' || comp.risk_level === 'high' ? 'pill-danger' : 'pill-success'}`}>
          risk: {comp.risk_level}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="label">Mission</div>
          <p className="mt-1 text-sm whitespace-pre-wrap">{comp.definition?.mission || <em className="text-muted">—</em>}</p>
        </div>
        <div className="card p-4">
          <div className="label">Performance</div>
          {perf ? (
            <div className="mt-1 text-sm space-y-0.5">
              <div>runs: <span className="mono">{perf.runs}</span></div>
              <div>success rate: <span className="mono">{(perf.success_rate * 100).toFixed(1)}%</span></div>
              <div>avg latency: <span className="mono">{perf.avg_latency_ms.toFixed(0)} ms</span></div>
              <div>total tokens: <span className="mono">{perf.total_tokens}</span></div>
              <div>total cost: <span className="mono">${perf.total_cost_usd.toFixed(4)}</span></div>
            </div>
          ) : (
            <div className="text-muted text-sm mt-1">no runs yet</div>
          )}
        </div>
      </div>

      <div className="card p-4 space-y-3">
        <div className="label">Run</div>
        <textarea className="input mono" rows={5} value={inputs} onChange={(e) => setInputs(e.target.value)} />
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={runPlan} onChange={(e) => setRunPlan(e.target.checked)} /> Run reasoning before executing
        </label>
        {runErr && <div className="text-sm text-danger">{runErr}</div>}
        <button className="btn btn-primary" onClick={run} disabled={running}>{running ? 'Running…' : 'Run'}</button>
      </div>

      <div className="card p-4">
        <div className="label mb-2">Recent executions</div>
        <table className="w-full text-sm">
          <thead className="text-left text-muted">
            <tr><th>id</th><th>status</th><th>tokens</th><th>cost</th><th>latency</th><th>started</th></tr>
          </thead>
          <tbody>
            {(execs || []).slice(0, 20).map((e) => (
              <tr key={e.id} className="border-t border-border">
                <td><Link href={`/executions/${e.id}`} className="mono hover:underline">{e.id.slice(0, 8)}…</Link></td>
                <td><StatusPill status={e.status} /></td>
                <td className="mono">{e.tokens_in + e.tokens_out}</td>
                <td className="mono">${(e.cost_usd || 0).toFixed(4)}</td>
                <td className="mono">{e.latency_ms} ms</td>
                <td className="mono text-xs">{new Date(e.started_at).toLocaleString()}</td>
              </tr>
            ))}
            {execs && execs.length === 0 && (
              <tr><td colSpan={6} className="text-muted py-3">no executions yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const cls =
    status === 'succeeded' ? 'pill-success' :
    status === 'failed' || status === 'denied' ? 'pill-danger' :
    status === 'pending_approval' ? 'pill-warn' : '';
  return <span className={`pill ${cls}`}>{status}</span>;
}
