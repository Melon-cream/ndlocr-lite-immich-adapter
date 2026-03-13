from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=3003, alias="PORT")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO", alias="LOG_LEVEL")
    device: str = Field(default="cpu", alias="DEVICE")
    model_dir: str = Field(default="/opt/ndlocr-lite/src/model", alias="MODEL_DIR")
    max_image_pixels: int = Field(default=40_000_000, alias="MAX_IMAGE_PIXELS")
    request_timeout: int = Field(default=120, alias="REQUEST_TIMEOUT")
    ndl_ocr_lite_dir: str = Field(default="/opt/ndlocr-lite", alias="NDL_OCR_LITE_DIR")
    ndl_ocr_lite_venv_dir: str = Field(default="/opt/ndlocr-lite-venv", alias="NDL_OCR_LITE_VENV_DIR")
    ndl_ocr_lite_repo: str = Field(default="https://github.com/ndl-lab/ndlocr-lite.git", alias="NDL_OCR_LITE_REPO")
    ndl_ocr_lite_ref: str = Field(default="master", alias="NDL_OCR_LITE_REF")
    bootstrap_ndl_ocr_lite: bool = Field(
        default=True,
        alias="BOOTSTRAP_NDL_OCR_LITE",
        validation_alias=AliasChoices("BOOTSTRAP_NDL_OCR_LITE", "NDL_OCR_LITE_AUTO_SETUP"),
    )
    ndl_ocr_python: str | None = Field(
        default_factory=lambda: os.getenv("NDL_OCR_LITE_PYTHON"),
        alias="NDL_OCR_LITE_PYTHON",
    )
    ndl_ocr_lite_bootstrap_python: str = Field(
        default_factory=lambda: os.getenv("PYTHON", "python3"),
        alias="NDL_OCR_LITE_BOOTSTRAP_PYTHON",
    )
    ndl_ocr_lite_bootstrap_timeout: int = Field(default=600, alias="NDL_OCR_LITE_BOOTSTRAP_TIMEOUT")
    detector_weights: str | None = Field(default=None, alias="DETECTOR_WEIGHTS")
    detector_classes: str | None = Field(default=None, alias="DETECTOR_CLASSES")
    recognizer_weights: str | None = Field(default=None, alias="RECOGNIZER_WEIGHTS")
    recognizer_classes: str | None = Field(default=None, alias="RECOGNIZER_CLASSES")

    @model_validator(mode="after")
    def apply_runtime_defaults(self) -> Settings:
        if self.ndl_ocr_python is None:
            self.ndl_ocr_python = str(Path(self.ndl_ocr_lite_venv_dir) / "bin" / "python")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
