"use client";

import useSWR from 'swr';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function ExecutionsPage() {
  const { data, error } = useSWR('executions', () => api.listExecutions());

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Executions</h1>
      {error && <div className="text-danger">{String(error.message)}</div>}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-muted">
            <tr>
              <th className="p-3">id</th><th>competency</th><th>status</th><th>tokens</th>
              <th>cost</th><th>latency</th><th>started</th>
            </tr>
          </thead>
          <tbody>
            {(data || []).map((e) => (
              <tr key={e.id} className="border-t border-border">
                <td className="p-3 mono"><Link href={`/executions/${e.id}`} className="hover:underline">{e.id.slice(0, 8)}…</Link></td>
                <td className="mono">{e.competency_id}</td>
                <td>{e.status}</td>
                <td className="mono">{e.tokens_in + e.tokens_out}</td>
                <td className="mono">${(e.cost_usd || 0).toFixed(4)}</td>
                <td className="mono">{e.latency_ms} ms</td>
                <td className="mono text-xs">{new Date(e.started_at).toLocaleString()}</td>
              </tr>
            ))}
            {data && data.length === 0 && (
              <tr><td colSpan={7} className="p-4 text-muted">no executions yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
