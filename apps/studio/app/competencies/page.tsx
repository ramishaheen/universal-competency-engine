"use client";

import useSWR from 'swr';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function CompetenciesPage() {
  const { data, error, isLoading } = useSWR('competencies', () => api.listCompetencies());

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Competencies</h1>
        <Link href="/competencies/new" className="btn btn-primary">+ New</Link>
      </div>
      {isLoading && <div className="text-muted">Loading…</div>}
      {error && <div className="text-danger">{String(error.message)}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(data || []).map((c) => (
          <Link key={c.id} href={`/competencies/${c.id}`} className="card p-4 hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <div className="font-medium">{c.name}</div>
              <span className={`pill ${c.risk_level === 'critical' || c.risk_level === 'high' ? 'pill-danger' : 'pill-success'}`}>
                risk: {c.risk_level}
              </span>
            </div>
            <div className="text-xs text-muted mt-1 mono">{c.id} · v{c.version} · {c.domain || '—'}</div>
            <div className="text-sm mt-2 line-clamp-2">{c.description || <em className="text-muted">no description</em>}</div>
          </Link>
        ))}
        {data && data.length === 0 && (
          <div className="text-muted text-sm">No competencies yet. Click + New to create one, or import from <span className="mono">competencies/</span>.</div>
        )}
      </div>
    </div>
  );
}
