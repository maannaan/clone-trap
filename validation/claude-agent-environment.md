# Claude Code agent environment

Recorded 2026-09-06. Discovery only. No credentials printed.

## Claude Code

| Item | Value |
| --- | --- |
| Binary | `/Users/apple/.local/bin/claude` |
| Version | `2.1.263` (Claude Code) |
| Auth (`claude -p` without `--bare`) | Authenticated. Smoke prompt returned `AUTH_OK`. |
| Auth (`claude -p --bare`) | `Not logged in · Please run /login` (bare skips keychain/OAuth) |

Non-interactive flag: `-p` / `--print`. Permission bypass available via `--dangerously-skip-permissions` / `--permission-mode bypassPermissions` for unattended sessions.

## Rote

| Item | Value |
| --- | --- |
| Binary | `/Users/apple/.local/bin/rote` |
| Version | `0.80.0` |
| `rote whoami` | Account reachable (`mananpaliwal30@gmail.com`). Handle lookup returned `lookup_failed` on this run; earlier publication used `maannaaan`. |

## Python

| Item | Value |
| --- | --- |
| `python3` | `/usr/local/bin/python3` 3.14.7 |
| `python` | not on PATH |
| clone-trap venv | `/Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/clone-trap/.venv/bin/python` |
| merge-memory venv | `/Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/merge-memory/.venv/bin/python` |
| change-neighbor venv | none (stdlib script; no pip required) |

System `/usr/bin/python3` is 3.9.6. Play preflight needs ≥3.10. Prefer `/usr/local/bin` first.

## Repository paths (discovered)

| Repo | Path | Git HEAD |
| --- | --- | --- |
| change-neighbor | `/Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/change-neighbor` | `178e63a` |
| merge-memory | `/Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/merge-memory` | `5ee836c` |
| clone-trap | `/Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/clone-trap` | `8032ac0` |
| Mend | `/Users/apple/Desktop/Manan/Hackathons/Mend` | `ba7e329` |
| Ripple | `/Users/apple/Desktop/Manan/Hackathons/Ripple` | `be7267d` |
| Deplot | `/Users/apple/Desktop/Manan/Hackathons/Deplot` | `ee6077c` |
| continuum | `/Users/apple/Desktop/Manan/Continumm/continuum` | `0e6ea4e` |

## Skill / agent integration state

| Play | Cursor skill in checkout | Claude Code user skill (`~/.claude/skills`) |
| --- | --- | --- |
| change-neighbor | **absent** (no `.cursor/skills`, no `.claude/`) | **absent** |
| merge-memory | `.cursor/skills/merge-memory/SKILL.md` | **absent** |
| clone-trap | `.cursor/skills/clone-trap/SKILL.md` | **absent** |

`~/.claude/skills` contains Rote/Play skills only. Claude Code does not automatically load `.cursor/skills/`. Natural skill trigger tests must be scored against **this** environment, not an idealized one.

No `CLAUDE.md` in Mend or continuum.

## Limitations

- `python` is not on PATH; merge-memory skill examples use `python -m`. Agents must use `python3` or a venv.
- change-neighbor has no agent skill file at all.
- continuum working tree has pre-existing dirty files (unrelated to these tools).
- Unattended Claude sessions need a non-interactive permission mode to actually run Bash.
