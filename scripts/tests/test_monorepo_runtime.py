from __future__ import annotations

import re
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PARSER = ROOT / "document-parser"


def test_clean_parser_source_is_kept_in_this_repository() -> None:
    assert (PARSER / "pyproject.toml").is_file()
    assert (PARSER / "LICENSE.md").is_file()
    assert (PARSER / "mineru" / "cli" / "fast_api.py").is_file()

    forbidden_names = {"output", "output-local", "MinerU-master"}
    assert not any((PARSER / name).exists() for name in forbidden_names)

    ignored = subprocess.run(
        ["git", "check-ignore", "document-parser/.venv"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert ignored.returncode == 0

    tracked = subprocess.run(
        ["git", "ls-files", "document-parser"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert not any("/.venv/" in path or "/__pycache__/" in path for path in tracked)
    assert not any(path.endswith((".pyc", ".pyo")) for path in tracked)


def test_parser_model_configuration_comes_from_environment() -> None:
    config_path = PARSER / "mineru" / "utils" / "multimodal_config.py"
    source = config_path.read_text(encoding="utf-8")

    for variable in ("MULTIMODAL_API_URL", "MULTIMODAL_MODEL", "MULTIMODAL_API_KEY"):
        assert f'os.getenv("{variable}"' in source

    assert not re.search(r"sk-[A-Za-z0-9_-]{20,}", source)
    assert not re.search(
        r"(?<![0-9])(?:10|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)(?:\.\d{1,3}){2}(?![0-9])",
        source,
    )


def test_start_script_launches_all_three_services() -> None:
    script = ROOT / "start.sh"
    source = script.read_text(encoding="utf-8")

    assert script.stat().st_mode & stat.S_IXUSR
    assert "document-parser/.venv/bin/mineru-api" in source
    assert "backend/.venv/bin/uvicorn" in source
    assert "frontend/web/node_modules/.bin/vite" in source
    assert "pnpm dev" not in source
    assert 'VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:8001}"' in source
    assert "8002" in source
    assert "8001" in source
    assert "5180" in source
    assert ".env.local" in source
    assert ".runtime/logs" in source
    assert "${port}" in source
    assert "$port（" not in source
    assert 'local previous_dir="$PWD"' in source
    assert "trap '" in source
    assert "\nwait\n" in source


def test_stop_script_only_uses_runtime_pid_files() -> None:
    script = ROOT / "stop.sh"
    source = script.read_text(encoding="utf-8")

    assert script.stat().st_mode & stat.S_IXUSR
    assert ".runtime/pids" in source
    assert "pkill" not in source
    assert "killall" not in source


def test_local_environment_files_are_documented_and_ignored() -> None:
    example = (ROOT / ".env.local.example").read_text(encoding="utf-8")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    for variable in (
        "DOCUMENT_LLM_BASE_URL",
        "DOCUMENT_LLM_MODEL",
        "DOCUMENT_LLM_API_KEY",
        "MULTIMODAL_API_URL",
        "MULTIMODAL_MODEL",
        "MULTIMODAL_API_KEY",
    ):
        assert f"{variable}=" in example

    assert ".env.local" in ignore
    assert ".runtime/" in ignore
    assert "document-parser/.venv/" in ignore
    assert "backend/data/documents/" in ignore
