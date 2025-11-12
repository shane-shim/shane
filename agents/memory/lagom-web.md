# Memory: apps/lagom-web

Stack
- Next.js 14 (app router), TypeScript strict, Tailwind.

Key paths
- App components: `apps/lagom-web/src/app/**`
- Config: `apps/lagom-web/next.config.js`, `apps/lagom-web/tsconfig.json`, `apps/lagom-web/tailwind.config.js`
- Public assets: `apps/lagom-web/public/**`

Scripts
- `npm run dev`, `npm run build`, `npm start`, `npm run lint`

Notes
- `eslint` enabled via `eslint.config.mjs`.
- Use `Image` from `next/image`; keep server/client boundaries explicit.

