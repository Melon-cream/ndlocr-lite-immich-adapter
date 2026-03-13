# NOTICE

This project includes an adapter integration for `NDLOCR-Lite` (`ndlocr-lite`).

- Original work: `NDLOCR-Lite`
- Source: https://github.com/ndl-lab/ndlocr-lite
- Original authorship: National Diet Library related upstream project as credited in the upstream repository
- Upstream license: CC BY 4.0
- Upstream license URL: https://creativecommons.org/licenses/by/4.0/
- Distribution model in this repository: the published adapter image bootstraps `ndlocr-lite` from the upstream repository at runtime instead of bundling its source tree in the image layers

Modifications in this repository:

- Added an HTTP adapter compatible with the Immich machine-learning OCR API
- Converted upstream OCR output into Immich OCR response fields
- Added runtime bootstrap logic, containerization, operational configuration, CI workflows, and documentation

This repository is an adapter and is not the upstream OCR project itself.
