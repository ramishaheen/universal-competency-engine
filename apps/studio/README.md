# UCE Studio

Next.js 15 + Tailwind frontend for the Universal Competency Engine.

## Dev

```bash
# from repo root, start the API:
uv run uvicorn uce_api.main:app --reload

# in another terminal:
cd apps/studio
npm install
cp .env.example .env.local
npm run dev
# → http://localhost:3000
```

Default sign-in: `admin@example.com` / `changeme` (override with
`UCE_BOOTSTRAP_ADMIN_PASSWORD` before first API boot).
