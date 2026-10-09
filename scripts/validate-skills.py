#!/usr/bin/env python3
"""Validate this repository's skill conventions using only Python's standard library.

This is not a general YAML or Markdown parser. Required frontmatter fields use
one-line JSON double-quoted strings or restricted plain strings; numeric and
date-like scalar values must be quoted. Other metadata fields are not parsed.
Markdown checks
cover inline/image links and reference links, excluding fenced/inline code and
HTML comments. Local link paths and reference definitions are checked; URL
availability and heading fragments are not. Files checked for UTF-8 are Markdown
and JSON files inside skills; the repository README is not a skill.

Exit codes: 0 valid, 1 validation failed, 2 invalid invocation/discovery failure.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


NAME = re.compile(r"[a-z0-9\u4e00-\u9fff]+(?:-[a-z0-9\u4e00-\u9fff]+)*\Z")
VERSION = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
                     r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z")
DEFINITION = re.compile(r"(?m)^ {0,3}\[([^\]\n]+)\]:[ \t]*(.*)$")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
NON_STRING_PLAIN = re.compile(
    r"[-+]?(?:(?:\d[\d_]*(?:\.[\d_]*)?|\.[\d_]+)(?:e[-+]?\d+)?"
    r"|0[xob][0-9a-f_]+|\.(?:inf|nan)|\d[\d_]*(?::[0-5]?\d)+(?:\.\d*)?)"
    r"|\d{4}-\d{2}-\d{2}(?:[Tt ]\d.*)?", re.I)


def within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def mask(text):
    """Keep newlines/offsets so diagnostics still point to the original source."""
    return "".join("\n" if char == "\n" else " " for char in text)


def prose(text):
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            lines.append(mask(line))
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
            lines.append(mask(line))
        else:
            lines.append(line)
    text = "".join(lines)
    text = re.sub(r"<!--.*?-->", lambda match: mask(match[0]), text, flags=re.S)
    return re.sub(r"(?<!`)(`+)(?!`)(.*?)\1(?!`)", lambda match: mask(match[0]), text, flags=re.S)


def closing(text, start, opener, closer):
    depth = 1
    index = start + 1
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def destination(text, start=0):
    """Read a Markdown destination (angle brackets or balanced parentheses)."""
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    if index < len(text) and text[index] == "<":
        end = closing(text, index, "<", ">")
        if end < 0:
            return None, index
        return text[index + 1:end], end + 1
    begin = index
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            index += 2
            continue
        if char.isspace():
            break
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                break
            depth -= 1
        index += 1
    if depth:
        return None, index
    return text[begin:index], index


def label_key(label):
    return " ".join(label.split()).casefold()


def reject_constant(value):
    raise ValueError("JSON 不允许常量 " + value)


def markdown_links(text):
    """Yield (line, destination, missing_reference) for conventional links."""
    text = prose(text)
    definitions = {}
    for match in DEFINITION.finditer(text):
        target, _ = destination(match[2])
        line = text.count("\n", 0, match.start()) + 1
        if target is None or not target:
            yield line, None, "无效的链接引用定义：" + match[1]
        else:
            definitions.setdefault(label_key(match[1]), target)
            yield line, target, None
    text = DEFINITION.sub(lambda match: mask(match[0]), text)
    for match in re.finditer(r"(?<!\\)\[", text):
        start = match.start()
        end = closing(text, start, "[", "]")
        if end < 0:
            continue
        label = text[start + 1:end]
        index = end + 1
        line = text.count("\n", 0, start) + 1
        if index < len(text) and text[index] == "(":
            target, after = destination(text, index + 1)
            if target is None:
                continue
            while after < len(text) and text[after].isspace():
                after += 1
            if after < len(text) and text[after] in "\"'":
                quote = text[after]
                after += 1
                while after < len(text) and text[after] != quote:
                    after += 2 if text[after] == "\\" else 1
                after += 1
            elif after < len(text) and text[after] == "(":
                after = closing(text, after, "(", ")") + 1
            while after < len(text) and text[after].isspace():
                after += 1
            if after < len(text) and text[after] == ")":
                yield line, target, None
        elif index < len(text) and text[index] == "[":
            ref_end = closing(text, index, "[", "]")
            if ref_end < 0:
                continue
            key = label_key(text[index + 1:ref_end] or label)
            if key not in definitions:
                yield line, None, "未定义的链接引用：" + key
        # Shortcut references resolve through definitions, checked above.


class Validator:
    def __init__(self):
        self.errors = []

    def error(self, path, message, line=None):
        location = str(path) + (":" + str(line) if line else "")
        self.errors.append("{}: {}".format(location, message))

    def scalar(self, value):
        if value.startswith('"'):
            parsed = json.loads(value)
            if not isinstance(parsed, str):
                raise ValueError("必须是字符串")
        else:
            if (not value or value[0] in "'[]{},&*!|>@`%#" or re.match(r"[-?:](?:\s|$)", value)
                    or re.search(r":(?:\s|$)|\s#", value)
                    or value.lower() in {"true", "false", "null", "yes", "no", "on", "off", "~"}
                    or NON_STRING_PLAIN.fullmatch(value)):
                raise ValueError("请使用单行 JSON 双引号字符串或简单 plain 字符串")
            parsed = value
        if not parsed.strip() or any(ord(char) < 32 for char in parsed):
            raise ValueError("必须是非空的单行字符串，不能包含控制字符")
        return parsed

    def frontmatter(self, path, text, skill_name):
        lines = text.splitlines()
        if len(lines) > 500:
            self.error(path, "SKILL.md 不能超过 500 行（当前 {} 行）".format(len(lines)))
        if not lines or lines[0] != "---":
            self.error(path, "文件必须以 --- frontmatter 开始")
            return
        try:
            end = lines.index("---", 1)
        except ValueError:
            self.error(path, "frontmatter 缺少结束的 ---")
            return
        fields = {}
        previous_field = None
        for number, line in enumerate(lines[1:end], 2):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line[0].isspace() and previous_field:
                self.error(path, previous_field + " 必须写在单独一行，不能包含缩进续行", number)
            match = re.match(r"^(name|description|version):(?:[ \t]+(.*))?$", line)
            if not match:
                previous_field = None
                continue
            key, value = match.groups()
            previous_field = key
            if key in fields:
                self.error(path, "重复的元数据字段：" + key, number)
                continue
            fields[key] = None
            try:
                fields[key] = self.scalar((value or "").strip())
            except ValueError as error:
                self.error(path, "{}：{}".format(key, error), number)
        for required in ("name", "description", "version"):
            if required not in fields:
                self.error(path, "缺少元数据字段：" + required)
        name = fields.get("name")
        if name is not None and (not NAME.fullmatch(name) or len(name) > 64 or name != skill_name):
            self.error(path, "name 必须与目录名相同，至多 64 字符，仅含中文汉字/小写字母/数字及单个分隔连字符")
        description = fields.get("description")
        if description is not None and len(description) > 1024:
            self.error(path, "description 不能超过 1024 字符")
        version = fields.get("version")
        if version is not None and not VERSION.fullmatch(version):
            self.error(path, "version 必须是 MAJOR.MINOR.PATCH，可选 -预发布 与 +构建 后缀：" + version)
        if not "\n".join(lines[end + 1:]).strip():
            self.error(path, "缺少正文")

    def links(self, path, text, root):
        for line, target, error in markdown_links(text):
            if error:
                self.error(path, error, line)
                continue
            target = re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~\\])", r"\1", target)
            if target.startswith("//") or (SCHEME.match(target) and not target.lower().startswith("file:")):
                continue
            try:
                local = unquote(urlsplit(target).path, errors="strict")
                if target.lower().startswith("file:") or local.startswith("/"):
                    self.error(path, "本地链接必须使用 skill 内的相对路径：" + target, line)
                    continue
                resolved = (path.parent / local).resolve() if local else path.resolve()
                if not within(resolved, root):
                    self.error(path, "链接越过 skill 目录：" + target, line)
                elif not resolved.exists():
                    self.error(path, "链接目标不存在：" + target, line)
            except (OSError, ValueError, RuntimeError) as exception:
                self.error(path, "无效链接 {}：{}".format(target, exception), line)

    def evals(self, path, text, skill_name):
        try:
            data = json.loads(text, parse_constant=reject_constant)
        except ValueError as error:
            self.error(path, "无效 JSON：" + str(error))
            return
        if not isinstance(data, dict):
            self.error(path, "顶层必须是包含 skill_name 和 evals 的对象")
            return
        if data.get("skill_name") != skill_name:
            self.error(path, "skill_name 必须与 skill 目录名相同")
        cases = data.get("evals")
        if not isinstance(cases, list):
            self.error(path, "evals 必须是数组")
            return
        seen = set()
        for index, case in enumerate(cases):
            prefix = "evals[{}]".format(index)
            if not isinstance(case, dict):
                self.error(path, prefix + " 必须是对象")
                continue
            identifier = case.get("id")
            if type(identifier) is not int:
                self.error(path, prefix + ".id 必须是整数（不能是布尔值）")
            elif identifier in seen:
                self.error(path, prefix + ".id 重复：" + str(identifier))
            else:
                seen.add(identifier)
            for key in ("name", "prompt"):
                if not isinstance(case.get(key), str) or not case[key].strip():
                    self.error(path, prefix + "." + key + " 必须是非空字符串")
            for key in ("expected_behavior", "must_not"):
                value = case.get(key)
                if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
                    self.error(path, prefix + "." + key + " 必须是非空字符串数组，且每项非空")

    def report(self, path, skills):
        """Check an evaluation report: schema, coverage arithmetic, and version pinning."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
        except (OSError, UnicodeError, ValueError) as error:
            self.error(path, "无效 JSON 或无法读取：" + str(error))
            return
        if not isinstance(data, dict):
            self.error(path, "顶层必须是包含 date/type/execution/coverage/limitations/results 的对象")
            return
        for key in ("date", "type", "execution", "coverage", "limitations", "results"):
            if key not in data:
                self.error(path, "缺少顶层字段：" + key)
        coverage = data.get("coverage")
        if isinstance(coverage, dict):
            numerals = {k: coverage.get(k) for k in
                        ("defined_cases", "executed_cases", "passed_cases", "not_executed_cases")}
            bad = [k for k, v in numerals.items() if type(v) is not int or v < 0]
            if bad:
                self.error(path, "coverage 字段必须是非负整数：" + "、".join(bad))
            else:
                if numerals["executed_cases"] + numerals["not_executed_cases"] != numerals["defined_cases"]:
                    self.error(path, "coverage 不一致：executed + not_executed 应等于 defined_cases")
                if numerals["passed_cases"] > numerals["executed_cases"]:
                    self.error(path, "coverage 不一致：passed_cases 不能超过 executed_cases")
        elif coverage is not None:
            self.error(path, "coverage 必须是对象")
        results = data.get("results")
        if not isinstance(results, list) or not results:
            self.error(path, "results 必须是非空数组")
            return
        expected = {}
        for skill in skills:
            expected[skill.name] = self.eval_ids(skill)
        seen = set()
        for index, result in enumerate(results):
            prefix = "results[{}]".format(index)
            if not isinstance(result, dict):
                self.error(path, prefix + " 必须是对象")
                continue
            skill_name = result.get("skill_name")
            identifier = result.get("eval_id")
            if skill_name not in expected:
                self.error(path, "{} 引用了不存在的 skill：{}".format(prefix, skill_name))
                continue
            if type(identifier) is not int:
                self.error(path, prefix + ".eval_id 必须是整数")
            elif identifier not in expected[skill_name]:
                self.error(path, "{}.eval_id {} 在该 skill 的用例中不存在".format(prefix, identifier))
            elif (skill_name, identifier) in seen:
                self.error(path, "同一 skill 的用例被重复记录：{} #{}".format(skill_name, identifier))
            else:
                seen.add((skill_name, identifier))
            if not isinstance(result.get("output"), str) or not result["output"].strip():
                self.error(path, prefix + ".output 必须是非空字符串")
            pinned = result.get("source_sha256")
            if not isinstance(pinned, dict) or not pinned:
                self.error(path, prefix + ".source_sha256 必须是非空对象")
            elif not result.get("stale_revision"):
                root = next(skill for skill in skills if skill.name == skill_name)
                for name, digest in pinned.items():
                    relative = name.split("/", 1)[1] if "/" in name else name
                    target = root / relative
                    if not target.is_file():
                        self.error(path, "{}.source_sha256 指向不存在的文件：{}".format(prefix, name))
                    elif hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                        self.error(path, "{}：{} 的内容已与该报告记录的版本不符；重新执行评估并更新记录，"
                                         "或在该条结果注明 stale_revision".format(prefix, name))

    def eval_ids(self, root):
        path = root / "evals" / "evals.json"
        try:
            cases = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant).get("evals")
        except (OSError, UnicodeError, ValueError, AttributeError):
            return set()
        return {case.get("id") for case in cases if isinstance(case, dict)} if isinstance(cases, list) else set()

    def skill(self, root):
        if not NAME.fullmatch(root.name) or len(root.name) > 64:
            self.error(root, "skill 目录名不符合中文汉字/小写字母/数字及单个连字符的命名规范（最多 64 字符）")
        main = root / "SKILL.md"
        eval_file = root / "evals" / "evals.json"
        try:
            files = set(root.rglob("*.md")) | set(root.rglob("*.json")) | {main, eval_file}
            for path in sorted(files):
                if not within(path.resolve(), root):
                    self.error(path, "文件通过符号链接越过 skill 目录")
                    continue
                if not path.is_file():
                    self.error(path, "缺少文件或不是普通文件")
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as error:
                    self.error(path, "无法按 UTF-8 读取：" + str(error))
                    continue
                if path == main:
                    self.frontmatter(path, text, root.name)
                    metadata = re.match(r"\A---\n.*?\n---(?:\n|\Z)", text, flags=re.S)
                    if metadata:
                        text = mask(metadata[0]) + text[metadata.end():]
                if path.suffix == ".md":
                    self.links(path, text, root)
                if path == eval_file:
                    self.evals(path, text, root.name)
        except (OSError, RuntimeError, ValueError) as error:
            self.error(root, "无法检查 skill 文件：" + str(error))


def discover(paths):
    skills = set()
    for raw in paths:
        path = Path(raw).expanduser().resolve()
        if path.is_file() and path.name == "SKILL.md":
            path = path.parent
        if not path.is_dir():
            raise ValueError("路径必须是仓库目录、skill 目录或 SKILL.md：" + str(path))
        if (path / "SKILL.md").exists() or (path / "SKILL.md").is_symlink():
            skills.add(path)
            continue
        found = [child for child in path.iterdir() if child.is_dir() and (
            (child / "SKILL.md").exists() or (child / "SKILL.md").is_symlink())]
        if not found:
            raise ValueError("目录内未找到 SKILL.md：" + str(path))
        for child in found:
            if child.is_symlink():
                raise ValueError("skill 目录不允许是符号链接：" + str(child))
            skills.add(child)
    return sorted(skills)


def manifest(skills):
    """Emit deterministic per-file digests so evaluation reports stay reproducible."""
    entries = []
    for skill in skills:
        files = {}
        for path in sorted(skill.rglob("*")):
            if not path.is_file() or path.is_symlink() or not within(path.resolve(), skill):
                continue
            try:
                files[path.relative_to(skill).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            except (OSError, ValueError):
                continue
        entries.append({"skill_name": skill.name, "files": files})
    return json.dumps({"skills": entries}, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", metavar="PATH", help="仓库目录、skill 目录或 SKILL.md；默认使用脚本所在仓库")
    parser.add_argument("--manifest", action="store_true",
                        help="只输出各 skill 文件的 SHA-256 摘要（稳定顺序），供评估报告记录版本；不执行结构校验")
    parser.add_argument("--report", metavar="FILE", action="append", default=[],
                        help="校验一份评估报告：字段、覆盖率算术、用例编号，以及记录的文件摘要是否仍与当前 skill 一致")
    args = parser.parse_args()
    try:
        skills = discover(args.paths or [Path(__file__).resolve().parent.parent])
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    if args.manifest:
        sys.stdout.write(manifest(skills))
        return 0
    validator = Validator()
    for raw in args.report:
        path = Path(raw).expanduser()
        if not path.is_file():
            parser.error("报告文件不存在：" + str(path))
        validator.report(path, skills)
    for skill in skills:
        validator.skill(skill)
    if validator.errors:
        for error in validator.errors:
            print(error, file=sys.stderr)
        print("校验失败：{} 个 skill，{} 个问题。".format(len(skills), len(validator.errors)), file=sys.stderr)
        return 1
    print("校验通过：{} 个 skill。".format(len(skills)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
