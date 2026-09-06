# Final Play publication validation

Date: 2026-09-06 (local). Rote 0.80.0. Handle `maannaaan`.

## Verdict

**PUBLISHED AND VALIDATED**

GitHub `v0.1.0` at `b698a4c`, registry upload, public inspect, and public URI runs on both controls all succeeded. Self-scan extractor-pattern noise remains a documented limitation, not a publication failure.

## 1. Date/time of validation

2026-09-06. Local Play runs `run_20260906_141255` / `run_20260906_141257`. Public URI runs immediately after registry push.

## 2. Git commit used

`b698a4ce74770bfc8b25f41f1739f1d125f4bd60` (`docs: clarify Play is unpublished and record Phase 4 readiness`)

## 3. Git tag

`v0.1.0` → `b698a4c` (`git rev-parse 'v0.1.0^{commit}'`). No new tag was created.

## 4. Test count

`PYTHONPATH=src .venv/bin/python -m pytest -q` — **41 passed**, 0 failed.

## 5. Local Play lint result

`rote play lint play/main.ts` — passed.

## 6. Local negative control result

`rote play run play/main.ts repo_path=.../change-neighbor`

`READY`. Empty findings. Footer: not a safety guarantee. change-neighbor `git status --porcelain` empty after.

## 7. Local positive control result

`rote play run play/main.ts repo_path=.../continuum`

`HIGH RISK TO CLONE`. Missing `all_documents.zip`, uninitialized `hydradb/hydradb-repo`, undeclared `powershell`, PowerShell-only bootstrap, `CONTINUUM_ENV_FILE`. Continuum porcelain unchanged vs pre-scan snapshot.

## 8. Published Play reference

`maannaaan/clone-trap@0.1.0`

## 9. Public Play URI

`https://play.modiqo.ai/maannaaan/clone-trap@0.1.0`

## 10. Bootstrap URI

`https://play.modiqo.ai/install?play=maannaaan/clone-trap@0.1.0`

Registry fields: visibility `public`, version `0.1.0`, `play_run_eligible: true`, `privileged_access: process`, `status: released`, `size_bytes: 33320`.

## 11. Public inspect result

`rote play inspect https://play.modiqo.ai/maannaaan/clone-trap@0.1.0`

- Visibility: public
- Ready to run: yes
- Description matches local frontmatter
- Inputs: `repo_path` required, `max_findings` optional default 20
- Privileged access: process
- Write permissions: none declared
- Credentials / authentication: not required
- Services: none
- Package projection: 49 files, 2 tools (python3, git)
- No `engine_root`

## 12. Public URI negative control result

`rote play run https://play.modiqo.ai/maannaaan/clone-trap@0.1.0 repo_path=.../change-neighbor --yes`

`READY`. No invented HIGH RISK. change-neighbor still clean.

## 13. Public URI positive control result

Same URI against continuum. `HIGH RISK TO CLONE` with the same dataset / submodule / PowerShell signals. Evidence language: “appears to require.” Continuum porcelain unchanged vs pre-scan snapshot.

The public Play did not need this checkout’s `src/` or `engine_root`.

## 14. Read-only safety confirmation

Allowlisted `git` only (`rev-parse`, `ls-files`, `check-ignore`, `submodule status`). `shell=False`. Inspect: no write permissions. Target repositories were not modified by these runs.

CLI `/tmp`: exit 1, `clone-trap must be run against a Git repository.`

## 15. Known limitations

- Static analysis cannot see native libraries or compile-time failures.
- Optional / dynamic fallbacks may look required.
- Documentation mentions are heuristic.
- Empty `ready` is not a safety guarantee.
- Ignored datasets can be confirmed at low severity (continuum zip).
- **Self-scan:** running Clone Trap on this repository can report mongodb/mysql/rabbitmq traps because extractor files contain those pattern strings. That is not a clean-clone requirement. Do not demo the product on its own source.

## Other pre-publication checks

| Check | Result |
| --- | --- |
| Vendor sync `src/clone_trap` ↔ `play/resources/clone_trap` | 38/38 identical |
| JSON `schema_version` | 1 |
| change-neighbor JSON findings | `[]`, stderr empty |
| Working tree at publish | clean `main` = `origin/main` |
| Extra Git tag | none created |

Production engine was not changed. Publication was performed once.
