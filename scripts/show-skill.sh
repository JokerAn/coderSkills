#!/usr/bin/env bash
# 仓库通用：把某个 skill 目录下的 SKILL.md 打印出来
# 用法: ./scripts/show-skill.sh <skill-name>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:-}"
if [ -z "$NAME" ]; then
  echo "可用 skill:"; ls -1 "$ROOT" | grep -v '^scripts$' | grep -v '^\.'
  exit 0
fi
FILE="$ROOT/$NAME/SKILL.md"
[ -f "$FILE" ] || { echo "未找到: $FILE"; exit 1; }
cat "$FILE"
