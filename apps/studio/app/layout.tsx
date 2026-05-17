import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'UCE Studio',
  description: 'Universal Competency Engine — Studio',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <header className="border-b border-border bg-surface">
          <div className="mx-auto max-w-6xl flex items-center justify-between px-6 py-3">
            <Link href="/" className="font-semibold tracking-tight">UCE Studio</Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link href="/competencies" className="hover:underline">Competencies</Link>
              <Link href="/executions" className="hover:underline">Executions</Link>
              <Link href="/audit" className="hover:underline">Audit</Link>
              <Link href="/login" className="btn">Sign in</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        <footer className="mx-auto max-w-6xl px-6 py-6 text-xs text-muted">
          Universal Competency Engine — v0.1
        </footer>
      </body>
    </html>
  );
}
