from clone_trap.extractors import extract_facts
from clone_trap.extractors.yaml_lite import mapping_under, parse_lines, values_for
from clone_trap.inventory import build_inventory

from tests.conftest import commit_all, write


def test_env_extractor_detects_defaults(git_repo):
    write(
        git_repo,
        "src/config.py",
        "import os\nPORT = os.getenv('PORT', '8000')\nSECRET = os.environ['API_SECRET']\n",
    )
    write(git_repo, ".env.example", "API_SECRET=\n")
    commit_all(git_repo)
    facts = extract_facts(build_inventory(str(git_repo)))
    names = {item.name: item for item in facts.env_usages}
    assert names["PORT"].has_default is True
    assert names["API_SECRET"].has_default is False
    assert "API_SECRET" in facts.env_example_names


def test_docs_extractor_reads_setup(git_repo):
    write(git_repo, "README.md", "# App\n\n```\nnpm install\nnpm run dev\n```\nNeeds REDIS_URL and Postgres.\n")
    commit_all(git_repo)
    facts = extract_facts(build_inventory(str(git_repo)))
    assert any("npm install" in command for command in facts.doc_commands)
    assert "REDIS_URL" in facts.doc_env_names
    assert "postgres" in facts.doc_services


def test_docs_skips_english_make_and_fixture_services(git_repo):
    write(
        git_repo,
        "README.md",
        "# App\n\nPlease make this work on a clean clone.\nThen make the full setup.\n",
    )
    write(
        git_repo,
        "docs/dataset.md",
        "The fixture dump mentions redis and mysql but they are not setup steps.\n",
    )
    commit_all(git_repo)
    facts = extract_facts(build_inventory(str(git_repo)))
    assert not any(command.lower().startswith("make ") for command in facts.doc_commands)
    assert "redis" not in facts.doc_services
    assert "mysql" not in facts.doc_services


def test_compose_extractor(git_repo):
    write(
        git_repo,
        "docker-compose.yml",
        "services:\n  redis:\n    image: redis:7\n    ports:\n      - '6379:6379'\n    environment:\n      REDIS_PASSWORD: x\n",
    )
    commit_all(git_repo)
    facts = extract_facts(build_inventory(str(git_repo)))
    assert facts.compose_services
    assert facts.compose_services[0].name == "redis"
    assert "6379" in facts.compose_services[0].ports


def test_yaml_lite_services():
    text = "services:\n  db:\n    image: postgres:16\n    environment:\n      POSTGRES_PASSWORD: x\n"
    lines = parse_lines(text)
    services = mapping_under(lines, "services")
    assert services[0][0] == "db"
    assert values_for(services[0][1], "image") == ["postgres:16"]
