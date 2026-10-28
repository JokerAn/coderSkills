#!/usr/bin/env python3
"""把本仓库的 skill 安装到 DeepSeek Harness 的用户 skill 根目录。

为什么需要改写名字
------------------
DeepSeek Harness 的 `@deepseek-ai/dsh-skill-filesystem` 提供方按下面的优先级
扫描 skill 根目录：

| rank | 来源          | 路径                          |
| ---- | ------------- | ----------------------------- |
| 100  | project-dsh   | `<projectRoot>/.dsh/skills`   |
| 200  | project-agents| `<projectRoot>/.agents/skills`|
| 300  | custom        | `Config.customSkillDirs`      |
| 400  | user-dsh      | `<dshHome>/skills`            |
| 500  | user-agents   | `<agentsHome>/skills`         |

其中 `<projectRoot>` 是最近包含 `.git` 的祖先目录，`<dshHome>` 默认 `~/.dsh`，
`<agentsHome>` 默认 `~/.agents`。每个根目录下一层的 `<name>/SKILL.md` 会被解析。

**frontmatter 中的 `name` 必须匹配 `/^[a-z0-9]+(?:-[a-z0-9]+)*$/`（kebab-case）**，
否则该 skill 会连同警告被静默丢弃，不会出现在会话目录里。本仓库为 Codex 使用
中文名（`修改web代码` 等），因此安装时需要生成一份 `name` 改写为 kebab-case 的
`SKILL.md`；正文与其余文件保持原样。

除 `SKILL.md` 外的内容默认以符号链接指回仓库，便于边改边生效；使用 `--copy`
可以生成完全自包含的副本。两种模式都会在目标目录写入 `.dsh-install.json`
标记，记录来源与模式，供重复安装与 `--uninstall` 判断归属。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

# 仓库中文目录名 -> DeepSeek Harness kebab-case skill 名
SKILLS: list[tuple[str, str]] = [
    ("web-code-modifier", "web-code-modifier"),
    ("web-code-reviewer", "web-code-reviewer"),
    ("web-code-tracer", "web-code-tracer"),
    ("mermaid-diagram", "mermaid-diagram"),
]

# 与 @deepseek-ai/dsh-skill 的 SKILL_NAME 保持一致
SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

MARKER = ".dsh-install.json"
LINKED_DIRS = ("agents", "references", "evals")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


class InstallError(Exception):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def rewrite_name(text: str, name: str, source: Path) -> str:
    """把 frontmatter 的 name 改写为 name，保留其余行原样。"""
    match = FRONTMATTER.match(text)
    if not match:
        raise InstallError("{}: SKILL.md 缺少 YAML frontmatter".format(source))
    lines = match.group(1).split("\n")
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith("name:"):
            lines[index] = "name: " + name
            replaced = True
            break
    if not replaced:
        lines.insert(0, "name: " + name)
    body = text[match.end():]
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def read_skill(source: Path, name: str) -> str:
    path = source / "SKILL.md"
    if not path.is_file():
        raise InstallError("{}: 缺少 SKILL.md".format(source))
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
    if not match:
        raise InstallError("{}: SKILL.md 缺少 YAML frontmatter".format(path))
    for required in ("name:", "description:"):
        if not any(line.startswith(required) for line in match.group(1).split("\n")):
            raise InstallError("{}: frontmatter 缺少 {}".format(path, required.rstrip(":")))
    return rewrite_name(text, name, path)


def remove_if_present(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def install_one(source: Path, name: str, dest_root: Path, copy: bool, force: bool) -> str:
    if not SKILL_NAME.match(name):
        raise InstallError("非法的 kebab-case skill 名：{}".format(name))
    content = read_skill(source, name)
    dest = dest_root / name
    marker = dest / MARKER

    if dest.exists() or dest.is_symlink():
        ours = marker.is_file()
        if not ours and not force:
            raise InstallError(
                "{} 已存在且不是本脚本安装的；确认后加 --force 覆盖".format(dest)
            )
        remove_if_present(dest)

    dest.mkdir(parents=True, exist_ok=True)
    (dest / "SKILL.md").write_text(content, encoding="utf-8")

    linked: list[str] = []
    for sub in LINKED_DIRS:
        origin = source / sub
        if not origin.is_dir():
            continue
        target = dest / sub
        if copy:
            shutil.copytree(origin, target)
        else:
            target.symlink_to(origin, target_is_directory=True)
        linked.append(sub)

    marker.write_text(
        json.dumps(
            {
                "tool": "coderSkills/scripts/install-dsh-skills.py",
                "source": str(source),
                "sourceSkill": source.name,
                "dshSkill": name,
                "mode": "copy" if copy else "link",
                "linked": linked,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return "{} -> {}（{}）".format(source.name, dest, "复制" if copy else "链接")


def uninstall_one(dest_root: Path, name: str) -> str | None:
    dest = dest_root / name
    if not dest.is_dir():
        return None
    if not (dest / MARKER).is_file():
        return "跳过 {}：不是本脚本安装的".format(dest)
    remove_if_present(dest)
    return "已移除 {}".format(dest)


def parse_args(argv: list[str]) -> argparse.Namespace:
    default_dsh_home = Path(os.environ.get("DSH_HOME") or Path.home() / ".dsh")
    parser = argparse.ArgumentParser(
        description="把本仓库的 skill 安装到 DeepSeek Harness 的 skill 根目录",
    )
    parser.add_argument(
        "--dest",
        default=os.environ.get("DSH_SKILLS_DIR") or str(default_dsh_home / "skills"),
        help="目标 skill 根目录（默认 $DSH_SKILLS_DIR 或 $DSH_HOME/skills，即 ~/.dsh/skills）",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="复制全部内容而非符号链接 references/agents/evals",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="覆盖同名但非本脚本安装的目录",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="移除本脚本安装的 skill",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要执行的操作",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出仓库中的 skill 与对应的 DSH 名称",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = repo_root()
    dest_root = Path(args.dest).expanduser()

    if args.list:
        for source_name, name in SKILLS:
            exists = "有" if (root / source_name / "SKILL.md").is_file() else "缺失"
            print("{:<12} -> {:<20} [{}]".format(source_name, name, exists))
        return 0

    print("仓库：{}".format(root))
    print("目标：{}".format(dest_root))
    print("模式：{}".format("复制" if args.copy else "链接"))

    failed = False
    if not args.dry_run and not args.uninstall:
        dest_root.mkdir(parents=True, exist_ok=True)

    for source_name, name in SKILLS:
        source = root / source_name
        try:
            if args.uninstall:
                message = uninstall_one(dest_root, name)
            elif args.dry_run:
                message = "{} -> {}（{}）".format(
                    source.name, dest_root / name, "复制" if args.copy else "链接"
                )
            else:
                message = install_one(source, name, dest_root, args.copy, args.force)
        except (InstallError, OSError) as error:
            print("失败：{}".format(error), file=sys.stderr)
            failed = True
            continue
        if message:
            print("  {}".format(message))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
