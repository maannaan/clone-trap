"""Synthetic repositories covering the planned validation fixtures."""

from clone_trap.analysis import analyze_repository
from clone_trap.models.enums import Category, Verdict

from tests.conftest import commit_all, write


def _ids(report, verdict=None, category=None):
    findings = report.findings
    if verdict is not None:
        findings = [item for item in findings if item.verdict == verdict]
    if category is not None:
        findings = [item for item in findings if item.category == category]
    return [item.id for item in findings]


def test_fixture_clean_stdlib(git_repo):
    write(git_repo, "README.md", "# Tool\n\npython3 app.py\n")
    write(git_repo, "app.py", "print('hello')\n")
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    assert report.readiness == "ready"
    assert report.findings == []
    assert report.bootstrap_actions == []


def test_fixture_undocumented_env(git_repo):
    write(git_repo, "README.md", "# App\n\nnpm install\nnpm run dev\n")
    write(
        git_repo,
        "backend/app/config.py",
        "import os\n\nREDIS_URL = os.environ['REDIS_URL']\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    confirmed = [item for item in report.findings if item.verdict == Verdict.CONFIRMED_TRAP]
    assert any("REDIS_URL" in item.title for item in confirmed)
    assert report.readiness == "high_risk"
    assert any("REDIS_URL" in item.title for item in report.findings)


def test_fixture_documented_env(git_repo):
    write(
        git_repo,
        "README.md",
        "# App\n\nCopy `.env.example` to `.env`.\nRequired: `REDIS_URL`.\n",
    )
    write(git_repo, ".env.example", "REDIS_URL=redis://localhost:6379\n")
    write(
        git_repo,
        "backend/app/config.py",
        "import os\n\nREDIS_URL = os.environ['REDIS_URL']\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    traps = [
        item
        for item in report.findings
        if item.verdict in {Verdict.CONFIRMED_TRAP, Verdict.LIKELY_TRAP}
        and "REDIS_URL" in item.title
    ]
    assert traps == []


def test_fixture_redis_without_compose(git_repo):
    write(git_repo, "README.md", "# App\n\npip install -r requirements.txt\n")
    write(git_repo, "requirements.txt", "flask\n")
    write(
        git_repo,
        "backend/app/settings.py",
        "import os\nimport redis\n\ncache = redis.from_url(os.environ['REDIS_URL'])\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    assert any(
        item.category == Category.SERVICES
        and item.verdict in {Verdict.CONFIRMED_TRAP, Verdict.LIKELY_TRAP}
        and "redis" in item.title.lower()
        for item in report.findings
    )


def test_fixture_redis_with_compose(git_repo):
    write(git_repo, "README.md", "# App\n\ndocker compose up -d\n")
    write(
        git_repo,
        "docker-compose.yml",
        "services:\n  redis:\n    image: redis:7\n    ports:\n      - '6379:6379'\n",
    )
    write(
        git_repo,
        "backend/app/settings.py",
        "import redis\n\ncache = redis.Redis(host='localhost', port=6379)\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    traps = [
        item
        for item in report.findings
        if item.category == Category.SERVICES
        and item.verdict in {Verdict.CONFIRMED_TRAP, Verdict.LIKELY_TRAP}
    ]
    assert traps == []


def test_fixture_generated_undocumented(git_repo):
    write(git_repo, "README.md", "# App\n\nnpm install\n")
    write(git_repo, ".gitignore", "generated/\n")
    write(git_repo, "src/app.py", "from Path('generated/schema.py')\nDATA = open('generated/schema.py')\n")
    write(git_repo, "generated/schema.py", "SCHEMA = {}\n")
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    assert any(
        item.category == Category.ARTIFACTS
        and item.verdict in {Verdict.CONFIRMED_TRAP, Verdict.LIKELY_TRAP}
        for item in report.findings
    )


def test_fixture_generated_documented(git_repo):
    write(git_repo, "README.md", "# App\n\nnpm install\nnpm run generate\n")
    write(
        git_repo,
        "package.json",
        '{"name":"app","scripts":{"generate":"prisma generate"},"devDependencies":{"prisma":"5.0.0"}}\n',
    )
    write(git_repo, ".gitignore", "generated/\n")
    write(git_repo, "src/app.ts", "import { schema } from './generated/schema'\n")
    write(git_repo, "generated/schema.ts", "export const schema = {}\n")
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    traps = [
        item
        for item in report.findings
        if item.category == Category.ARTIFACTS
        and item.verdict in {Verdict.CONFIRMED_TRAP, Verdict.LIKELY_TRAP}
    ]
    assert traps == []


def test_fixture_absolute_path(git_repo):
    write(git_repo, "README.md", "# App\n\npython3 app.py\n")
    write(
        git_repo,
        "backend/app/config.py",
        "DATA = '/Users/alex/projects/secret/data.json'\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    assert any(item.category == Category.LOCALITY for item in report.findings)


def test_fixture_version_mismatch(git_repo):
    write(git_repo, "README.md", "# App\n\npip install -e .\n")
    write(git_repo, ".python-version", "3.11\n")
    write(
        git_repo,
        "pyproject.toml",
        '[project]\nname = "app"\nrequires-python = ">=3.12"\n',
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    assert any(
        item.category == Category.TOOLCHAIN and "python" in item.title.lower()
        for item in report.findings
    )


def test_fixture_dataset_prose_is_not_unused_service(git_repo):
    write(git_repo, "README.md", "# App\n\npython3 app.py\n")
    write(git_repo, "app.py", "print('hello')\n")
    write(
        git_repo,
        "docs/dataset.md",
        "The enterprise dump includes redis and mysql sample rows.\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    unused = " ".join(report.documentation_drift.documented_but_unused).lower()
    assert "redis" not in unused
    assert "mysql" not in unused


def test_fixture_localhost_only_in_tests(git_repo):
    write(git_repo, "README.md", "# App\n\npython3 -m pytest\n")
    write(git_repo, "app.py", "def add(a, b):\n    return a + b\n")
    write(
        git_repo,
        "tests/test_app.py",
        "def test_health():\n    url = 'http://localhost:6379/health'\n    assert url\n",
    )
    commit_all(git_repo)
    report = analyze_repository(str(git_repo))
    assert not any(item.category == Category.SERVICES for item in report.findings)
    assert report.readiness in {"ready", "mostly_portable"}
