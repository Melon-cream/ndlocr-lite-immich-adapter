from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ndlocr_lite_adapter.bootstrap import ensure_ndl_ocr_lite_runtime
from ndlocr_lite_adapter.config import Settings


def test_bootstrap_clones_and_installs_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_dir = tmp_path / "ndlocr-lite"
    venv_dir = tmp_path / "ndlocr-lite-venv"
    calls: list[list[str]] = []
    bootstrap_python = "/usr/bin/python3"

    def fake_run(command: list[str], description: str, *, timeout: int) -> None:
        calls.append(command)
        if command[:2] == ["git", "clone"]:
            checkout_dir = Path(command[-1])
            script_path = checkout_dir / "src" / "ocr.py"
            script_path.parent.mkdir(parents=True)
            script_path.write_text("print('ok')", encoding="utf-8")
            (checkout_dir / "requirements.txt").write_text("pillow\n", encoding="utf-8")
            return
        if command[-3:] == ["-m", "venv", str(venv_dir)]:
            python_path = venv_dir / "bin" / "python"
            python_path.parent.mkdir(parents=True)
            python_path.write_text("", encoding="utf-8")

    monkeypatch.setattr("ndlocr_lite_adapter.bootstrap._run", fake_run)
    settings = Settings(
        NDL_OCR_LITE_DIR=str(source_dir),
        NDL_OCR_LITE_VENV_DIR=str(venv_dir),
        NDL_OCR_LITE_BOOTSTRAP_PYTHON=bootstrap_python,
        NDL_OCR_LITE_BOOTSTRAP_TIMEOUT=123,
    )

    ensure_ndl_ocr_lite_runtime(settings)

    assert calls[0][:6] == ["git", "clone", "--depth", "1", "--branch", "master"]
    assert calls[0][-2] == "https://github.com/ndl-lab/ndlocr-lite.git"
    assert calls[1] == [bootstrap_python, "-m", "venv", str(venv_dir)]
    assert calls[2] == [str(venv_dir / "bin" / "python"), "-m", "pip", "install", "--no-cache-dir", "--upgrade", "pip"]
    assert calls[3] == [
        str(venv_dir / "bin" / "python"),
        "-m",
        "pip",
        "install",
        "--no-cache-dir",
        "-r",
        str(source_dir / "requirements.txt"),
    ]
    assert source_dir.exists()
    assert (source_dir / "src" / "ocr.py").exists()
    assert (venv_dir / ".bootstrap-state").read_text(encoding="utf-8") == _bootstrap_state_text(
        "https://github.com/ndl-lab/ndlocr-lite.git",
        "master",
        source_dir / "requirements.txt",
    )


def test_bootstrap_fails_when_disabled_and_checkout_missing(tmp_path: Path) -> None:
    source_dir = tmp_path / "ndlocr-lite"
    venv_dir = tmp_path / "venv"
    settings = Settings(
        NDL_OCR_LITE_DIR=str(source_dir),
        NDL_OCR_LITE_VENV_DIR=str(venv_dir),
        BOOTSTRAP_NDL_OCR_LITE=False,
    )

    with pytest.raises(RuntimeError, match="bootstrap is disabled"):
        ensure_ndl_ocr_lite_runtime(settings)


def test_bootstrap_skips_install_when_state_matches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_dir = tmp_path / "ndlocr-lite"
    script_path = source_dir / "src" / "ocr.py"
    script_path.parent.mkdir(parents=True)
    script_path.write_text("print('ok')", encoding="utf-8")
    requirements_path = source_dir / "requirements.txt"
    requirements_path.write_text("pillow\n", encoding="utf-8")

    venv_dir = tmp_path / "venv"
    python_path = venv_dir / "bin" / "python"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("", encoding="utf-8")
    (venv_dir / ".bootstrap-state").write_text(
        _bootstrap_state_text("https://github.com/ndl-lab/ndlocr-lite.git", "master", requirements_path),
        encoding="utf-8",
    )

    calls: list[list[str]] = []

    def fake_run(command: list[str], description: str, *, timeout: int) -> None:
        calls.append(command)

    monkeypatch.setattr("ndlocr_lite_adapter.bootstrap._run", fake_run)
    settings = Settings(
        NDL_OCR_LITE_DIR=str(source_dir),
        NDL_OCR_LITE_VENV_DIR=str(venv_dir),
        NDL_OCR_LITE_REPO="https://github.com/ndl-lab/ndlocr-lite.git",
        NDL_OCR_LITE_REF="master",
    )

    ensure_ndl_ocr_lite_runtime(settings)

    assert calls == []


def test_bootstrap_accepts_python_from_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_dir = tmp_path / "ndlocr-lite"
    script_path = source_dir / "src" / "ocr.py"
    script_path.parent.mkdir(parents=True)
    script_path.write_text("print('ok')", encoding="utf-8")
    requirements_path = source_dir / "requirements.txt"
    requirements_path.write_text("pillow\n", encoding="utf-8")
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()

    calls: list[list[str]] = []

    def fake_run(command: list[str], description: str, *, timeout: int) -> None:
        calls.append(command)

    monkeypatch.setattr("ndlocr_lite_adapter.bootstrap._run", fake_run)
    monkeypatch.setattr("ndlocr_lite_adapter.bootstrap.shutil.which", lambda command: "/usr/bin/python3")
    settings = Settings(
        NDL_OCR_LITE_DIR=str(source_dir),
        NDL_OCR_LITE_VENV_DIR=str(venv_dir),
        NDL_OCR_LITE_PYTHON="python3",
    )

    ensure_ndl_ocr_lite_runtime(settings)

    assert calls == [["python3", "-m", "pip", "install", "--no-cache-dir", "-r", str(requirements_path)]]


def test_bootstrap_clones_without_tempdir_under_source_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "restricted" / "ndlocr-lite"
    venv_dir = tmp_path / "venv"
    bootstrap_python = "/usr/bin/python3"
    temporary_dirs: list[str | None] = []

    class FakeTemporaryDirectory:
        def __init__(self, *, prefix: str, dir: str | None = None) -> None:
            temporary_dirs.append(dir)
            self.path = tmp_path / "tmp-bootstrap"
            self.path.mkdir(exist_ok=True)

        def __enter__(self) -> str:
            return str(self.path)

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    def fake_run(command: list[str], description: str, *, timeout: int) -> None:
        if command[:2] == ["git", "clone"]:
            checkout_dir = Path(command[-1])
            script_path = checkout_dir / "src" / "ocr.py"
            script_path.parent.mkdir(parents=True)
            script_path.write_text("print('ok')", encoding="utf-8")
            (checkout_dir / "requirements.txt").write_text("pillow\n", encoding="utf-8")
            return
        if command[-3:] == ["-m", "venv", str(venv_dir)]:
            python_path = venv_dir / "bin" / "python"
            python_path.parent.mkdir(parents=True)
            python_path.write_text("", encoding="utf-8")

    monkeypatch.setattr("ndlocr_lite_adapter.bootstrap.tempfile.TemporaryDirectory", FakeTemporaryDirectory)
    monkeypatch.setattr("ndlocr_lite_adapter.bootstrap._run", fake_run)
    settings = Settings(
        NDL_OCR_LITE_DIR=str(source_dir),
        NDL_OCR_LITE_VENV_DIR=str(venv_dir),
        NDL_OCR_LITE_BOOTSTRAP_PYTHON=bootstrap_python,
    )

    ensure_ndl_ocr_lite_runtime(settings)

    assert temporary_dirs == [None]
    assert source_dir.exists()


def _bootstrap_state_text(repo: str, ref: str, requirements_path: Path) -> str:
    requirements_hash = hashlib.sha256(requirements_path.read_bytes()).hexdigest()
    return f"{repo}@{ref}:{requirements_hash}"
