from __future__ import annotations

import uvicorn

from .app import app
from .bootstrap import ensure_ndl_ocr_lite_runtime
from .config import get_settings


def main() -> None:
    settings = get_settings()
    ensure_ndl_ocr_lite_runtime(settings)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())


if __name__ == "__main__":
    main()
