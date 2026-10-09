#!/usr/bin/env bash
# 溯源辅助：在一批源码里搜符号/文本的所有出现位置（带行号）
# 用法: ./scripts/find-symbol.sh <关键词> [搜索目录]
# 依赖：rg (ripgrep) 优先，回退 grep -rn
set -euo pipefail
KW="${1:-}"
DIR="${2:-.}"
if [ -z "$KW" ]; then echo "用法: $0 <关键词> [目录]"; exit 1; fi
if command -v rg >/dev/null 2>&1; then
  rg -n --no-heading -S "$KW" "$DIR" || true
else
  grep -rn --exclude-dir=node_modules --exclude-dir=.git "$KW" "$DIR" || true
fi
