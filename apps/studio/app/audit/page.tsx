"use client";

import useSWR from 'swr';
import { api } from '@/lib/api';

export default function AuditPage() {
  const { data, error } = useSWR('audit', () => api.audit());
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">Audit Log</h1>
      {error && <div className="text-danger">{String(error.message)}</div>}
      <div className="card overflow-x-auto">
        <table className="w-full text-xs mono">
          <thead className="text-left text-muted">
            <tr>
              <th className="p-3">time</th><th>event</th><th>action</th><th>decision</th>
              <th>actor</th><th>tokens</th><th>cost</th><th>error</th>
            </tr>
          </thead>
          <tbody>
            {(data || []).map((e) => (
              <tr key={e.id} className="border-t border-border">
                <td className="p-3">{new Date(e.created_at).toLocaleTimeString()}</td>
                <td>{e.event_type}</td>
                <td>{e.action}</td>
                <td>{e.decision || ''}</td>
                <td>{e.actor?.email || e.actor?.id || '-'}</td>
                <td>{(e.tokens_in || 0) + (e.tokens_out || 0)}</td>
                <td>${(e.cost_usd || 0).toFixed(4)}</td>
                <td className="text-danger">{e.error || ''}</td>
              </tr>
            ))}
            {data && data.length === 0 && <tr><td colSpan={8} className="p-4 text-muted">no events</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
