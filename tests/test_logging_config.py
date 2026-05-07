from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
from iamai.config import load_config, load_env_file
from iamai.logging import configure_logging
from iamai.observability import AuditLogger
from loguru import logger


def test_load_config_validates_logging_section(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
        [runtime]
        adapters = []
        builtin_plugins = false

        [logging]
        level = "debug"
        file = "logs/runtime.log"
        serialize = true
        stderr = false
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["logging"]["level"] == "DEBUG"
    assert config["logging"]["file"] == "logs/runtime.log"
    assert config["logging"]["serialize"] is True


def test_load_env_file_does_not_override_existing_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        """
        OPENAI_MODEL=kimi-k2.5
        QUOTED_VALUE="hello world"
        export EXPORTED_VALUE=ok
        """,
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_MODEL", "existing")

    load_env_file(env_path)

    assert os.environ["OPENAI_MODEL"] == "existing"
    assert os.environ["QUOTED_VALUE"] == "hello world"
    assert os.environ["EXPORTED_VALUE"] == "ok"


def test_configure_logging_writes_loguru_and_stdlib_records(tmp_path: Path) -> None:
    log_path = tmp_path / "runtime.log"
    configure_logging(
        {
            "logging": {
                "enabled": True,
                "level": "INFO",
                "format": "{level}:{name}:{message}",
                "stderr": False,
                "file": str(log_path),
                "rotation": None,
                "retention": None,
                "compression": None,
                "intercept_stdlib": True,
                "capture_warnings": False,
            }
        },
        base_path=tmp_path,
    )

    logger.bind(name="test.loguru").info("loguru record")
    logging.getLogger("test.stdlib").warning("stdlib record")
    AuditLogger().emit("demo.audit", user="alice")
    logger.complete()

    content = log_path.read_text(encoding="utf-8")
    assert "loguru record" in content
    assert "stdlib record" in content
    assert "demo.audit" in content
