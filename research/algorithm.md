# Algorithm

The tool answers: **what hidden assumptions could prevent a clean clone from working?**

It is a working-tree auditor. Git history is out of scope (that belongs to change-neighbor and merge-memory).

## Architecture

1. Inventory the repository (tracked files, gitignore, submodules, classified paths).
2. Extract structured facts per file class (docs, env, compose/CI, manifests, scripts, source).
3. Join facts on shared keys (env name, service name, binary, path, version identity).
4. Score only joined candidates with an additive model.
5. Assign verdicts with a two-source rule for confirmed traps.
6. Synthesize documentation drift, clone path, bootstrap actions, and readiness.
7. Render text or JSON.

No LLMs. No network. No target-repo execution. A raw `localhost` or `process.env` hit never becomes a finding by itself.

## Inputs

- `--repo`: local Git working tree (required)
- `--json`: machine-readable stdout
- `--max-findings`: display cap after ranking (default 20)

## Inventory

Read-only Git allowlist: `rev-parse`, `ls-files`, `check-ignore`, `submodule`.

Skip vendor trees: `node_modules`, `.git`, `.venv`, `venv`, `dist`, `build`, `coverage`, `.next`, `__pycache__`, and similar.

Cap file reads (size and count). Skip binaries. Do not read `.env` values.

File classes: `source`, `test`, `docs`, `example`, `env_example`, `compose`, `ci`, `manifest`, `lockfile`, `version`, `script`, `ignore`, `gitmodules`, `config`.

## Extractors

Structured, class-aware. Not a repo-wide grep.

- **Docs:** claimed setup commands, mentioned env names, mentioned services, generate commands.
- **Env:** language-aware `os.getenv` / `process.env` in source and config; keys from `.env.example` / `.env.template` / `.env.sample`.
- **Compose / CI:** purpose-built YAML subset (`services`, `image`, `environment`, `ports`, setup-python / setup-node versions).
- **Manifests:** `package.json` scripts and engines; `pyproject.toml` / `requirements.txt`; lockfiles; `.python-version` / `.nvmrc`.
- **Artifacts:** referenced paths that are ignored and not produced by a documented generate step; empty submodules.
- **Toolchain:** binaries used in repo scripts but not declared as dependencies; version-file conflicts; non-public registry hosts.
- **Locality:** absolute and `$HOME` paths in runtime files; OS-only bootstrap scripts; sibling-repo references.

## Join keys

Candidates are grouped by identity: env name, service name, binary name, artifact path, version family, locality pattern.

A candidate must have at least one runtime/source signal before scoring. Documentation-only mentions are not traps.

## Scoring

Additive confidence, clamped to 0.00–1.00.

Positive:

- referenced in executable/startup/config code: +0.35
- missing from README/setup docs: +0.20
- missing from the natural declaration file (`.env.example`, compose, manifest): +0.20
- no fallback/default in code: +0.15
- referenced by multiple independent files: +0.10
- CI and local setup disagree: +0.10

Negative:

- documented in README/setup docs: −0.25
- present in example/compose/manifest: −0.25
- optional, defaulted, or guarded: −0.20
- only appears in tests/examples/fixtures: −0.20
- well-known ambient variable (`NODE_ENV`, `CI`, `DEBUG`, `PATH`): −0.30

## Verdicts

- `confirmed_trap`: confidence ≥ 0.80 **and** at least two independent positive source *kinds* **and** at least one undeclared/missing-declaration signal **and** not test/example-only
- `likely_trap`: 0.60–0.79, or two sources with some counter-evidence
- `environment_assumption`: a real external dependency that is documented, or one strong undeclared signal
- `informational`: 0.40–0.59 after penalties
- below 0.40: dropped

Independent sources mean different file kinds (source vs docs vs compose), not two lines in the same file.

Severity is impact, not confidence:

- `high` — startup/config path, no fallback, blocks `run` or `start_services`
- `medium` — feature-path or generate-step
- `low` — optional, contributor-only, or locality nit

A documented Postgres service is an `environment_assumption`. It is not a trap.

## Caps

Display at most 8 confirmed, 8 likely, 8 assumptions, and 5 informational findings. `--max-findings` truncates after ranking. JSON sets `truncated: true` when anything was dropped.

## Synthesis

- **Documentation drift:** README commands vs undocumented confirmed/likely requirements.
- **Clone path:** place findings on `clone → install → generate → configure → start_services → run` without executing those steps.
- **Bootstrap actions:** confirmed traps plus likely traps with confidence ≥ 0.70. Empty means no high-confidence setup gap, not "safe to run."
- **Readiness:** `ready` / `mostly_portable` / `hidden_assumptions` / `high_risk`, plus a one-sentence reason. Not a 0–100 score.

## Language

Always: "appears to require", "may fail on a clean clone", "consider documenting."

Never: "will fail", "is broken", "must add", "the repository is incomplete."

## Safety

Read-only Git only. `shell=False`. No add, commit, checkout, reset, network, installs, or target-repo code execution.
