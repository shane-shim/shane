# Serena Integration (for this repo)

Purpose
- Adopt Serena’s agent patterns to improve precision, efficiency, and safety in Codex CLI.

Key Principles
- Read minimally: avoid whole-file reads unless necessary; prefer targeted symbol/range inspection.
- Plan → Act → Validate loop: small steps, each ending with a build/lint/test or quick verification.
- Tool discipline: prefer semantic/targeted queries (e.g., `rg`, partial `sed -n`), avoid noisy scans.
- Modes: Implement, Refactor, Investigate, Fix. Choose one and keep scope tight.
- Memories: persist durable repo facts to reduce re-discovery.

How to apply here
- Discovery
  - Use `rg` for structure: `rg --files apps/lagom-web/src/app | head -n 50`.
  - Read only needed lines: `sed -n '1,120p' file.tsx`.
- Editing
  - Extract function, rename, and parameter-object refactors when clarity improves (Fowler).
  - Keep Next.js components SRP; separate server/client concerns.
- Validation
  - Frontend: `cd apps/lagom-web && npm run build && npm run lint`.
  - Python (if touched): `pytest` or minimal functional check; validate Docker compose for crawler.
- Safety
  - Destructive or networked commands require explicit approval; never modify `node_modules/`, `.next/`.

Memories
- Store stable facts under `agents/memory/*.md` (e.g., app structure, scripts, env keys). Update when architecture changes.

Checklist
1) Pick the mode. 2) Draft a short plan. 3) Read minimally. 4) Implement small change. 5) Validate. 6) Summarize and record memory if durable.

