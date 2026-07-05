# Ledgerly — agent instructions

## Session context files (maintain these!)
Two gitignored, repo-root files carry cross-session context. **At session start, read both.** They may not exist on a fresh clone — recreate them from git history if missing.

- **`REPO_STATE.md`** — current snapshot: stack, run/test commands, design-system conventions, feature inventory, known gotchas, in-flight work.
- **`SESSION_SUMMARY.md`** — dated log, newest first: what was done and *why* (decisions, root causes), per session/feature.

**After every feature, fix, or notable decision: update both files before ending the turn.** REPO_STATE gets edited in place (it reflects *now*); SESSION_SUMMARY gets a new/extended dated entry. Stale context files are worse than none.

## Hard rules
- **Never `git push` or open PRs** — the user commits and pushes. Committing locally only when asked.
- **All tests must pass** before a feature is "done" — including pre-existing failures you didn't cause. Fix them, don't skip them.
- **FR + EN i18n in sync** (`web/src/lib/i18n/translations.ts`) for every user-visible string.
- The app promises **"100% local — no data leaves your machine"** — any feature calling external services needs explicit discussion first.
- Live-DB data fixes: only via app service code, only after showing the user exactly what will change and getting confirmation.

## Quick reference
- Run: `docker compose build api web && docker compose up -d` → app at `http://localhost/` (Caddy).
- Tests: `docker compose -f docker-compose.test.yml run --rm api-test` then **always** `docker compose -f docker-compose.test.yml down`.
- Design conventions (cards, KPI pills, chart styling, tokens): see REPO_STATE.md — follow them for anything UI.
- Architecture docs live in `docs/` (ARCHITECTURE.md, DATA_MODEL.md, …).
