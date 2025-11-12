# Code & PR Review Rules

Focus: correctness, clarity, cohesion, and minimal diff.

Design & Readability
- Single Responsibility: one reason to change per module/component.
- Names reveal intent; avoid abbreviations; align with variable roles when useful.
- Short, focused functions; prefer composition over conditionals nesting.

Refactoring Triggers (Fowler)
- Duplicated code, long method, large class/module, long parameter list, feature envy.
- Apply safe refactorings: Extract Function, Rename, Move Function, Introduce Parameter Object.

TypeScript/Next.js
- Strict types; no `any` unless justified.
- Client/server boundaries explicit; avoid server-only APIs in client components.
- Co-locate tests as `*.test.ts(x)` and favor React Testing Library.

Python (crawler/airflow)
- PEP8; explicit interfaces; small pure functions where possible.
- Tests named `test_*.py`; avoid hidden side effects in module import.

APIs & Contracts (Zimmermann)
- Design-first: document routes/contracts; version explicitly.
- Prefer tolerant readers; add contract tests where feasible.

PR Hygiene
- Conventional Commits in title (e.g., `feat(lagom-web): ...`).
- Description includes problem, approach, screenshots (UI), and risks/breaking changes.
- Diff is minimal; unrelated refactors split out.

