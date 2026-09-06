# Release readiness

## Checklist

- [x] `PYTHONPATH=src python -m pytest -q` — 30 passed after vendor sync
- [x] CLI `--help` / `--json` emit stable `schema_version: 1`
- [x] Empty honest result on change-neighbor and merge-memory
- [x] Two-source confirmed-trap rule covered by unit tests
- [x] Synthetic fixtures 1–10
- [x] Play `rote play lint play/main.ts` passed
- [x] Play vendors `src/clone_trap` (no `engine_root`)
- [x] Presentation fixtures + blocked/truncated/partial cases
- [x] Cursor skill with when-to-run / when-not-to-run
- [x] README + CONTRIBUTING + research docs
- [x] Real-repo audit recorded in `validation/findings.md`
- [ ] Registry publication (`rote play release`) — not done in this phase; no commit/push unless requested

## Known limitations

- Shell script binary extraction can still over-report uncommon tokens
- Documentation command extraction can pick up prose (`make this`)
- Static analysis cannot see native libraries or compile failures
- Empty output is not a safety guarantee

## Version

- Package: `0.1.0`
- Play frontmatter: `0.1.0`
- `rote_version`: `0.80.0`
