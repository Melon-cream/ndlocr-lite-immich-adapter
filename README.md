# ndlocr-lite-adapter

`ndlocr-lite-adapter` is an OCR-only adapter service for Immich that exposes an `Immich machine-learning` compatible API and delegates OCR inference to `NDLOCR-Lite` (`ndlocr-lite`).

The published container image does not bundle `ndlocr-lite`. It bootstraps the upstream project from its official repository on first start and reuses it from mounted volumes.

## What It Does

- Exposes `GET /ping` and `POST /predict`
- Accepts Immich OCR requests via `multipart/form-data`
- Converts NDLOCR-Lite JSON output into Immich OCR fields: `text`, `box`, `boxScore`, `textScore`
- Keeps the response shape compatible with Immich OCR storage, overlay rendering, and search indexing

## Scope

- Supported task: `ocr`
- Unsupported tasks: `clip`, `facial-recognition`, and any non-OCR request return `501`
- Initial target: CPU runtime

## Repository Layout

- `src/ndlocr_lite_adapter`: FastAPI application and NDLOCR-Lite runner
- `tests`: API and response transformation tests
- `Dockerfile`: container image for the adapter bootstrap runtime
- `docker-compose.example.yml`: example standalone service definition

## Quick Start

### 1. Pull the published image

```bash
docker pull ghcr.io/melon-cream/ndlocr-lite-immich-adapter:latest
```

### 2. Run the adapter

```bash
docker run --rm -p 3003:3003 ghcr.io/melon-cream/ndlocr-lite-immich-adapter:latest
```

On the first start, the container downloads `ndlocr-lite` directly from the upstream repository, creates a dedicated virtual environment under `/opt/ndlocr-lite-venv`, and installs the upstream runtime dependencies there.

### 3. Point Immich to the adapter

Set the Immich machine-learning URL to:

```text
http://ndlocr-lite-immich-adapter:3003
```

If you use a standalone container, replace the hostname with the container or host address reachable from Immich.

## Compose Example

Use [`docker-compose.example.yml`](https://github.com/Melon-cream/ndlocr-lite-immich-adapter/blob/main/docker-compose.example.yml) as a starting point. The service exposes port `3003`, which matches Immich's default machine-learning port, and mounts named volumes so the upstream checkout and virtual environment survive container recreation.

## Environment Variables

- `HOST`: bind address, default `0.0.0.0`
- `PORT`: listening port, default `3003`
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, or `ERROR`
- `DEVICE`: NDLOCR-Lite device argument, default `cpu`
- `MODEL_DIR`: model directory path inside the container, default `/opt/ndlocr-lite/src/model`
- `MAX_IMAGE_PIXELS`: maximum allowed pixel count before downscaling
- `REQUEST_TIMEOUT`: NDLOCR-Lite subprocess timeout in seconds
- `NDL_OCR_LITE_DIR`: upstream NDLOCR-Lite checkout path
- `NDL_OCR_LITE_VENV_DIR`: virtual environment directory prepared for the upstream runtime
- `NDL_OCR_LITE_REPO`: upstream Git repository used for bootstrap
- `NDL_OCR_LITE_REF`: branch or tag fetched from the upstream repository
- `BOOTSTRAP_NDL_OCR_LITE`: set to `false` to require a preinstalled upstream checkout
- `NDL_OCR_LITE_BOOTSTRAP_TIMEOUT`: timeout in seconds for bootstrap clone and dependency installation
- `NDL_OCR_LITE_PYTHON`: Python executable used for the upstream CLI

## API Compatibility Notes

- `entries` must contain only the `ocr` task.
- The adapter reads:
  - `ocr.detection.modelName`
  - `ocr.detection.options.minScore`
  - `ocr.detection.options.maxResolution`
  - `ocr.recognition.modelName`
  - `ocr.recognition.options.minScore`
- `box` coordinates are returned in normalized `0.0-1.0` space using Immich's expected point order.
- `textScore` falls back to the upstream confidence value because NDLOCR-Lite does not expose a separate recognition score in its JSON output.

## Verification

Basic syntax verification can be run locally with:

```bash
python3 -m compileall src tests
```

Full lint and test automation is provided in GitHub Actions.

## License and Attribution

This repository is an adapter around `NDLOCR-Lite` and is not the upstream project itself.

- Adapter code license: MIT
- Upstream project: `ndlocr-lite`
- Upstream bootstrap source: official upstream repository configured by `NDL_OCR_LITE_REPO`
- Attribution and modification notes: see [`NOTICE.md`](https://github.com/Melon-cream/ndlocr-lite-immich-adapter/blob/main/NOTICE.md)
- Third-party license summary: see [`THIRD_PARTY_LICENSES.md`](https://github.com/Melon-cream/ndlocr-lite-immich-adapter/blob/main/THIRD_PARTY_LICENSES.md)

The published adapter image does not contain the upstream repository contents. Operators should review the upstream license before enabling bootstrap in their environment.
