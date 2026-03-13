from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: extract_changelog.py <tag>")

    tag = sys.argv[1].removeprefix("v")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(rf"^## \[{re.escape(tag)}\].*?(?=^## \[|\Z)", changelog, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit(f"version {tag} was not found in CHANGELOG.md")

    Path(".github/release-notes.md").write_text(match.group(0).strip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
