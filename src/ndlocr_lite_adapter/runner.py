from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import Settings

logger = logging.getLogger(__name__)


class NdlOcrLiteRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.source_dir = Path(settings.ndl_ocr_lite_dir)
        self.model_dir = Path(settings.model_dir)
        self.script_path = self.source_dir / "src" / "ocr.py"
        self.detector_weights = settings.detector_weights or str(self.model_dir / "deim-s-1024x1024.onnx")
        self.detector_classes = settings.detector_classes or str(self.source_dir / "src" / "config" / "ndl.yaml")
        self.recognizer_weights = settings.recognizer_weights or str(
            self.model_dir / "parseq-ndl-16x768-100-tiny-165epoch-tegaki2.onnx"
        )
        self.recognizer_classes = settings.recognizer_classes or str(
            self.source_dir / "src" / "config" / "NDLmoji.yaml"
        )

    def run(self, image_bytes: bytes) -> dict:
        self._validate_installation()
        with tempfile.TemporaryDirectory(prefix="ndlocr-lite-adapter-") as tmp_dir:
            temp_dir = Path(tmp_dir)
            input_path = temp_dir / "input.png"
            output_dir = temp_dir / "out"
            output_dir.mkdir()
            input_path.write_bytes(image_bytes)

            command = [
                self.settings.ndl_ocr_python,
                str(self.script_path),
                "--sourceimg",
                str(input_path),
                "--output",
                str(output_dir),
                "--device",
                self.settings.device,
                "--det-weights",
                self.detector_weights,
                "--det-classes",
                self.detector_classes,
                "--rec-weights",
                self.recognizer_weights,
                "--rec-classes",
                self.recognizer_classes,
            ]

            logger.debug("Executing NDLOCR-Lite command", extra={"command": command})
            try:
                completed = subprocess.run(
                    command,
                    cwd=self.source_dir,
                    capture_output=True,
                    check=False,
                    text=True,
                    timeout=self.settings.request_timeout,
                )
            except subprocess.TimeoutExpired as error:
                raise TimeoutError(f"NDLOCR-Lite inference timed out after {self.settings.request_timeout}s") from error
            if completed.returncode != 0:
                raise RuntimeError(
                    "NDLOCR-Lite inference failed: "
                    f"exit={completed.returncode} stderr={completed.stderr.strip()} stdout={completed.stdout.strip()}"
                )

            output_path = output_dir / f"{input_path.stem}.json"
            if not output_path.exists():
                raise RuntimeError(f"NDLOCR-Lite output file was not created: {output_path}")

            return json.loads(output_path.read_text(encoding="utf-8"))

    def _validate_installation(self) -> None:
        if not self.script_path.exists():
            raise RuntimeError(f"NDLOCR-Lite script not found: {self.script_path}")
        if not _command_exists(self.settings.ndl_ocr_python):
            raise RuntimeError(f"NDLOCR-Lite Python executable not found: {self.settings.ndl_ocr_python}")


def _command_exists(command: str) -> bool:
    if "/" in command:
        return Path(command).exists()
    return shutil.which(command) is not None
