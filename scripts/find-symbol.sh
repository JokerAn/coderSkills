#!/usr/bin/env bash
# 搜索区分大小写的文本；默认 literal，--regex 启用正则表达式。
# 退出码：0 找到，1 无结果，2 参数或检索失败。
set -euo pipefail

usage() {
  printf '用法: %s [--regex] [--] <文本或正则> [搜索目录]\n' "$0"
  printf '默认按字面文本、区分大小写搜索；以选项名称开头的文本可放在 -- 之后。\n'
}

mode='-F'
if [[ "${1:-}" == '-h' || "${1:-}" == '--help' ]]; then
  usage
  exit 0
fi
if [[ "${1:-}" == '--regex' ]]; then
  mode='-E'
  shift
fi
if [[ "${1:-}" == '--' ]]; then
  shift
fi
if (( $# < 1 || $# > 2 )) || [[ -z "$1" ]]; then
  usage >&2
  exit 2
fi
keyword="$1"
directory="${2-.}"
if [[ ! -d "$directory" ]]; then
  printf '错误：搜索目录不存在或不是目录：%s\n' "$directory" >&2
  exit 2
fi
# -- 无法阻止工具把单独的 - 当 stdin；相对路径统一加 ./。
if [[ "$directory" != /* ]]; then
  directory="./$directory"
fi
# 同时适用于 rg 与 grep；rg 还会遵循仓库的 ignore 规则。
excluded_dirs=(.git node_modules vendor .venv venv __pycache__ .cache .next .nuxt dist build coverage target)
status=0
if command -v rg >/dev/null 2>&1; then
  options=(--no-config -n --no-heading --color never)
  if [[ "$mode" == '-F' ]]; then
    options+=(-F)
  fi
  for excluded in "${excluded_dirs[@]}"; do
    options+=(--glob "!**/$excluded/**")
  done
  rg "${options[@]}" -- "$keyword" "$directory" || status=$?
else
  if ! command -v grep >/dev/null 2>&1; then
    printf '错误：需要 rg 或 grep 才能搜索。\n' >&2
    exit 2
  fi
  options=(-rnI "$mode")
  for excluded in "${excluded_dirs[@]}"; do
    options+=(--exclude-dir="$excluded")
  done
  grep "${options[@]}" -- "$keyword" "$directory" || status=$?
fi
if (( status > 1 )); then
  printf '错误：检索失败（搜索工具退出码 %s），请检查以上诊断。\n' "$status" >&2
  exit 2
fi
exit "$status"
