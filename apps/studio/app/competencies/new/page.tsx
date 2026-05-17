"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

const SAMPLE = `{
  "id": "demo",
  "name": "Demo Competency",
  "mission": "Do something useful",
  "objectives": [{"id": "primary", "name": "Primary objective"}],
  "skills": [{
    "id": "echo",
    "name": "Echo",
    "execution_steps": [
      {"id": "say", "type": "prompt", "prompt": "Echo: {{inputs.text}}", "output_key": "msg"}
    ]
  }],
  "workflows": [{
    "id": "main",
    "name": "Main",
    "is_default": true,
    "steps": [{"id": "r", "type": "skill", "skill": "echo", "output_key": "msg"}]
  }],
  "policies": [{"id": "allow", "name": "Allow", "effect": "allow", "applies_to": ["*"]}],
  "llm": {"provider": "anthropic", "model": "claude-sonnet-4-6"}
}`;

export default function NewCompetencyPage() {
  const router = useRouter();
  const [json, setJson] = useState(SAMPLE);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true); setErr(null);
    try {
      const def = JSON.parse(json);
      const c = await api.createCompetency(def) as any;
      router.push(`/competencies/${c.id}`);
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  async function validateOnly() {
    setBusy(true); setErr(null);
    try {
      const def = JSON.parse(json);
      await api.validateDefinition(def);
      setErr('✓ valid');
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">New Competency</h1>
      <p className="text-sm text-muted">Paste a Competency JSON definition. (YAML can be authored via the CLI: <span className="mono">competency create</span>.)</p>
      <textarea
        value={json}
        onChange={(e) => setJson(e.target.value)}
        className="input mono"
        rows={28}
      />
      {err && <div className={`text-sm ${err.startsWith('✓') ? 'text-success' : 'text-danger'}`}>{err}</div>}
      <div className="flex gap-2">
        <button className="btn" onClick={validateOnly} disabled={busy}>Validate</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>{busy ? 'Saving…' : 'Create'}</button>
      </div>
    </div>
  );
}
