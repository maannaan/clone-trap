# Claude CLI contract validation

Recorded 2026-09-06. Engines were not redesigned.

## Commands an agent should run

### change-neighbor

Canonical (from its README):

```bash
python3 /Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/change-neighbor/scripts/change_neighbor.py \
  --repo /absolute/path/to/git/repo
python3 .../scripts/change_neighbor.py --repo /absolute/path/to/git/repo --json
python3 .../scripts/change_neighbor.py --repo /absolute/path/to/git/repo --base-ref HEAD~5 --history-limit 30 --json
```

`--base-ref` is required when the working tree is clean; otherwise it analyzes uncommitted diffs and can return empty neighbors.

### merge-memory

No `--repo` flag. `cd` to the target working tree. `python` is not on PATH; use `python3` or the project venv.

```bash
cd /absolute/path/to/target-repo
PYTHONPATH=/Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/merge-memory/src \
  /Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/merge-memory/.venv/bin/python \
  -m merge_memory --json -- path/to/file.py
```

### clone-trap

```bash
PYTHONPATH=/Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/clone-trap/src \
  /Users/apple/Desktop/Manan/Hackathons/Modiqo/projects/clone-trap/.venv/bin/python \
  -m clone_trap --repo /absolute/path/to/git/repo
PYTHONPATH=.../clone-trap/src python3 -m clone_trap --repo /absolute/path/to/git/repo --json
```

## Results

| Tool | Command | Result |
| --- | --- | --- |
| change-neighbor | `--help` | Exit 0. Flags: `--repo` required, `--json`, `--base-ref`, history/confidence/tests/surfaces. |
| change-neighbor | `--repo Mend --base-ref HEAD --json` | Exit 0, valid JSON. Clean tree: `current_changes []`, `historical_commits_analyzed` 0. Honest empty. |
| change-neighbor | `--repo Mend --base-ref HEAD~5 --json` | Exit 0. 22 commits, 41 current changes, 3 neighbors. |
| merge-memory | `--help` | Exit 0. Options: files, `--base`, `--json`, `--limit`, `--max-commits`. **No `--repo`.** |
| merge-memory | `--json --repo Mend` from merge-memory cwd | **Failed.** `No such option: --repo`. |
| merge-memory | from Mend cwd, `--json -- mcp` | Exit 0. `memories []`, `incidents []`. |
| merge-memory | from Mend cwd, `--json -- backend/app/routes/auth.py backend/app/services/auth_jwt.py` | Exit 0 after ~85s. `memories 0`, `incidents 1`. stderr empty. |
| clone-trap | `--help` | Exit 0. `--repo`, `--json`, `--max-findings`. |
| clone-trap | `--repo change-neighbor` | `READY`, empty traps. |
| clone-trap | `--repo continuum --json` | `schema_version` 1, `high_risk`, 5 findings, stderr empty. |

## Agent implications

- merge-memory skill samples that say `python -m` will fail unless `python` exists or the agent uses `python3` / a venv.
- Passing `--repo` to merge-memory is a real footgun.
- change-neighbor on a clean tree without `--base-ref` looks like “no neighbors,” which is correct, not a crash.
