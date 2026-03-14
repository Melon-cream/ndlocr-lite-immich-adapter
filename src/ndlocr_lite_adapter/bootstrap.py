from __future__ import annotations

import hashlib
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import Settings

logger = logging.getLogger(__name__)


def ensure_ndl_ocr_lite_runtime(settings: Settings) -> None:
    source_dir = Path(settings.ndl_ocr_lite_dir)
    venv_dir = Path(settings.ndl_ocr_lite_venv_dir)
    script_path = source_dir / "src" / "ocr.py"
    requirements_path = source_dir / "requirements.txt"
    python_command = settings.ndl_ocr_python
    default_python_path = str(venv_dir / "bin" / "python")
    state_path = venv_dir / ".bootstrap-state"

    if not script_path.exists():
        if not settings.bootstrap_ndl_ocr_lite:
            raise RuntimeError(
                "NDLOCR-Lite is not installed and bootstrap is disabled. "
                f"Populate {source_dir} manually or enable BOOTSTRAP_NDL_OCR_LITE."
            )
        _clone_upstream(settings, source_dir)

    if not requirements_path.exists():
        raise RuntimeError(f"NDLOCR-Lite requirements file not found: {requirements_path}")

    if not _command_exists(python_command):
        if python_command != default_python_path:
            raise RuntimeError(f"Configured NDLOCR-Lite Python executable not found: {python_command}")
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        _run(
            [settings.ndl_ocr_lite_bootstrap_python, "-m", "venv", str(venv_dir)],
            "create the NDLOCR-Lite virtual environment",
            timeout=settings.ndl_ocr_lite_bootstrap_timeout,
        )
        _run(
            [python_command, "-m", "pip", "install", "--no-cache-dir", "--upgrade", "pip"],
            "upgrade pip in the NDLOCR-Lite virtual environment",
            timeout=settings.ndl_ocr_lite_bootstrap_timeout,
        )

    bootstrap_state = _bootstrap_state(settings, requirements_path)
    if state_path.exists() and state_path.read_text(encoding="utf-8") == bootstrap_state:
        return

    _run(
        [python_command, "-m", "pip", "install", "--no-cache-dir", "-r", str(requirements_path)],
        "install NDLOCR-Lite Python dependencies",
        timeout=settings.ndl_ocr_lite_bootstrap_timeout,
    )
    state_path.write_text(bootstrap_state, encoding="utf-8")


def _clone_upstream(settings: Settings, source_dir: Path) -> None:
    source_dir.parent.mkdir(parents=True, exist_ok=True)
    if source_dir.exists() and any(source_dir.iterdir()):
        raise RuntimeError(
            "NDLOCR-Lite source directory exists but does not contain a valid checkout: "
            f"{source_dir}. Remove its contents or point NDL_OCR_LITE_DIR to a clean directory."
        )

    logger.info(
        "Bootstrapping NDLOCR-Lite from upstream",
        extra={"repo": settings.ndl_ocr_lite_repo, "ref": settings.ndl_ocr_lite_ref},
    )
    with tempfile.TemporaryDirectory(prefix="ndlocr-lite-bootstrap-") as tmp_dir:
        checkout_dir = Path(tmp_dir) / "repo"
        _run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                settings.ndl_ocr_lite_ref,
                settings.ndl_ocr_lite_repo,
                str(checkout_dir),
            ],
            "clone NDLOCR-Lite from the upstream repository",
            timeout=settings.ndl_ocr_lite_bootstrap_timeout,
        )
        if source_dir.exists():
            shutil.copytree(checkout_dir, source_dir, dirs_exist_ok=True)
            return
        shutil.move(str(checkout_dir), str(source_dir))


def _bootstrap_state(settings: Settings, requirements_path: Path) -> str:
    requirements_hash = hashlib.sha256(requirements_path.read_bytes()).hexdigest()
    return f"{settings.ndl_ocr_lite_repo}@{settings.ndl_ocr_lite_ref}:{requirements_hash}"


def _command_exists(command: str) -> bool:
    if "/" in command:
        return Path(command).exists()
    return shutil.which(command) is not None


def _run(command: list[str], description: str, *, timeout: int) -> None:
    logger.info("Running bootstrap command", extra={"description": description, "command": command})
    try:
        completed = subprocess.run(command, capture_output=True, check=False, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"Timed out while trying to {description} after {timeout}s") from error
    if completed.returncode != 0:
        raise RuntimeError(
            f"Failed to {description}: exit={completed.returncode} "
            f"stderr={completed.stderr.strip()} stdout={completed.stdout.strip()}"
        )
