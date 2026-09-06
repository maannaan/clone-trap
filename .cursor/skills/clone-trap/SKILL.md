---
name: clone-trap
description: >
  Before installing or starting an unfamiliar repository, run Clone Trap to
  surface hidden environment, service, artifact, toolchain, and locality
  assumptions that may prevent a clean clone from working. Do not use for
  typo-only, documentation-only, or formatting-only edits.
---

# Clone Trap

Compare what a repository claims you need with what it appears to require. Findings are portability evidence, not a guarantee that a clone will fail or succeed.

Do not execute install, generate, Docker, or application commands because of this report. Do not invent traps that are not in the JSON. Investigate cited files; do not auto-edit the target repository.

## When to run

Run before:

- cloning or onboarding onto an unfamiliar repository
- asking an agent to install dependencies or start the app
- handing a repository to another team
- investigating CI/local setup mismatches

Do not run for:

- tiny typo fixes
- purely cosmetic edits
- documentation-only changes
- trivial formatting

## How to run

From a clone-trap checkout:

```bash
PYTHONPATH=src python3 -m clone_trap --json --repo /absolute/path/to/git/repo
```

Or:

```bash
python3 scripts/clone_trap.py --json --repo /absolute/path/to/git/repo
```

Optional Rote Play (self-contained; no `engine_root`):

```bash
rote play run play/main.ts repo_path=/absolute/path/to/git/repo
```

## How to interpret results

JSON fields: `readiness`, `documentation_drift`, `clone_path`, `bootstrap_actions`, `findings`.

- **confirmed_trap** — two independent signals and a missing declaration. Treat as a real setup gap.
- **likely_trap** — multiple signals, some counter-evidence. Inspect before running.
- **environment_assumption** — a real external dependency that is documented. Know it exists; it is not a trap.
- **informational** — weak evidence only.

Empty `bootstrap_actions` means no high-confidence setup gap was found. Continue. Do not treat that as "safe to run."

Footer meaning: `Portability evidence only — not a guarantee the clone will fail or succeed.`

## How to act

**Undocumented environment variable.** Add it to `.env.example` and setup docs before attempting to start the app, or confirm a code fallback exists.

**Undocumented service.** Check Compose/CI and README. Do not assume Redis/Postgres is optional because the process started.

**Generated or ignored artifact.** Look for a documented generate command. Do not invent one.

**No findings.** Continue with the documented setup. Do not fabricate hidden dependencies.

## Limitations

- Static analysis cannot see native libraries or compile-time failures.
- Optional feature flags may look required if fallbacks are dynamic.
- Documentation mentions are heuristic.
- Empty output is not a safety guarantee.
