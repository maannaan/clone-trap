# Claude Code skill integration

Recorded 2026-09-06. Skill/install work only. No production engine algorithm changes, no republish, no commit.

Prior explicit-invocation validation: [claude-code-agent-validation.md](claude-code-agent-validation.md). This file is the **natural-trigger** retest after installing Claude Code skills.

## 1. Claude Code version

| Item | Value |
| --- | --- |
| Binary | `/Users/apple/.local/bin/claude` |
| Version | `2.1.263` (Claude Code) |
| Model in sessions | `claude-sonnet-5` |
| `python3` | `/usr/local/bin/python3` 3.14.7 (`python` not on PATH) |

## 2. Skill installation mechanism

Canonical skill lives in each engine repo:

```
<repo>/.claude/skills/<name>/SKILL.md
<repo>/.claude/skills/<name>/scripts/run
```

Claude Code user install (matches Play/Rote on this machine: **per-skill symlink**, not a copy, not a symlink of the whole `skills` directory):

```bash
ln -sfn "$(pwd)/.claude/skills/<name>" ~/.claude/skills/<name>
```

Refuse to replace a non-symlink already at that name. Play and Rote entries were not modified.

Cursor loads the same files via `.cursor/skills/<name>` → `../../.claude/skills/<name>`.

**Genuine integration blocker found and fixed (launchers only):** the first natural G session invoked Clone Trap immediately, then `bash ~/.claude/skills/clone-trap/scripts/run` failed with `No module named clone_trap`. Logical `pwd` through the `~/.claude/skills/<name>` symlink resolved `ENGINE_ROOT` to `$HOME`. Launchers now use `pwd -P`. Engines were not changed.

## 3. Skill locations

| Skill | Canonical | User install | Cursor |
| --- | --- | --- | --- |
| change-neighbor | `change-neighbor/.claude/skills/change-neighbor/` | `~/.claude/skills/change-neighbor` → canonical | `.cursor/skills/change-neighbor` → canonical |
| merge-memory | `merge-memory/.claude/skills/merge-memory/` | `~/.claude/skills/merge-memory` → canonical | `.cursor/skills/merge-memory` → canonical |
| clone-trap | `clone-trap/.claude/skills/clone-trap/` | `~/.claude/skills/clone-trap` → canonical | `.cursor/skills/clone-trap` → canonical |

Every live init event listed `change-neighbor`, `merge-memory`, and `clone-trap` in `slash_commands` / `skills`.

## 4. Verified CLI commands

Do not assume `python`.

### change-neighbor

```bash
bash ~/.claude/skills/change-neighbor/scripts/run --repo /absolute/path/to/git/repo --json
bash ~/.claude/skills/change-neighbor/scripts/run \
  --repo /absolute/path/to/git/repo --base-ref HEAD~5 --history-limit 30 --json
python3 /absolute/path/to/change-neighbor/scripts/change_neighbor.py \
  --repo /absolute/path/to/git/repo --json
```

`--repo` required. Files are not CLI args. Clean tree without `--base-ref` yields honest empty neighbors.

### merge-memory

Product CLI has **no `--repo`**. Wrapper `--repo` only `cd`s, then:

```bash
bash ~/.claude/skills/merge-memory/scripts/run \
  --repo /absolute/path/to/target-repo \
  --json -- path/a.py path/b.py
cd /absolute/path/to/target-repo
PYTHONPATH=/absolute/path/to/merge-memory/src \
  python3 -m merge_memory --json -- path/a.py path/b.py
```

Query related files together.

### clone-trap

```bash
bash ~/.claude/skills/clone-trap/scripts/run --json --repo /absolute/path/to/git/repo
PYTHONPATH=/absolute/path/to/clone-trap/src \
  python3 -m clone_trap --json --repo /absolute/path/to/git/repo
```

## 5. Tests run

Fresh `claude -p` sessions. Prompts did **not** name Plays or commands. Write/Edit disallowed. `--allowedTools Bash,Read,Glob,Grep,Skill` (Skill is required to load `SKILL.md` bodies). `--add-dir` on the three engine trees for filesystem access, not discovery.

Traces: [claude-skill-sessions/](claude-skill-sessions/). First broken-launcher traces: [claude-skill-sessions/attempt1-launcher-bug/](claude-skill-sessions/attempt1-launcher-bug/).

| Test | Target | Session | Duration | Turns |
| --- | --- | --- | --- | --- |
| B | Mend | `51821c7c-b0eb-4356-a2e8-667e5dc83b58` | ~141s | 17 |
| G | continuum | `2bdf1fa2-3d7f-4913-bd90-02567e28f005` | ~211s | report + follow-up |
| I | Mend | `5bd0c8bd-7d91-4688-b5e1-d8fdd6d5197e` | ~113s | 19 |
| J | continuum | `48bed1f7-780b-48a8-b81b-609ef3d8661c` | ~112s | 22 |
| H | clone-trap | `c7fa5070-e463-4bf5-b93b-675a3d6d579b` | ~8s | 3 |

## 6. Trigger results

### Explicit invocation (historical, not re-run)

C, D, E, F from the prior report remain PASS when the command was handed over. This phase does not re-score them.

### Natural invocation (this phase)

| Test | Skill discovered | Skill tool | Engine CLI | Affected reasoning | Verdict |
| --- | --- | --- | --- | --- | --- |
| B | all three | merge-memory, then change-neighbor | **yes** both | yes (incident `e8fd949` + neighbors/tests) | **PASS** |
| G | all three | clone-trap | **yes** | yes (HIGH RISK findings, then cited-file checks) | **PASS** |
| I | all three | change-neighbor, then merge-memory | **yes** both | yes (co-change + incidents; clone-trap not forced) | **PASS** |
| J | all three | change-neighbor, then clone-trap | **yes** both | yes (setup co-change + portability traps; merge-memory not forced) | **PASS** |
| H | all three available | **none** | **none** | n/a | **PASS** (negative) |

Manual `git log` appeared as a **supplement** after engines ran (I, J). It is not counted as Play usage. Play usage is the `scripts/run` / engine CLI lines below.

### False triggers

H did not invoke any Play. B also loaded merge-memory for a “safe implementation plan” on auth; that is in-skill, not a false trigger.

## 7. PASS / PARTIAL / FAIL table

| Test | Kind | Invoked | Useful | False claims | Repo modified | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| B | natural | change-neighbor + merge-memory | yes | no “must also change”; incident taken from JSON | no | PASS |
| G | natural | clone-trap | yes | mild: “would block a clean clone” vs “appears to require” | no | PASS |
| I | natural multi | change-neighbor + merge-memory | yes | evidence language; clone-trap unused (correct) | no | PASS |
| J | natural multi | change-neighbor + clone-trap | yes | clone-trap findings used; merge-memory unused (correct) | no | PASS |
| H | negative | none | yes | none | no | PASS |

**PASS 5 · PARTIAL 0 · FAIL 0** on this natural-trigger matrix.

Attempt 1 G (archived) invoked the skill then **failed the launcher**. Not counted in the table above.

## 8. Traces / command evidence

### B

```text
Skill: merge-memory
Skill: change-neighbor
bash ~/.claude/skills/merge-memory/scripts/run --repo .../Mend --json -- \
  backend/app/routes/auth.py backend/app/services/auth_jwt.py \
  backend/app/services/tenant_context.py \
  frontend/app/api/auth/[...nextauth]/route.ts \
  frontend/middleware.ts frontend/components/SessionProviderWrapper.tsx
bash ~/.claude/skills/change-neighbor/scripts/run --repo .../Mend --base-ref HEAD~30 --json
# retried HEAD~29, HEAD~28, HEAD~8 after inspecting history length
```

Merge Memory JSON: `memories []`, **1 incident** (`e8fd949`, “Fix Judge Mode hangs and stale JWT 401 errors on production.”) because related files were queried together. Change Neighbor used `--base-ref` (clean-tree rule followed).

### G

```text
Skill: clone-trap
bash ~/.claude/skills/clone-trap/scripts/run --json --repo .../continuum
```

JSON: `readiness: high_risk`, 1 confirmed (`all_documents.zip`), likely submodule + PowerShell, environment assumption `CONTINUUM_ENV_FILE`. Agent then read `.gitmodules`, Makefile, `docs/hydradb-local.md` — verification of cited files, not a manual replacement for the engine.

### I

```text
Skill: change-neighbor
Skill: merge-memory
bash ~/.claude/skills/change-neighbor/scripts/run --repo .../Mend --json   # empty/dirty-tree path
bash ~/.claude/skills/change-neighbor/scripts/run --repo .../Mend --base-ref e8fd949~1 --json
bash ~/.claude/skills/merge-memory/scripts/run --repo .../Mend --json -- \
  backend/app/services/auth_jwt.py frontend/middleware.ts ...
```

Order: co-change skill first, then incidents. Two Merge Memory incidents (`e8fd949`, CORS `78ec4b8`). Clone Trap not invoked.

### J

```text
Skill: change-neighbor
Skill: clone-trap
bash ~/.claude/skills/change-neighbor/scripts/run --repo .../continuum --base-ref HEAD~15 --json
bash ~/.claude/skills/clone-trap/scripts/run --json --repo .../continuum
```

Agent noted the dirty tree, passed `--base-ref`, then used git history on README/Makefile because the neighbor run was anchored on dirty benchmark files — honest about that limitation. Merge Memory not invoked.

### H

Grep on README only. No Skill tool. No engine CLI.

## 9. Whether output affected reasoning

- **B:** Plan called out the stale-JWT / Judge Mode anonymous fallback from Merge Memory, and test/API neighbors from Change Neighbor. Asked which auth change was intended rather than editing.
- **G:** Ranked PowerShell HydraDB, uninitialized submodule, missing zip, undocumented env var from Clone Trap JSON, then inspected cited files.
- **I:** Combined neighbor bands with incidents; treated a non-auth commit as unrelated; said “evidence, not a required file list.”
- **J:** Used both co-change of setup docs and Clone Trap traps to scope an onboarding-doc edit. Did not treat READY/absence as a topic (findings were non-empty).

Empty / wide-tree Change Neighbor on a large `--base-ref` was not invented into a fake neighbor list. Merge Memory empty `memories` with a real incident was not treated as “safe.”

## 10. Negative control

Test H: trivial README heading. Skills were **visible** (discovery works) and **not used**. Expected.

## 11. Remaining limitations

- User-global symlink is required for sessions on Mend/continuum. Repo-local `.claude/skills` in the engine checkout would not have fired those tests.
- Launchers must use `pwd -P` when installed as `~/.claude/skills` symlinks.
- `--allowedTools` must include `Skill` or the body (commands) may not load.
- Change Neighbor `--base-ref HEAD~N` on a repo with few commits can treat most of the tree as `current_changes`. Agents may need a commit that actually touched the area (I used `e8fd949~1`).
- Agents still sometimes follow Clone Trap with extra `git`/`grep`. That is allowed verification; it is not a substitute for the engine.
- Mild over-claim risk remains (G: “would block a clean clone”).
- This phase did not re-run explicit C–F. Historical explicit PASSes still stand.
- Skills are not published; installing still needs the `ln -sfn` documented in each README.

## Production files changed

None of `src/`, `scripts/change_neighbor.py`, or `play/resources/` engines.

Skill/docs only: `.claude/skills/`, Cursor skill symlinks, README install notes, skill `scripts/run` wrappers.

## Validation files changed

- `validation/claude-code-skill-integration.md` (this file)
- `validation/claude-skill-sessions/{B,G,I,J,H}.json` plus logs
- `validation/claude-skill-sessions/attempt1-launcher-bug/` (broken first G/B/I/J)
