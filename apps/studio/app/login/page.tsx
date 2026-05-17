"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('changeme');
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      await api.login(email, password);
      router.push('/competencies');
    } catch (e: any) {
      setErr(e.message || 'login failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-md mx-auto card p-6 space-y-4">
      <h1 className="text-xl font-semibold">Sign in</h1>
      <form onSubmit={submit} className="space-y-3">
        <div>
          <label className="label">Email</label>
          <input className="input mt-1" value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
        </div>
        <div>
          <label className="label">Password</label>
          <input className="input mt-1" value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
        </div>
        {err && <div className="text-sm text-danger">{err}</div>}
        <button className="btn btn-primary w-full" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
      </form>
      <p className="text-xs text-muted">
        Default bootstrap admin: <span className="mono">admin@example.com</span> / <span className="mono">changeme</span>.
        Set <span className="mono">UCE_BOOTSTRAP_ADMIN_PASSWORD</span> before first boot to change.
      </p>
    </div>
  );
}
