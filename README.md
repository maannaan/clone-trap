# Clone Trap

**What hidden assumptions could prevent a clean clone from working?**

`Python 3.10+` · `Git` · `stdlib tests` · `Rote Play`

Source: [https://github.com/maannaan/clone-trap](https://github.com/maannaan/clone-trap)

A read-only repository portability auditor. It compares what a repository claims you need with what the working tree appears to require, then reports only the gaps that have evidence.

It never says a clone will fail. It never runs `npm install`, Docker, or application code.

## Problem

A repository that works on the author's machine often fails after a clean clone. README may say `npm install && npm run dev` while startup code also reads `REDIS_URL` and expects PostgreSQL.

Those hidden assumptions already live in the tree: documentation, manifests, scripts, Git configuration, tracked or ignored artifacts, service configuration, toolchain declarations, and machine-specific paths. Most linters check one layer. They do not join them.

## Solution

Clone Trap treats the working tree as evidence. It extracts structured facts, joins them across docs / examples / compose / source, and scores only candidates with independent signals.

```
  Git working tree
        |
        v
   inventory + extractors
        |
        v
   cross-signal join -----> score + verdicts
        |
        +--> documentation drift
        +--> clone path
        +--> bootstrap actions
        +--> readiness bucket
```

## Features

- Stdlib-only Python engine (`src/clone_trap`)
- Adapterless Rote Play that vendors the same package (no `engine_root`)
- Confirmed / likely / assumption / informational verdicts
- Documentation drift, clone path, and agent bootstrap actions
- Read-only Git argv (`shell=False`, allowlisted subcommands)
- No network, no adapters, no target-repo code execution, no installs

## Clone and install

```bash
git clone https://github.com/maannaan/clone-trap.git
cd clone-trap
```

Requirements: Python 3.10+ and Git on `PATH`. There is nothing required to pip-install for the engine. Dev tests use pytest:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Python CLI

```bash
PYTHONPATH=src python3 -m clone_trap --repo /absolute/path/to/git/repo
PYTHONPATH=src python3 -m clone_trap --repo /absolute/path/to/git/repo --json
python3 scripts/clone_trap.py --repo /absolute/path/to/git/repo --max-findings 20
```

`src/clone_trap/` is the source of truth. `play/resources/clone_trap/` is a packaged copy that must stay in sync.

## Rote Play

Public Play (no `engine_root`; does not need this checkout):

```bash
rote play run https://play.modiqo.ai/maannaaan/clone-trap@0.1.0 \
  repo_path=/absolute/path/to/git/repo
```

From a clone-trap checkout:

```bash
rote play run play/main.ts repo_path=/absolute/path/to/git/repo
```

The Play ships the analysis package. Findings are evidence, not a guarantee that a clone will fail or succeed.

`rote play info` may print `version: 0.80.0`. That is the Rote runtime (`rote_version`). The Play version is **0.1.0**.

## Inputs

| Input | Required | Default | Purpose |
| --- | --- | --- | --- |
| `repo_path` / `--repo` | yes | — | Path to the Git working tree |
| `max_findings` / `--max-findings` | no | 20 | Hide extra findings after ranking |
| `--json` | no | off | Machine-readable stdout |

## Example

README promises `npm install` and `npm run dev`. Startup reads `REDIS_URL` and no Compose Redis service exists.

Clone Trap reports a confirmed trap: undocumented Redis / `REDIS_URL`, readiness `HIGH RISK TO CLONE`, and a bootstrap action to configure `REDIS_URL`.

Inspect that evidence. Do not treat it as proof the process cannot start.

## Safety

- Allowlisted read-only Git only: `rev-parse`, `ls-files`, `check-ignore`, `submodule`
- Executable is always literal `git` with `shell=False`
- No project code execution, npm scripts, Docker, or target-repo tests
- No dependency installation
- No network, remotes, credentials, or adapters
- Wording stays **appears to require**, **may fail on a clean clone**, **consider documenting**

## Limitations

- Static analysis cannot see native libraries or compile-time failures.
- Optional feature flags may look required if fallbacks are dynamic.
- Documentation mentions are heuristic.
- Empty output is not a safety guarantee.
- Scanning this repository itself can report fake service traps (mongodb/mysql/rabbitmq) because the extractors contain those pattern strings. Do not demo Clone Trap on its own source.

## Tests

```bash
PYTHONPATH=src python3 -m pytest -q
```

## Part of Repository Memory Intelligence

`clone-trap` is the third project in the series, after `change-neighbor` and `merge-memory`.

- change-neighbor asks what else may deserve review
- merge-memory asks what historically went wrong here
- clone-trap asks what hidden assumptions could prevent a clean clone from working

## Project status

The GitHub repository and the Rote Play are public. MIT license. Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
