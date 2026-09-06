from clone_trap.analysis import analyze_repository
from clone_trap.models.enums import Category, Verdict

from tests.conftest import commit_all, write


def test_python_under_scripts_is_not_a_binary_flood(git_repo):
    write(git_repo, "README.md", "# Tool\n\npython3 scripts/tool.py\n")
    write(
        git_repo,
        "scripts/tool.py",
        "def main():\n    age_days = 0.42\n    print(age_days)\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    binaries = [
        item
        for item in report.findings
        if item.category == Category.TOOLCHAIN and "tool used" in item.title.lower()
    ]
    assert binaries == []
    assert report.readiness == "ready"


def _toolchain_titles(report) -> list[str]:
    return [
        item.title
        for item in report.findings
        if item.category == Category.TOOLCHAIN and "tool used" in item.title.lower()
    ]


def test_venv_local_uvicorn_extra_is_declared(git_repo):
    write(git_repo, "README.md", "# App\n\npip install -r requirements.txt\n")
    write(git_repo, "requirements.txt", "uvicorn[standard]>=0.32.0\n")
    write(
        git_repo,
        "scripts/serve.sh",
        "#!/bin/bash\n.venv/bin/uvicorn app:app --reload\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    assert not any("uvicorn" in title.lower() for title in _toolchain_titles(report))


def test_python_c_block_in_shell_is_not_binaries(git_repo):
    write(git_repo, "README.md", "# App\n\nbash scripts/verify.sh\n")
    write(
        git_repo,
        "scripts/verify.sh",
        "#!/bin/bash\n"
        'AGENT_MANIFEST=$(echo "$JSON" | python3 -c "\n'
        "import json, sys\n"
        "except Exception:\n"
        "    dsa = 1\n"
        "    has_skill = True\n"
        '")\n',
    )
    commit_all(git_repo)
    titles = _toolchain_titles(analyze_repository(str(git_repo)))
    blob = " ".join(titles).lower()
    assert "except" not in blob
    assert "dsa" not in blob
    assert "has_skill" not in blob


def test_env_assignment_prefix_is_not_a_binary(git_repo):
    write(git_repo, "README.md", "# App\n\nbash scripts/run.sh\n")
    write(
        git_repo,
        "scripts/run.sh",
        "#!/bin/bash\nRIPPLE_MODEL=fireworks/minimax-m3 bash worker.sh\n",
    )
    commit_all(git_repo)
    titles = _toolchain_titles(analyze_repository(str(git_repo)))
    assert not any("minimax" in title.lower() for title in titles)


def test_dev_null_redirect_is_not_a_binary(git_repo):
    write(git_repo, "README.md", "# App\n\nbash scripts/check.sh\n")
    write(
        git_repo,
        "scripts/check.sh",
        "#!/bin/bash\n"
        "if ! command -v git >/dev/null 2>&1; then\n"
        "  echo missing\n"
        "fi\n"
        "curl -sf http://127.0.0.1 >/dev/null 2>&1\n",
    )
    commit_all(git_repo)
    titles = _toolchain_titles(analyze_repository(str(git_repo)))
    assert not any("null" in title.lower() for title in titles)


def test_quoted_echo_text_is_not_a_binary(git_repo):
    write(git_repo, "README.md", "# App\n\nbash scripts/register.sh\n")
    write(
        git_repo,
        "scripts/register.sh",
        '#!/bin/bash\necho "Tools list HTTP ${CODE} (server registered; retry after MCP is running)"\n',
    )
    commit_all(git_repo)
    titles = _toolchain_titles(analyze_repository(str(git_repo)))
    assert not any("retry" in title.lower() for title in titles)


def test_require_version_prose_is_not_a_binary(git_repo):
    write(git_repo, "README.md", "# App\n\nbash scripts/check-env.sh\n")
    write(git_repo, "scripts/check-env.sh", "#!/bin/bash\necho 'require >= 22.14'\n")
    commit_all(git_repo)
    titles = _toolchain_titles(analyze_repository(str(git_repo)))
    assert not any("require" in title.lower() for title in titles)


def test_playwright_config_env_is_test_only(git_repo):
    write(git_repo, "README.md", "# App\n\nnpm install\n")
    write(
        git_repo,
        "package.json",
        '{"name":"app","scripts":{"test":"playwright test"},'
        '"devDependencies":{"@playwright/test":"1.49.0"}}\n',
    )
    write(
        git_repo,
        "frontend/playwright.config.ts",
        "export default { use: { baseURL: process.env.PLAYWRIGHT_BASE_URL } }\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    assert not any("PLAYWRIGHT_BASE_URL" in item.title for item in report.findings)
    assert not any("playwright" in title.lower() for title in _toolchain_titles(report))


def test_single_undeclared_binary_is_likely_not_confirmed(git_repo):
    write(git_repo, "README.md", "# App\n\nbash scripts/vo.sh\n")
    write(git_repo, "scripts/vo.sh", "#!/bin/bash\nafconvert -f caff input.aiff output.caf\n")
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    traps = [
        item
        for item in report.findings
        if item.category == Category.TOOLCHAIN and "afconvert" in item.title.lower()
    ]
    assert traps
    assert all(item.verdict == Verdict.LIKELY_TRAP for item in traps)
    assert all(item.verdict != Verdict.CONFIRMED_TRAP for item in traps)
    assert report.readiness != "high_risk"
