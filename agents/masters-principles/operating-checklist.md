# Operating Checklist (Codex CLI Agent)

Use this checklist for every task in this repo.

1) Intake & Scope
- Clarify goal, constraints, and success criteria.
- Identify affected subproject: `lagom-web/`, `news-crawler-bot/`, `airflow/`, or `python_scripts/`.

2) Recon
- List files and configs in scope. For Next.js: `package.json`, `tsconfig.json`, `next.config.js`, `src/app/**`.
- For Python: `requirements.txt`, entrypoints, `docker-compose.yml` (crawler).

3) Plan (brief)
- Outline 2–5 concrete steps. Separate feature vs refactor work (Fowler’s two hats).

4) Implement (small steps)
- Make minimal change; prefer Extract Function / Rename to improve clarity.
- Keep components single-responsibility; avoid global side effects.

5) Validate
- Frontend: `npm run build` (or `bun/pnpm`), `npm run lint`. Add/adjust `*.test.tsx` if behavior changed.
- Python: run unit tests (`pytest` if present) or functional checks; validate Docker compose if touched.

6) Summarize
- Describe what changed, why, and impact. Note follow-ups.

TDD Micro-cycle (when changing behavior)
- Red: write/modify a single failing test.
- Green: implement minimal code to pass.
- Refactor: improve design with tests green.

Guardrails
- No secrets or credentials. Never edit generated artifacts (e.g., `.next/`, `node_modules/`).
- Prefer explicit names that reflect variable roles (flag/stepper/gatherer, etc.).

