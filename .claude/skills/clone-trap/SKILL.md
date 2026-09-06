---
name: clone-trap
description: >
  This skill should be used when the user asks whether another developer can
  clone and run a repository, about onboarding, clean-machine readiness,
  hidden setup assumptions, missing dependencies, portability, environment
  requirements, why a project works on one machine but not another, CI vs
  local mismatches, or open-sourcing without undocumented dependencies.
  Use it for questions like "can another developer clone this and get
  started?", "what hidden assumptions does this repository have?", or
  "why might this fail on CI or another laptop?" It runs Clone Trap, a
  read-only portability auditor. Do not use it for typo-only,
  documentation-only, or formatting-only edits. For historical co-change
  use change-neighbor. For previous bugs or reverts use merge-memory.
---

# Clone Trap

Compare what a repository claims you need with what it appears to require. Findings are portability evidence, not a guarantee that a clone will fail or succeed.

## When to use

- Cloning or onboarding onto a repository
- "Can another developer clone this and run it?"
- Hidden setup assumptions, missing dependencies, environment requirements
- Why it works on one machine but not another; CI vs local
- Clean-machine / open-source readiness

## When not to use

- Typo-only, documentation-only, or formatting-only edits
- "What else usually changes with this module?" → use **change-neighbor**
- "Has this area failed or been reverted before?" → use **merge-memory**

Do not execute install, generate, Docker, or application commands because of this report. Do not auto-edit the target repository.

## Natural-language triggers

- "Can another developer clone this and get started without undocumented dependencies?"
- "What hidden assumptions does this repository have?"
- "Why might this fail on CI or another laptop?"
- "This works on my machine; what could prevent someone else from running it?"

## Command

`--repo` is required. Prefer `python3` (`python` may be missing).

Prefer the skill launcher:

```bash
bash ~/.claude/skills/clone-trap/scripts/run --json --repo /absolute/path/to/git/repo
```

Equivalent direct command:

```bash
PYTHONPATH=/absolute/path/to/clone-trap/src \
  python3 -m clone_trap --json --repo /absolute/path/to/git/repo
```

Or: `python3 /absolute/path/to/clone-trap/scripts/clone_trap.py --json --repo /absolute/path/to/git/repo`

## How to interpret output

JSON fields: `readiness`, `documentation_drift`, `clone_path`, `bootstrap_actions`, `findings`.

- **confirmed_trap** — two independent signals and a missing declaration. Treat as a real setup gap.
- **likely_trap** — multiple signals, some counter-evidence. Inspect before running.
- **environment_assumption** — a real external dependency that is documented.
- **informational** — weak evidence only.

`READY` and empty `bootstrap_actions` mean no high-confidence setup gap was found. Continue. That is not a guarantee the clone will work.

## Evidence language rules

- Say: "appears to require", "may fail on a clean clone", "consider documenting"
- Never say a clone "will fail" or that PowerShell "breaks on any machine"
- Do not invent traps that are not in the JSON
- Investigate cited files; do not treat READY as proof of portability
