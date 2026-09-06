# Contributing

Fork the repository, create a branch, and open a pull request against `main`.

1. Keep `src/clone_trap/` and `play/resources/clone_trap/` in sync (same package files).
2. Run `PYTHONPATH=src python3 -m pytest -q` before you push.
3. Do not commit `__pycache__`, `.pyc`, `.DS_Store`, `.venv/`, or Rote sidecars (`.rote-flow-lint.json`, `.rote-release.lock`).
4. Keep language cautious: repositories **appear to require** something; a clean clone **may** fail. Do not claim a clone will fail or that a repository is incomplete.
5. Do not add network calls, adapters, target-repo code execution, or third-party runtime dependencies.

Play frontmatter `version` is the Play version. `rote play info` may show `0.80.0`; that is `rote_version`.
