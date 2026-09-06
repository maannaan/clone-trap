# Phase 2 — Real-world validation and tuning

Recorded 2026-09-06. Foreign repositories were not modified. No commit, push, or Play publication.

This phase measured Clone Trap on real working trees, classified every HIGH/MEDIUM finding by hand, then applied only general algorithm fixes for evidenced false-positive classes.

## Verdict

**VALIDATION PASSED WITH MINOR TUNING**

Negative controls stay `ready`. Continuum’s real traps remain. Ripple and Mend no longer flood `high_risk` from a single shell token.

`ready` still means “no high-confidence portability gaps,” not “production quality” or “safe to run.”

## Repositories

| Repo | Path | Role |
| --- | --- | --- |
| clone-trap (self) | this workspace | Fail-closed: not a Git repository |
| change-neighbor | `/Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/change-neighbor` | Clean stdlib negative control |
| merge-memory | `/Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/merge-memory` | Clean package negative control |
| continuum | `/Users/apple/Desktop/Manan/Continumm/continuum` | Submodule, dataset, PowerShell |
| Deplot | `/Users/apple/Desktop/Manan/Hackathons/Deplot` | Compose + machine-specific CLI |
| Mend | `/Users/apple/Desktop/Manan/Hackathons/Mend` | Python extras + Node |
| Ripple | `/Users/apple/Desktop/Manan/Hackathons/Ripple` | Compose, scripts, optional adapters |

No eighth repo was added. These seven already cover Python, Node, Compose, submodules, datasets, mixed apps, CI, and scripts.

Raw JSON (gitignored): `validation/results/phase2-*.json` (pre-tune) and `validation/results/phase2-post-*.json` (post-tune).

## Scenarios

| ID | Intent | Expected | Pre-tune | Post-tune |
| --- | --- | --- | --- | --- |
| A | Clean stdlib (change-neighbor) | `ready`, zero traps | `ready`, 0 | `ready`, 0 |
| B | Mostly portable package (merge-memory) | `ready` | `ready`, 0 | `ready`, 0 |
| C | Mixed app (Mend) | No env/toolchain flood | `hidden_assumptions` (`uvicorn`) | `ready`, 0 |
| D | Compose + demo tooling (Ripple) | Postgres silent; extra tools possible | `high_risk`, 8 confirmed shell tokens | `hidden_assumptions`, real extras only |
| E | Compose Redis/Postgres (Deplot) | Declared services silent | Services silent; Playwright noise | Services silent; Homebrew `zcli` remains |
| F | Submodule + data + PowerShell (continuum) | Real traps | `high_risk` (correct) | `high_risk` (correct) |
| G | Self (clone-trap) | Fail-closed without `.git` | Error, exit 1 | Error, exit 1 |

## Pre-tune HIGH/MEDIUM matrix

Every HIGH/MEDIUM finding was inspected against the cited files. The algorithm was not trusted.

Class labels: `TRUE_POSITIVE` | `USEFUL_WARNING` | `FALSE_POSITIVE` | `AMBIGUOUS`.

| Repo | Finding | Category | Severity | Confidence | Classification | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| change-neighbor | *(none)* | — | — | — | — | Correct silence |
| merge-memory | *(none)* | — | — | — | — | Correct silence |
| continuum | Missing `data/raw/.../all_documents.zip` | artifacts | low (confirmed) | 0.90 | TRUE_POSITIVE | Gitignored dataset; inspected though severity is low |
| continuum | Uninitialized `hydradb/hydradb-repo` | artifacts | high | 0.80 | TRUE_POSITIVE | Plain clone does not fetch submodules |
| continuum | Undeclared `powershell` | toolchain | medium | 0.90 | USEFUL_WARNING | Real Makefile token; wrongly `confirmed_trap` from one script mention |
| continuum | PowerShell-only HydraDB scripts | locality | medium | 0.72 | TRUE_POSITIVE | `.ps1` without Unix counterparts |
| continuum | `CONTINUUM_ENV_FILE` | environment | medium | 0.55 | USEFUL_WARNING | Optional override; not a startup blocker |
| Deplot | `/opt/homebrew/bin/zcli` | locality | high | 0.90 | TRUE_POSITIVE | Machine-specific Homebrew path in `backend/app/services/zerops.py` |
| Deplot | `PLAYWRIGHT_SKIP_WEBSERVER` | environment | medium | 0.75 | FALSE_POSITIVE | `playwright.config.ts` is e2e, not runtime |
| Deplot | Undeclared `playwright` | toolchain | medium | 0.75 | FALSE_POSITIVE | Declared as `@playwright/test` |
| Mend | Undeclared `uvicorn` | toolchain | medium | 0.75 | FALSE_POSITIVE | `uvicorn[standard]` in requirements; script uses `.venv/bin/uvicorn` |
| Ripple | `afconvert` | toolchain | medium | 0.90 | USEFUL_WARNING | Real macOS video tool in `video/scripts/gen-vo.sh`; wrongly confirmed |
| Ripple | `dsa`, `except`, `has_skill`, `name`, `req` | toolchain | medium | 0.90 | FALSE_POSITIVE | Tokens from `python3 -c` blocks in `scripts/verify-phase4.sh` |
| Ripple | `minimax-m3` | toolchain | medium | 0.90 | FALSE_POSITIVE | Basename of `RIPPLE_MODEL=fireworks/minimax-m3` |
| Ripple | `require` | toolchain | medium | 0.90 | FALSE_POSITIVE | Prose `require >= 22.14` in `scripts/check-env.sh` |
| Ripple | `mcp`, `sandbox` | toolchain | medium | 0.75 | FALSE_POSITIVE | Same embedded-Python / script-token class |
| Ripple | `NETSUITE_BASE_URL`, `NETSUITE_ROLE_ID` | environment | medium | 0.75 | USEFUL_WARNING | Optional adapter env in `mcp-server/src/adapters/factory.ts` |
| Ripple | `RIPPLE_POLICIES`, `RIPPLE_STATUS_MAP` | environment | medium | 0.55 | USEFUL_WARNING | Config overrides, not startup-blocking |

Pre-tune HIGH/MEDIUM inspected: **22**, plus the confirmed low-severity dataset zip.

| Class | Count (HIGH/MEDIUM + confirmed zip) |
| --- | ---: |
| TRUE_POSITIVE | 4 |
| USEFUL_WARNING | 7 |
| FALSE_POSITIVE | 12 |
| AMBIGUOUS | 0 |

Additional pre-tune drift (not scored findings, still wrong):

- continuum `make this` / `make the` from English prose
- continuum `documented_but_unused: redis, mysql` from dataset/fixture docs

## What was wrong

Two implementation bugs produced most of the over-confidence:

1. **Toolchain over-scoring** in `_join_toolchain`: every undeclared binary was marked `in_startup=True` and `independent_source_kinds=2`. A token in a `.sh` file is one source, not two. That yielded ~0.90 `confirmed_trap` from a single script mention.
2. **Readiness exaggeration**: any `confirmed_trap` became `high_risk`, so Ripple looked unsafe because of `except` / `dsa`.

Extractor bugs confirmed by the matrix:

- `make [\w.-]+` matched English (`make this`)
- requirements extras (`uvicorn[standard]`) were not normalized
- `.venv/bin/` and `VAR=value` prefixes were treated as binaries
- `python3 -c` bodies were parsed as shell
- `playwright.config.*` was SOURCE/CONFIG, so `PLAYWRIGHT_*` fired
- `@playwright/test` did not satisfy a `playwright` binary
- service words in dataset prose became `documented_but_unused`
- later, `;` inside `echo "..."` and `|` inside `/dev/null` produced `retry` / `null`

Scoring weights were not changed. The additive model was not the problem.

## General fixes (no repo-name denylists)

| Fix | Where | Regression test |
| --- | --- | --- |
| One script mention = one source; `in_startup=False` | `analysis/join.py` | `test_single_undeclared_binary_is_likely_not_confirmed` |
| `high_risk` only for startup-blocking confirmed traps (env/services/artifacts, or high locality) | `analysis/readiness.py` | `test_toolchain_confirmed_is_not_high_risk` (env confirmed still `high_risk`) |
| Strip extras on requirements names | `extractors/manifests.py` | `test_venv_local_uvicorn_extra_is_declared` |
| Skip `.venv/bin/`, `VAR=value`, Python-like lines, `python3 -c` bodies; normalize scoped packages | `extractors/toolchain.py` | `test_python_c_block_*`, `test_env_assignment_*`, `test_playwright_config_*` |
| Skip `require` version prose | `extractors/toolchain.py` | `test_require_version_prose_is_not_a_binary` |
| Quote-aware command split; skip `echo`/`printf`; strip redirections | `extractors/toolchain.py` | `test_quoted_echo_text_*`, `test_dev_null_redirect_*` |
| `playwright.config.*` and `*.spec.ts` are TEST | `inventory/classify.py` | `test_classify_common_paths`, `test_playwright_config_env_is_test_only` |
| `make` only in command context; English stopwords | `extractors/docs.py` | `test_docs_skips_english_make_and_fixture_services` |
| Service mentions only from setup-primary docs | `extractors/docs.py` | `test_fixture_dataset_prose_is_not_unused_service` |

Real extras kept: uninitialized submodule, missing dataset zip, `/opt/homebrew/bin/zcli`, `afconvert`, `say`, undocumented adapter env, PowerShell-only bootstrap.

## Post-tune HIGH/MEDIUM matrix

| Repo | Readiness | Confirmed | Likely | Assumptions | HIGH/MEDIUM remaining |
| --- | --- | ---: | ---: | ---: | --- |
| clone-trap | n/a (not a git repo) | — | — | — | Fail-closed |
| change-neighbor | `ready` | 0 | 0 | 0 | none |
| merge-memory | `ready` | 0 | 0 | 0 | none |
| Mend | `ready` | 0 | 0 | 0 | none (`uvicorn` gone) |
| continuum | `high_risk` | 1 | 3 | 1 | zip (confirmed, low), submodule, powershell, OS scripts, `CONTINUUM_ENV_FILE` |
| Deplot | `high_risk` | 1 | 0 | 0 | `/opt/homebrew/bin/zcli` only |
| Ripple | `hidden_assumptions` | 0 | 4 | 4 | `NETSUITE_*`, `afconvert`, `say`, `RIPPLE_*` |

Post-tune HIGH/MEDIUM false positives: **0**.

Playwright env, `uvicorn`, `make this`, redis/mysql drift, and the shell-token flood are gone.

## Tests

Baseline: **30 passed**.

Final: **41 passed** (`PYTHONPATH=src .venv/bin/python -m pytest -q`).

Play vendor sync: `tests/test_play_sync.py` still requires `play/resources/clone_trap/` to match `src/clone_trap/` byte-for-byte. Re-vendored after every `src/` change.

## CLI and Play contracts

| Check | Result |
| --- | --- |
| `python3 -m clone_trap --help` | Usage with `--repo`, `--json`, `--max-findings` |
| `--json \| python3 -m json.tool` | Valid JSON |
| `schema_version` | `1` |
| Empty findings | Valid (`change-neighbor` `findings: []`) |
| stderr bleed into JSON | None |
| Self on non-git tree | Exit 1, `Error: clone-trap must be run against a Git repository.` |
| `rote play lint play/main.ts` | Passed |
| Play on clone-trap | Honest failure: not a Git repository |
| Play on change-neighbor | `READY`, empty findings, “not a safety guarantee” |
| Play on continuum | `HIGH RISK`, dataset + submodule + PowerShell remain |
| `engine_root` | Absent from `play/main.ts`; vendor launcher only |
| Skill | Agent investigates cited files; does not auto-edit the target repo |

Play preflight requires `python3 >= 3.10` on `PATH`. System `/usr/bin/python3` (3.9.6) is rejected; Homebrew 3.14 satisfies it. That is an environment constraint, not a product defect.

## Remaining limitations

Documented as limitations, not deny-lists:

- Ignored dataset files can be `confirmed_trap` with **low** severity. Continuum’s zip still correctly drives `high_risk` because artifacts are startup-blocking.
- Uninitialized submodules stay `likely_trap` at confidence 0.80 (verdict assigned before a display floor). Still HIGH and useful.
- `afconvert` / `say` are real optional macOS video tools, not clone blockers. They are `likely_trap`, not `high_risk`.
- Optional adapter env (`NETSUITE_*`) is a useful warning, not a confirmed trap.
- Shell parsing is still heuristic. Further quote/redirect edge cases should be fixed as patterns, not repo names.
- Static analysis cannot see native libraries or compile-time failures.
- This workspace is not itself a Git repository, so self-scan fail-closes.

README limitations were not rewritten; no new ecosystem gap was proven.

## Recommended next action

Do not commit or publish from this phase. A correct `ready` on change-neighbor and Mend is more valuable than inventing problems.

Ship locally as-is. If another pass happens, prefer artifact severity for ignored required datasets and a cleaner submodule verdict — only with synthetic tests.
