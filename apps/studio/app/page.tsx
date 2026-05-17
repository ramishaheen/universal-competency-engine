import Link from 'next/link';

export default function Home() {
  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Universal Competency Engine</h1>
        <p className="text-muted max-w-2xl">
          Author, govern, and run AI competencies. A competency is an integrated expert
          capability: skills + reasoning + workflows + memory + policies + objectives + evaluation.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link href="/competencies" className="card p-5 hover:shadow-md transition">
          <div className="label">Manage</div>
          <div className="mt-1 text-lg font-medium">Competencies</div>
          <div className="text-sm text-muted mt-1">List, create, validate, edit competency definitions.</div>
        </Link>
        <Link href="/executions" className="card p-5 hover:shadow-md transition">
          <div className="label">Inspect</div>
          <div className="mt-1 text-lg font-medium">Executions</div>
          <div className="text-sm text-muted mt-1">View past runs, approve pending ones, see outputs.</div>
        </Link>
        <Link href="/audit" className="card p-5 hover:shadow-md transition">
          <div className="label">Govern</div>
          <div className="mt-1 text-lg font-medium">Audit log</div>
          <div className="text-sm text-muted mt-1">Every decision, every action, with reasons + cost.</div>
        </Link>
      </div>
    </div>
  );
}
