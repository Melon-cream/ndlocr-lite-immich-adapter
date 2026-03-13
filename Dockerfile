FROM python:3.12-slim

ARG NDL_OCR_LITE_REPO=https://github.com/ndl-lab/ndlocr-lite.git
ARG NDL_OCR_LITE_REF=master

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=3003 \
    LOG_LEVEL=INFO \
    DEVICE=cpu \
    MODEL_DIR=/opt/ndlocr-lite/src/model \
    MAX_IMAGE_PIXELS=40000000 \
    REQUEST_TIMEOUT=120 \
    NDL_OCR_LITE_DIR=/opt/ndlocr-lite \
    NDL_OCR_LITE_VENV_DIR=/opt/ndlocr-lite-venv \
    NDL_OCR_LITE_REPO=${NDL_OCR_LITE_REPO} \
    NDL_OCR_LITE_REF=${NDL_OCR_LITE_REF} \
    BOOTSTRAP_NDL_OCR_LITE=true \
    NDL_OCR_LITE_PYTHON=/opt/ndlocr-lite-venv/bin/python

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md README-JP.md CHANGELOG.md CHANGELOG-JP.md NOTICE.md THIRD_PARTY_LICENSES.md LICENSE /app/
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /app

EXPOSE 3003

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python3 -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:3003/ping').read()"

CMD ["python3", "-m", "ndlocr_lite_adapter.main"]
