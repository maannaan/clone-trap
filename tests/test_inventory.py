from clone_trap.inventory import build_inventory
from clone_trap.inventory.classify import classify_path
from clone_trap.models.enums import FileClass

from tests.conftest import write


def test_walk_skips_vendor_dirs(git_repo):
    write(git_repo, "src/app.py", "print('ok')\n")
    write(git_repo, "node_modules/left-pad/index.js", "module.exports = 1\n")
    write(git_repo, ".venv/lib/python.py", "x = 1\n")
    inventory = build_inventory(str(git_repo))
    paths = {item.path for item in inventory.items}
    assert "src/app.py" in paths
    assert not any(path.startswith("node_modules/") for path in paths)
    assert not any(path.startswith(".venv/") for path in paths)
    assert any("node_modules" in name for name in inventory.skip_dirs_seen)


def test_classify_common_paths():
    assert classify_path("README.md") == FileClass.DOCS
    assert classify_path(".env.example") == FileClass.ENV_EXAMPLE
    assert classify_path("docker-compose.yml") == FileClass.COMPOSE
    assert classify_path(".github/workflows/ci.yml") == FileClass.CI
    assert classify_path("package.json") == FileClass.MANIFEST
    assert classify_path("tests/test_app.py") == FileClass.TEST
    assert classify_path("src/app.py") == FileClass.SOURCE
    assert classify_path("scripts/change_neighbor.py") == FileClass.SOURCE
    assert classify_path("scripts/setup.sh") == FileClass.SCRIPT
    assert classify_path("backend/app/config.py") == FileClass.CONFIG
    assert classify_path("frontend/playwright.config.ts") == FileClass.TEST
    assert classify_path("e2e/login.spec.ts") == FileClass.TEST
