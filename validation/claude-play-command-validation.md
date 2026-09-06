# Claude Play command validation

Recorded 2026-09-06. `rote` 0.80.0. Handle `maannaaan`.

One inspect attempt failed with `play authentication expired`; a later `rote whoami` and inspect/run succeeded. Transient.

## Inspect

| Play | URI | Visibility | Ready | Inputs | Writes | Credentials | engine_root |
| --- | --- | --- | --- | --- | --- | --- | --- |
| merge-memory@0.1.0 | https://play.modiqo.ai/maannaaan/merge-memory@0.1.0 | public | yes | `repo_path` required; `max_commits` 500; `files` optional; `engine_root` optional | none | none | declared optional; **required for execution** |
| clone-trap@0.1.0 | https://play.modiqo.ai/maannaaan/clone-trap@0.1.0 | public | yes | `repo_path` required; `max_findings` 20 | none | none | none |
| change-neighbor@0.1.2 | https://play.modiqo.ai/maannaaan/change-neighbor@0.1.2 | public | yes | `repo_path` + history/confidence/tests/surfaces/`base_ref` | none | none | none |

clone-trap package projection: 49 files, 2 tools. Self-contained.

## Runs (`--yes` for non-interactive setup)

| Run | Result |
| --- | --- |
| clone-trap URI → change-neighbor | `READY`. Honest empty. No `engine_root`. |
| clone-trap URI → continuum | `HIGH RISK`. Dataset zip, uninitialized submodule, PowerShell bootstrap. |
| merge-memory URI → merge-memory checkout + `engine_root` | Success. Clean tree: “No changed files” / “No relevant historical incidents.” Honest. |
| merge-memory URI → Mend + `engine_root` | Success. Same empty-current-change honesty (Mend working tree clean). |

clone-trap public URI does not depend on the clone-trap checkout `src/`.

merge-memory documents `engine_root` on inspect. Without it, prior validation showed fail-closed (not re-broken here).

Failures: inspect once expired; recovered. No crash, no invented traps on the negative control.
