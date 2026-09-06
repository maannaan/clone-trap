import json
import subprocess
import sys
from pathlib import Path

from clone_trap.cli import main

from tests.conftest import commit_all, write


def test_cli_json_empty_repo(git_repo, capsys):
    write(git_repo, "README.md", "# Clean\n\npython3 app.py\n")
    write(git_repo, "app.py", "print('hello')\n")
    commit_all(git_repo)
    code = main(["--repo", str(git_repo), "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == 1
    assert payload["readiness"] in {
        "ready",
        "mostly_portable",
        "hidden_assumptions",
        "high_risk",
    }
    assert isinstance(payload["findings"], list)


def test_cli_rejects_non_repo(tmp_path, capsys):
    code = main(["--repo", str(tmp_path / "missing")])
    assert code == 1
    assert "Error:" in capsys.readouterr().err


def test_module_invocation(git_repo):
    write(git_repo, "README.md", "# x\n")
    write(git_repo, "app.py", "print(1)\n")
    commit_all(git_repo)
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "-m", "clone_trap", "--repo", str(git_repo), "--json"],
        cwd=root,
        env={**__import__("os").environ, "PYTHONPATH": str(root / "src")},
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == 1
