from __future__ import annotations

import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_configure_launcher_is_a_safe_interactive_env_writer() -> None:
    script = ROOT / "configure.sh"
    source = script.read_text(encoding="utf-8")

    assert script.stat().st_mode & stat.S_IXUSR
    assert "read -r -s" in source
    assert "chmod 600" in source
    assert ".env.local" in source
    assert ".env.local.example" not in source
    assert "DOCUMENT_LLM_API_KEY" in source
    assert "MULTIMODAL_API_KEY" in source
    assert "set -a" not in source
    assert "echo \"$" not in source
