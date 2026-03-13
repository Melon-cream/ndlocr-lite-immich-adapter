from pathlib import Path

import pytest

from ndlocr_lite_adapter.config import Settings
from ndlocr_lite_adapter.runner import NdlOcrLiteRunner


def test_runner_defaults_match_ndlocr_lite_layout() -> None:
    settings = Settings()

    runner = NdlOcrLiteRunner(settings)

    assert runner.source_dir == Path("/opt/ndlocr-lite")
    assert runner.model_dir == Path("/opt/ndlocr-lite/src/model")
    assert runner.script_path == Path("/opt/ndlocr-lite/src/ocr.py")
    assert settings.ndl_ocr_lite_venv_dir == "/opt/ndlocr-lite-venv"
    assert settings.ndl_ocr_python == "/opt/ndlocr-lite-venv/bin/python"
    assert settings.bootstrap_ndl_ocr_lite is True
    assert runner.detector_weights == "/opt/ndlocr-lite/src/model/deim-s-1024x1024.onnx"
    assert runner.recognizer_weights == "/opt/ndlocr-lite/src/model/parseq-ndl-16x768-100-tiny-165epoch-tegaki2.onnx"


def test_runner_accepts_python_from_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_dir = tmp_path / "ndlocr-lite"
    script_path = source_dir / "src" / "ocr.py"
    script_path.parent.mkdir(parents=True)
    script_path.write_text("print('ok')", encoding="utf-8")

    monkeypatch.setattr("ndlocr_lite_adapter.runner.shutil.which", lambda command: "/usr/bin/python3")
    runner = NdlOcrLiteRunner(Settings(NDL_OCR_LITE_DIR=str(source_dir), NDL_OCR_LITE_PYTHON="python3"))

    runner._validate_installation()
