#!/usr/bin/env python3
"""Prepare a disposable repository for review evaluation #13 (Python + Git)."""

import json
from pathlib import Path
import subprocess
import tempfile


def main():
    destination = Path(tempfile.mkdtemp(prefix="review-head-eval-"))

    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(destination), "-c", "user.name=Skill Eval",
             "-c", "user.email=skill-eval@example.invalid", "-c", "commit.gpgsign=false",
             *args], text=True
        ).strip()

    git("init", "-q", "--template=", "-b", "main")
    (destination / "src").mkdir()
    (destination / "README.md").write_text(
        "# Display limit\n\nThe input is a non-negative integer, null, or undefined. "
        "Zero displays zero rows; only null and undefined default to 10. "
        "The result only controls how many rows a help list displays.\n", encoding="utf-8"
    )
    (destination / "package.json").write_text(
        '{"name":"review-head-fixture","private":true,"type":"module"}\n', encoding="utf-8"
    )
    limit = destination / "src" / "limit.js"
    limit.write_text("export const limit = value => value ?? 10;\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "baseline")
    git("checkout", "-qb", "feature")
    limit.write_text("export const limit = value => value || 10;\n", encoding="utf-8")
    git("add", "src/limit.js")
    git("commit", "-qm", "change display default")
    review_head = git("rev-parse", "feature")
    git("checkout", "-q", "main")
    (destination / "README.md").write_text(
        (destination / "README.md").read_text(encoding="utf-8")
        + "\nLocal note: preserve this uncommitted text.\n", encoding="utf-8"
    )
    print(json.dumps({"workspace": str(destination), "base": git("rev-parse", "main"),
                      "reviewHead": review_head, "head": git("rev-parse", "HEAD"),
                      "status": git("status", "--short")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
