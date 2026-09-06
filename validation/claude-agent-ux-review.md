# Claude Code UX review

Recorded 2026-09-06 after real `claude -p` sessions A–J. Scores are 1–5. This is about agent/developer experience, not engine accuracy.

Context that dominates every score: **none of the three Plays has a Claude Code skill installed.** Cursor skills exist for merge-memory and clone-trap only. `--add-dir` on the engine checkouts was not enough for discovery.

## Scoring key

1 = agent cannot reasonably succeed without being handed the exact command  
3 = usable if the developer already knows the Play  
5 = a typical Claude Code session would do the right thing from a natural prompt

---

## change-neighbor

| # | Dimension | Score | Evidence |
| --- | --- | --- | --- |
| 1 | When to use | 2 | No Claude skill, no Cursor skill, no `CLAUDE.md` in Mend. Test B (auth-plan prompt) never considered it. |
| 2 | Command discoverable | 2 | Canonical command is `python3 …/scripts/change_neighbor.py --repo PATH`. Not a module, not on PATH. Test A named the tool; invocation still unproven. |
| 3 | Arguments obvious | 2 | `--repo` is clear. Clean trees need `--base-ref` or neighbors are empty. An agent that “succeeds” with empty output will look like a no-op. |
| 4 | Output easy to parse | 4 | CLI JSON and human output are structured (neighbors, surfaces, REVIEW). Test A’s prose used REVIEW ratios, which parse well if the tool actually ran. |
| 5 | JSON vs human | 4 | JSON is better for agents. Human output is already tabular enough. |
| 6 | Boundaries explained | 1 | No skill file at all. Nothing tells Claude “do not run on typo-only edits” except the other Plays’ Cursor skills. Test H skipped it anyway because the task was trivial, not because a skill said so. |
| 7 | Unnecessary runs | 3 | Empty-on-clean-tree is honest, but without `--base-ref` guidance agents will either skip or conclude “no neighbors.” |
| 8 | Fail clearly | 4 | CLI `--help` and invalid flags fail cleanly in Phase 2. No agent-facing crash in these sessions. |
| 9 | Would a developer trust it? | 3 | When invoked (or imitated), the neighbor list is actionable. Trust drops if the agent cannot show the command it ran (Test A). |

**Mean: 2.8**

Main gap: there is no agent contract. The engine works; Claude cannot find it.

---

## merge-memory

| # | Dimension | Score | Evidence |
| --- | --- | --- | --- |
| 1 | When to use | 3 | Cursor skill is well written (substantial change / not typos). Claude Code never loads it. Tests B and I did the historical work with `git log` instead. |
| 2 | Command discoverable | 2 | Must `cd` into the target repo. No `--repo`. Skill samples use `python -m` and `python` is not on PATH. Agent succeeded only when the prompt pasted the venv command (C, D). |
| 3 | Arguments obvious | 2 | `--repo` is a real footgun (`No such option`). File args after `--`. Easy to query one file and miss a related incident (C: `auth.py` empty; `auth.py`+`auth_jwt.py` has 1 incident). |
| 4 | Output easy to parse | 5 | `--json` with `memories` / `incidents` arrays. Tests C and D parsed empty arrays correctly. |
| 5 | JSON vs human | 5 | Prefer JSON for agents. Empty arrays are unambiguous. |
| 6 | Boundaries explained | 4 | Cursor skill: evidence not prediction; empty is valid; do not invent risk. Claude followed that **when told in the prompt** (C, D). Skill never auto-applied. |
| 7 | Unnecessary runs | 4 | LICENSE empty-history test continued. Runtime ~1–2 min on real files — acceptable for explicit use, costly if a skill over-triggers. |
| 8 | Fail clearly | 4 | Wrong flags fail. Empty history is a successful empty, not an error. |
| 9 | Would a developer trust it? | 4 | C/D were honest. Trust depends on querying the right file set, not a single path. |

**Mean: 3.7** (conditional on being handed the command)

Main gaps: cwd/`--repo` contract; `python` vs `python3`; no Claude skill; file-set selection.

---

## clone-trap

| # | Dimension | Score | Evidence |
| --- | --- | --- | --- |
| 1 | When to use | 3 | Cursor skill description matches Test G’s prompt almost exactly. Skill did not fire. Claude reinvented a weaker audit with 18 Bash calls. |
| 2 | Command discoverable | 2 | Module + `--repo` is simple **if** `PYTHONPATH` and a Python ≥3.10 are known. Natural sessions never found it despite `--add-dir`. |
| 3 | Arguments obvious | 4 | `--repo` required. `--json` optional. No cwd trap. Best CLI of the three. |
| 4 | Output easy to parse | 5 | Readiness + confirmed/likely/environment_assumption. Test E mapped this 1:1. Test F treated READY as success. |
| 5 | JSON vs human | 4 | Human output was enough for E/F. JSON is still better for programmatic ranking. |
| 6 | Boundaries explained | 4 | Cursor skill: evidence not guarantee; do not invent traps; skip typo-only. E/F honored this when prompted. H skipped without a skill. |
| 7 | Unnecessary runs | 4 | Negative control stayed empty. Skill text already forbids trivial docs edits. |
| 8 | Fail clearly | 4 | Non-git / missing `--repo` fail closed (prior phases). Agent runs E/F exited 0 with understandable text. |
| 9 | Would a developer trust it? | 4 | E matched known continuum traps. F did not decorate a clean repo. Mild agent overclaim (“breaks”) is a prompt/skill wording issue, not a false finding. |

**Mean: 3.8** (conditional on being handed the command)

Main gap: the best-written Cursor skill is invisible to Claude Code.

---

## Cross-play UX

| Observation | Impact |
| --- | --- |
| Claude Code skills list in every session: Rote/Play only | Natural triggers B and G cannot pass in this install |
| `--add-dir` ≠ skill install | I/J still never executed the engines |
| Explicit command in the prompt | C–F then invoke correctly and understand output |
| Trivial README edit | H correctly skipped all three without a skill |
| Multi-play prompts that describe *purpose* but not *names* | Agent uses `git log` / `grep`, not the Plays |
| Rote public URIs were not used by Claude | Agents used local `python -m`, not `rote play run` |
| merge-memory Play needs `engine_root`; clone-trap does not | Unfair complexity if an agent ever uses Rote instead of CLI |

---

## Recommended skill improvements (do not implement yet)

1. **Install Claude Code skills** (`~/.claude/skills` or repo `.claude/skills`) for all three Plays. Port the Cursor skill text; do not leave change-neighbor without one.
2. **Put the exact command in the skill**, using `python3` or a documented venv, absolute `PYTHONPATH`, and `--json`.
3. **change-neighbor:** tell the agent to pass `--base-ref` when the tree is clean; empty neighbors are honest, not a crash.
4. **merge-memory:** say there is no `--repo`; `cd` first; query the *set* of affected files, not one path.
5. **clone-trap:** keep “appears to require” / “evidence not guarantee” in the skill so agents do not say “will break.”
6. **Trigger text:** include the natural phrases from B/G (“safe implementation plan”, “another developer can clone”) so those prompts load the skill.
7. **Skip rules:** keep typo/docs-only exclusions; Test H shows Claude already skips when the task is tiny.
8. **Do not rely on `--add-dir`** as distribution. It does not teach the agent that a Play exists.
