# Third-Party Licenses

## Included or Referenced Components

### NDLOCR-Lite (`ndlocr-lite`)

- Source: https://github.com/ndl-lab/ndlocr-lite
- License: CC BY 4.0
- License URL: https://creativecommons.org/licenses/by/4.0/
- Distribution model: the published adapter image does not bundle `ndlocr-lite`; the runtime bootstrap downloads it directly from the upstream repository configured by `NDL_OCR_LITE_REPO`
- Attribution note: preserve upstream attribution and license information when redistributing a deployment that includes a fetched `ndlocr-lite` checkout or a derivative thereof

### Immich

- Source: https://github.com/immich-app/immich
- Usage: Local source reference for API compatibility during development
- License: See the upstream Immich repository

### Python dependencies used by this adapter

- `fastapi`
- `orjson`
- `pillow`
- `pydantic-settings`
- `python-multipart`
- `uvicorn`

Dependency licenses should be reviewed before external distribution. The upstream NDLOCR-Lite repository may also ship its own dependency license information, and operators should keep that information available when redistributing a deployment that includes fetched upstream material.
