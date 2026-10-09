#!/usr/bin/env bash
# 打印指定文件的带行号内容；end=0 表示读到末尾。
set -euo pipefail

usage() {
  printf '用法: %s [--] <文件> [起始行=1] [结束行=0]\n' "$0"
  printf '行号需为不带前导零的正整数；结束行 0 表示末尾，显式范围不得超过文件行数。\n'
}
fail() {
  printf '错误：%s\n' "$1" >&2
  exit 2
}
# 比较规范十进制字符串，避免超大输入触发 shell 整数溢出。
decimal_gt() {
  [[ ${#1} -gt ${#2} || ( ${#1} -eq ${#2} && "$1" > "$2" ) ]]
}
if [[ "${1:-}" == '-h' || "${1:-}" == '--help' ]]; then
  usage
  exit 0
fi
if [[ "${1:-}" == '--' ]]; then
  shift
fi
if (( $# < 1 || $# > 3 )); then
  usage >&2
  exit 2
fi
file="$1"
start="${2-1}"
end="${3-0}"
[[ "$start" =~ ^[1-9][0-9]*$ ]] || fail '起始行必须是正整数（不带前导零）。'
[[ "$end" =~ ^(0|[1-9][0-9]*)$ ]] || fail '结束行必须是正整数或 0（不带前导零）。'
[[ -n "$file" && -f "$file" && -r "$file" ]] || fail "文件不存在、不是普通文件或不可读：$file"
# awk 会把 - 开头路径当选项、a=b 当赋值；给所有相对路径添加 ./。
if [[ "$file" != /* ]]; then
  file="./$file"
fi
if [[ "$end" != 0 ]] && decimal_gt "$start" "$end"; then
  fail '结束行不能小于起始行。'
fi
if ! total="$(awk 'END { printf "%.0f\n", NR }' "$file")"; then
  fail "无法读取文件：$file"
fi
decimal_gt "$start" "$total" && fail "起始行 ${start} 超过文件行数 ${total}。"
if [[ "$end" != 0 ]] && decimal_gt "$end" "$total"; then
  fail "结束行 ${end} 超过文件行数 ${total}。"
fi
if ! awk -v s="$start" -v e="$end" 'NR >= s && (e == 0 || NR <= e) { printf "%d\t%s\n", NR, $0 }' "$file"; then
  fail "无法读取文件：$file"
fi
