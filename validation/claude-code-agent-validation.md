# Claude Code Agent Validation

Recorded 2026-09-06. Stopped after validation. No production source changes, no republish, no commit.

## Environment

| Item | Value |
| --- | --- |
| Claude Code | `2.1.263` (`/Users/apple/.local/bin/claude`) |
| Auth | Working for `claude -p` (not `--bare`) |
| Model in sessions | `claude-sonnet-5` |
| Rote | `0.80.0` |
| `python3` | `/usr/local/bin/python3` 3.14.7 (`python` not on PATH) |
| Claude user skills | Rote/Play only. **No** change-neighbor / merge-memory / clone-trap |
| Cursor skills | merge-memory and clone-trap only; not loaded by Claude Code |

Details: `validation/claude-agent-environment.md`  
CLI: `validation/claude-cli-validation.md`  
Published Plays: `validation/claude-play-command-validation.md`  
Prompts + traces: `validation/claude-agent-prompts.md`  
UX scores: `validation/claude-agent-ux-review.md`

Validation repos used: Mend, continuum, change-neighbor, clone-trap (trivial README check only).

## Plays Tested

| Play | Published URI | Agent path used |
| --- | --- | --- |
| change-neighbor | `https://play.modiqo.ai/maannaaan/change-neighbor@0.1.2` | Not proven in agent tests. CLI is `scripts/change_neighbor.py` |
| merge-memory `0.1.0` | `https://play.modiqo.ai/maannaaan/merge-memory@0.1.0` | Local `python -m merge_memory` with `engine` venv. Play needs `engine_root` |
| clone-trap `0.1.0` | `https://play.modiqo.ai/maannaaan/clone-trap@0.1.0` | Local `python -m clone_trap --repo`. Play is self-contained |

Claude never called `rote play run` in these sessions.

## Test Matrix

| Test | Tool | Explicit/Natural | Invoked | Useful | False Claims | Repo Modified | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | change-neighbor | Explicit | Unproven | Yes | Some | No | PARTIAL |
| B | change-neighbor | Natural | No | Code map | No | No | FAIL |
| C | merge-memory | Explicit | Yes | Yes | No | No | PASS |
| D | merge-memory | Explicit | Yes | Yes | No | No | PASS |
| E | clone-trap | Explicit | Yes | Yes | Mild wording | No | PASS |
| F | clone-trap | Explicit | Yes | Yes | No | No | PASS |
| G | clone-trap | Natural | No | Manual audit | No | No | FAIL |
| H | none | Trivial | No (correct) | Yes | No | No | PASS |
| I | both history Plays | Conceptual | No | Git fallback | Mild | No | FAIL |
| J | neighbor + clone-trap | Conceptual | No | Git fallback | No | No | FAIL |

**PASS 5 · PARTIAL 1 · FAIL 4 · PENDING 0**  
Real agent experiments: **10**.

## Explicit Invocation Results

When the prompt named the Play **and included the CLI command**:

- **merge-memory (C, D):** invoked, parsed JSON, treated empty history as absence not safety. Did not invent risk. Did not claim guaranteed failure.
- **clone-trap (E, F):** invoked, mapped readiness, kept confirmed vs likely vs assumption. Negative control stayed READY. Did not edit the repo.

When the prompt named change-neighbor **without a captured command** (A):

- Plan quality was good (tests, demo/JWT cluster, schemas).
- Saved session is `--output-format json` with **no Bash trace**.
- Cannot claim the skill or CLI ran. PARTIAL.

## Natural Trigger Results

| Test | Prompt gist | Skill fired? | Play ran? |
| --- | --- | --- | --- |
| B | Safe auth implementation plan | No | No |
| G | Open-source / other developer can clone | No | No |
| H | README heading typo | No | No (correct) |
| I | Co-change then historical bugs | No | No |
| J | Co-change + clone/setup assumptions | No | No |

`--add-dir` on all three engine trees did not cause discovery.

This is the strongest finding in the validation: **without a Claude Code skill, these Plays do not enter the agent loop.**

## Negative Controls

- **F (clone-trap on change-neighbor):** READY. No fabricated traps. Success.
- **D (merge-memory on LICENSE):** empty. Continued. Success.
- **H (trivial heading):** no Play spend. Success.

A clean or empty result was not “fixed up” to look interesting.

## Trivial Change Behavior

Test H: Claude grepped, saw `## Limitations` already, stopped. Zero Play invocations. Matches the skip rule in the Cursor skills even though those skills were not loaded.

## Multi-Play Reasoning

Tests I and J are **not** evidence that the Plays complement each other. The agent never ran them.

What happened instead:

- I reconstructed co-change and the stale-JWT incident from `git log` / `git show`. Useful, but that is Git, not Merge Memory + change-neighbor.
- J reconstructed Makefile/docs drift and HydraDB portability issues from `git` + file reads. Overlaps Clone Trap, but is not Clone Trap.

Ideal sequence (affected files → change-neighbor → merge-memory → plan) was **not** observed.

## Failures

| Kind | What failed |
| --- | --- |
| Skill trigger | B, G, I, J |
| Proven change-neighbor CLI in-agent | A (untraced) |
| File-set selection | C queried only `auth.py`; missed the incident that appears when `auth_jwt.py` is included |
| Agent wording | E “breaks”; I “will likely reproduce this exact incident” |
| Play vs CLI | Agents never used public Rote URIs |

No engine crash, no hung process, no hallucinated JSON from a failed command.

## False Positives

- Clone Trap negative control: none invented.
- Merge Memory empty files: none invented.
- Self-source clone-trap false flags (mongodb/mysql in extractor strings) were **not** re-run as an agent demo.

## False Negatives

- Natural sessions that *should* have used a Play (B, G, I, J) if a skill existed.
- C: empty Merge Memory on `auth.py` alone is correct for that path, but incomplete for “this area.”
- A: if the tool did not run, the REVIEW ratios may be reconstructed from git and presented as tool output.

## Agent Comprehension

When output was actually produced by an engine (C, D, E, F):

- Empty arrays → continue, no invented risk. **Good.**
- HIGH RISK + finding classes → used in the report. **Good.**
- READY → accepted as a successful clean result. **Good.**
- Evidence vs guarantee: F stated it; E slipped into “breaks.” **Mostly good.**
- Current-code vs history: C distinguished “not in the index” from “safe.” **Good.**

When the agent used raw git (I, J, G): comprehension of the *repository* was strong; comprehension of the *Plays* was never tested.

## UX Assessment

See `validation/claude-agent-ux-review.md`.

| Play | Mean (1–5) | Blocker |
| --- | --- | --- |
| change-neighbor | 2.8 | No skill; script path; `--base-ref` footgun |
| merge-memory | 3.7 | No Claude skill; no `--repo`; `python` vs `python3` |
| clone-trap | 3.8 | No Claude skill; otherwise the clearest CLI |

## Recommended Skill Improvements

Do **not** change production engines for these. Skill/install work only, and only when asked:

1. Add Claude Code skills for all three Plays (change-neighbor has none even for Cursor).
2. Put copy-pasteable `python3` / venv commands and `--json` in the skill.
3. Teach merge-memory: `cd` to target, no `--repo`, pass the file *set*.
4. Teach change-neighbor: `--base-ref` on a clean tree.
5. Keep clone-trap’s “appears to require” language in the skill body.
6. Align skill `description` with the natural phrases in B and G.
7. Re-run B, G, I, J after skills exist. Those four are the real trigger experiments.

---

## Issue classes (do not mix)

### A. Production bugs

None found in these agent sessions that require an engine change.

Already-known engine limitations (not new): merge-memory has no `--repo`; change-neighbor empty-on-clean-tree; clone-trap can false-flag its own extractor source if run on itself.

### B. Skill / prompt problems

- No Claude Code skills.
- Cursor skills invisible to Claude.
- change-neighbor has no skill file.
- merge-memory skill still says `python -m`.
- Agents over-claim (“breaks”, “will reproduce”) unless the prompt repeats the evidence rule.
- Multi-play complementarity not exercised because tools were never selected.

### C. Environment issues

- `python` missing from PATH.
- System `/usr/bin/python3` is 3.9.6; Play preflight wants ≥3.10.
- Unattended Claude needs `bypassPermissions` (or equivalent) to actually run Bash.
- `--output-format json` hides tool traces (Test A evidence gap).
- continuum working tree was already dirty; not caused by these sessions.

### D. Expected limitations

- Empty Merge Memory is valid.
- READY Clone Trap is valid.
- Trivial docs edits should skip Plays (H did).
- Static history tools cannot prove a future change will fail.
- Natural trigger tests cannot pass until skills are installed. That is an environment/skill fact, not a silent engine failure.

## Bottom line

The engines work when Claude is handed the command. They do **not** participate in a normal Claude Code session today. That is the integration gap. It is more important than any of the PASS cells on C–F.
