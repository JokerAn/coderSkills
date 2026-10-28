#!/usr/bin/env python3
"""Prepare a disposable repository for modifier evaluation #9 (Python + Git)."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    source = Path(__file__).resolve().parent / "fixtures" / "shared-page-size"
    destination = Path(tempfile.mkdtemp(prefix="modifier-eval-"))
    shutil.copytree(source, destination, dirs_exist_ok=True)

    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(destination), "-c", "user.name=Skill Eval",
             "-c", "user.email=skill-eval@example.invalid", "-c", "commit.gpgsign=false",
             *args], text=True
        ).strip()

    git("init", "-q", "--template=", "-b", "main")
    git("add", ".")
    git("commit", "-qm", "evaluation baseline")
    (destination / "src" / "page-copy.js").write_text(
        "export const pageTitle = 'My results';\n", encoding="utf-8"
    )
    print(json.dumps({"workspace": str(destination), "head": git("rev-parse", "HEAD"),
                      "status": git("status", "--short")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
