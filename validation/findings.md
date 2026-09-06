# Findings

Recorded 2026-09-06 against existing working trees. Validation repositories were not modified.

An early run parsed Python under `scripts/` as shell and flooded every repo with undeclared-tool traps. That class was fixed before this audit (classify `.py` as source; only parse Makefile / `.sh` for binaries). After that fix, negative controls went quiet.

## change-neighbor — Correct / useful negative control

- Readiness: `ready`
- Confirmed/likely: 0
- Drift: unittest commands only
- Bootstrap: empty

A clean stdlib clone stays silent. This is the required negative control.

## merge-memory — Correct / useful negative control

- Readiness: `ready`
- Confirmed/likely: 0

`engine_root` is a Play limitation, not a hidden runtime dependency of the Python CLI. Staying silent is correct.

## continuum — Useful traps, some generic drift

Correct traps:

- Missing gitignored dataset zip under `data/raw/`
- Uninitialized `hydradb/hydradb-repo` submodule
- PowerShell-only HydraDB bootstrap (`locality` + undeclared `powershell`)

Ambiguous:

- `CONTINUUM_ENV_FILE` as an environment assumption
- Drift extracted noisy `make this` / `make the` phrases from prose
- `documented_but_unused: redis, mysql` from fixture/docs mentions

Bootstrap: safe to follow for submodule init and dataset presence. Do not treat `make this` as a command.

## Deplot — Mixed

Useful / plausible:

- Machine-specific absolute path (locality)
- Playwright env vars that are not in `.env.example`

False positive / weak:

- `v1` as an undeclared tool (later suppressed: binaries must be ≥3 characters)
- `playwright` may be declared in frontend `package.json` depending on which manifest bucket was seen

Declared Redis/Postgres Compose services were **not** emitted as traps. That is the intended service silence.

## Mend — Mostly quiet, one weak toolchain pair

- `DATABASE_URL` / OAuth names that appear in examples were not confirmed traps
- Remaining: `collectors` and `uvicorn` as undeclared tools

`uvicorn` is a plausible undeclared global if it is only invoked from a shell helper. `collectors` is more likely an in-repo script name (later suppressed by matching file stems).

## Ripple — Useful env assumptions, noisy shell parse

Useful:

- Extra NetSuite / MCP env names not in `.env.example`
- `trueforge` / `afconvert` as undeclared external tools (real extra demo/macOS dependencies)
- Postgres in Compose was not a trap

False positives from shell/heredoc/JS-in-shell parsing (`const`, `EOF`, `cfg`, `data`, `m`). A follow-up pass skips heredoc bodies, JS-looking lines, shell keywords, and sub-3-character names.

Sibling `../components/...` paths were suppressed after resolving them inside the repo.

## False-positive classes that appeared twice

1. **Python under `scripts/` parsed as shell** — fixed. Negative controls recovered.
2. **Shell builtins / heredocs / JS snippets as binaries** — reduced with allowlists, function detection, heredoc skipping, and length ≥ 3.
3. **In-repo `../` imports as sibling repositories** — fixed by resolving against the referencing file.

## Verdict

Clone Trap is useful on the family negative controls and on continuum's real clone blockers. It is not yet a perfect shell linter. Remaining toolchain noise should be treated as a known limitation, not as proof a clone will fail.
