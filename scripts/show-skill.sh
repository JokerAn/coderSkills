#!/usr/bin/env bash
# 无参数列出实际 skill；有参数打印对应的 SKILL.md。
set -euo pipefail

root="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
usage() {
  printf '用法: %s [skill-name]\n' "$0"
}
valid_name() {
  [[ "$1" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ && ${#1} -le 64 ]]
}
if [[ "${1:-}" == '-h' || "${1:-}" == '--help' ]]; then
  usage
  exit 0
fi
if (( $# == 0 )); then
  printf '可用 skill:\n'
  for directory in "$root"/*; do
    name="${directory##*/}"
    if valid_name "$name" && [[ -d "$directory" && ! -L "$directory" && -f "$directory/SKILL.md" && ! -L "$directory/SKILL.md" ]]; then
      printf '%s\n' "$name"
    fi
  done
  exit 0
fi
if (( $# != 1 )) || ! valid_name "$1"; then
  printf '错误：skill 名称需为不超过 64 字符的小写字母/数字，以单个连字符分隔。\n' >&2
  usage >&2
  exit 2
fi
directory="$root/$1"
file="$directory/SKILL.md"
# 不通过符号链接读取仓库之外的内容。
if [[ -L "$directory" || -L "$file" ]]; then
  printf '错误：skill 目录和 SKILL.md 不允许是符号链接：%s\n' "$1" >&2
  exit 2
fi
if [[ ! -f "$file" ]]; then
  printf '错误：未找到 skill：%s\n' "$1" >&2
  exit 1
fi
if ! cat -- "$file"; then
  printf '错误：无法读取：%s\n' "$file" >&2
  exit 2
fi
