# Serena-Style Reading Discipline

Goals
- Minimize tokens and noise. Read only what’s necessary to act.

Rules
- Prefer `rg` over broad `cat`/`grep`. Start with filenames or symbol hints.
- Read small ranges: `sed -n 'start,endp' file` (≤ 120 lines typical).
- Stop re-reading: once a file is fully read, don’t re-fetch it with other tools unless needed.
- Narrow scope: pass explicit paths to searches; avoid repo-wide scans without reason.
- Use structure: look for index/config files first (e.g., `apps/lagom-web/tsconfig.json`, `next.config.js`).

Examples
- Symbols/usage: `rg -n "export default function Home" apps/lagom-web/src/app -S`
- Nearest context: `sed -n '1,120p' apps/lagom-web/src/app/page.tsx`
- Config check: `sed -n '1,160p' apps/lagom-web/tsconfig.json`

When to read more
- Architecture questions, cross-cutting concerns, or ambiguous ownership.
- Before large refactors, gather overviews (file lists, key modules) then sample specific files.

