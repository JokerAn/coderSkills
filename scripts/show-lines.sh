#!/usr/bin/env bash
# 评审/改动辅助：打印指定文件的带行号内容（评审引用证据用）
# 用法: ./scripts/show-lines.sh <文件> [起始行] [结束行]
set -euo pipefail
F="${1:-}"; S="${2:-1}"; E="${3:-0}"
if [ -z "$F" ] || [ ! -f "$F" ]; then echo "用法: $0 <文件> [起] [止]"; exit 1; fi
if [ "$E" -gt 0 ] 2>/dev/null; then
  awk -v s="$S" -v e="$E" 'NR>=s && NR<=e {printf "%d\t%s\n", NR, $0}' "$F"
else
  awk -v s="$S" 'NR>=s {printf "%d\t%s\n", NR, $0}' "$F"
fi
