#!/usr/bin/env python3
"""team-mode skill 自检：结构、引用、登记、禁用词、表格。

用法:
    python3 scripts/check-skill.py            # 全量（错误 + 警告）
    python3 scripts/check-skill.py --quiet    # 只输出错误

错误（退出码 1）:
    1. frontmatter 缺失或字段不全
    2. 引用了不存在的文件（含大小写不符、路径穿越、指向仓库外）
    3. 目录缺失/为空，或文件未在 SKILL.md 登记（含表格里写了不存在的文件）
    4. 禁用词（已确认不存在的能力名），以及未加否定的 log()
    5. Markdown 表格列数不一致、代码围栏未闭合
    6. 角色/模板/prompt 缺少必需小节

警告（不影响退出码）:
    description 偏短、文件过长、prompt 占位符不全（name 与目录不一致只作提示）

仅依赖标准库，Python 3.9+。
"""

from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUIET = "--quiet" in sys.argv
KNOWN_ARGS = {"--quiet"}

errors: list[str] = []
warnings: list[str] = []
infos: list[str] = []


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def note_error(msg: str) -> None:
    if msg not in errors:
        errors.append(msg)


@lru_cache(maxsize=None)
def read(p: Path) -> str:
    """读取 UTF-8（容忍 BOM）；失败时记错误并返回空串，不中断其它检查。"""
    try:
        return p.read_bytes().decode("utf-8-sig")
    except OSError as e:
        note_error(f"{rel(p)}: 读取失败（{e.__class__.__name__}）")
    except UnicodeDecodeError:
        note_error(f"{rel(p)}: 不是合法 UTF-8，无法检查")
    return ""


# ---------- 0. 参数 ----------
def check_args() -> bool:
    unknown = [a for a in sys.argv[1:] if a not in KNOWN_ARGS]
    if unknown:
        print(f"未知参数：{' '.join(unknown)}")
        print("用法：python3 scripts/check-skill.py [--quiet]")
        return False
    return True


# ---------- 1. 文件枚举 ----------
def md_files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.md"):
        parts = p.relative_to(ROOT).parts
        if any(part.startswith(".") or part == "node_modules" for part in parts):
            continue
        out.append(p)
    return sorted(out)


# ---------- 2. frontmatter ----------
def check_frontmatter() -> None:
    p = ROOT / "SKILL.md"
    if not p.is_file():
        note_error("SKILL.md: 文件不存在")
        return
    text = read(p)
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        note_error("SKILL.md: 缺少 YAML frontmatter（文件首行应为 ---）")
        return
    fm = m.group(1)
    name = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
    desc = re.search(r"^description:\s*(.*)$", fm, re.M)
    if not name:
        note_error("SKILL.md: frontmatter 缺少 name")
    elif name.group(1) != ROOT.name:
        infos.append(
            f"SKILL.md: name={name.group(1)} 与目录名 {ROOT.name} 不一致"
            "（仓库克隆/改名安装时正常，不影响加载）"
        )
    if not desc:
        note_error("SKILL.md: frontmatter 缺少 description")
        return
    value = desc.group(1).strip()
    if value in {">", "|", ">-", "|-"}:  # YAML 块标量：拼接后续缩进行
        rest = fm[desc.end() :].splitlines()
        block = []
        for line in rest:
            if line.startswith(" ") or line.startswith("\t"):
                block.append(line.strip())
            elif line.strip():
                break
        value = " ".join(block)
    if len(value) < 40:
        warnings.append("SKILL.md: description 偏短，可能影响技能匹配")


# ---------- 3. 路径存在性（精确大小写、禁止穿越、禁止指向仓库外） ----------
def exact_exists(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    if any(part in ("..", "") for part in parts):
        return False
    cur = ROOT
    for part in parts:
        if not cur.is_dir():
            return False
        names = {e.name for e in cur.iterdir()}
        if part not in names:
            return False
        cur = cur / part
    if not cur.is_file():
        return False
    try:
        return cur.resolve().is_relative_to(ROOT.resolve())
    except (AttributeError, OSError):
        return False


def iter_lines_outside_fences(text: str):
    in_fence = False
    for no, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            yield no, line, True  # 围栏行本身标记为 fence
            continue
        yield no, line, in_fence
    if in_fence:
        note_error("代码围栏未闭合（最后一个 ``` 没有配对），后续内容会被跳过")


# ---------- 4. 引用 ----------
LINK_RE = re.compile(
    r"(?:references|roles|templates|prompts|scripts)/[\w\u4e00-\u9fff.\-/]+\.(?:md|py|sh)"
)


def check_links() -> None:
    for f in md_files():
        for no, line, in_fence in iter_lines_outside_fences(read(f)):
            if in_fence:
                continue
            for m in LINK_RE.finditer(line):
                target = m.group(0).rstrip(".,;:，。；：")
                if any(c in target for c in "<>*$`"):
                    continue
                if not exact_exists(target):
                    note_error(f"{rel(f)}:{no}: 引用了不存在的文件 {target}")


# ---------- 5. 登记 ----------
SKILL_DIRS = ("roles", "templates", "references", "prompts")


def check_registry() -> None:
    skill = read(ROOT / "SKILL.md")
    lines = skill.splitlines()
    for sub in SKILL_DIRS:
        d = ROOT / sub
        if not d.is_dir():
            note_error(f"{sub}/: 目录不存在")
            continue
        files = sorted(d.glob("*.md"))
        if not files:
            note_error(f"{sub}/: 目录为空（应至少有一个 .md）")
        for f in files:
            registered = f"{sub}/{f.name}" in skill or any(
                f.name in line and line.lstrip().startswith("|") for line in lines
            )
            if not registered:
                note_error(f"{sub}/{f.name}: 未在 SKILL.md 登记或索引")

    # 表格里写了不存在的文件（防止模板被删后仍显示"通过"）
    for no, line, in_fence in iter_lines_outside_fences(skill):
        if in_fence or not line.lstrip().startswith("|"):
            continue
        for token in re.findall(r"[A-Za-z][\w.-]*\.md", line):
            if token in ("SKILL.md", "README.md"):
                continue
            if not any((ROOT / sub / token).is_file() for sub in SKILL_DIRS):
                note_error(f"SKILL.md:{no}: 表格引用的文件不存在 {token}")


# ---------- 6. 禁用词 ----------
# 已确认不存在于 DSH/agent-team 的能力名；命中即错误（否定语境除外）。
FORBIDDEN = [
    "mimo-v2",
    "toDoWrite",
    "team_spawn",
    "team_send",
    "team_list",
    "team_note",
    "team_board",
    "team_dismiss",
    "maxChainHops",
    "默认 10 轮",
    "11 维验收",
]
NEGATIONS = ("不存在", "没有", "不要", "别调用", "不是", "已删", "改为", "禁止")
CLAUSE_SPLIT = re.compile(r"[，。；;、]")


def check_forbidden() -> None:
    for f in md_files():
        if f == ROOT / "README.md":  # 变更历史里允许出现旧名
            continue
        for no, line, in_fence in iter_lines_outside_fences(read(f)):
            if in_fence:
                continue
            clauses = CLAUSE_SPLIT.split(line)
            for token in FORBIDDEN:
                for clause in clauses:
                    if token in clause and not any(n in clause for n in NEGATIONS):
                        note_error(
                            f"{rel(f)}:{no}: 禁用词 {token!r}（该能力不存在，确认是否误写）"
                        )
            if "log()" in line and not any(n in line for n in NEGATIONS):
                note_error(f"{rel(f)}:{no}: 出现未加否定的 log()（子代理没有该工具）")


# ---------- 7. 表格 ----------
TABLE_SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
INLINE_CODE = re.compile(r"`[^`]*`")


def count_cells(line: str) -> int:
    s = INLINE_CODE.sub("", line.strip())
    s = s.replace(r"\|", "x")
    return s.count("|") - 1


def check_tables() -> None:
    for f in md_files():
        lines = read(f).splitlines()
        in_fence = False
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("```"):
                in_fence = not in_fence
                i += 1
                continue
            if in_fence:
                i += 1
                continue
            if line.strip().startswith("|") and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
                width = count_cells(line)
                j = i
                while j < len(lines) and lines[j].strip().startswith("|"):
                    if count_cells(lines[j]) != width:
                        note_error(
                            f"{rel(f)}:{j + 1}: 表格列数不一致"
                            f"（表头 {width} 列，本行 {count_cells(lines[j])} 列）"
                        )
                    j += 1
                i = j
            else:
                i += 1


# ---------- 8. 结构 ----------
def check_structure() -> None:
    skill = read(ROOT / "SKILL.md")
    for anchor in ("值不值得开团队", "平台检测", "退出阀", "预算表", "盲审"):
        if anchor not in skill:
            note_error(f"SKILL.md: 缺少关键小节内容 {anchor!r}")

    for f in sorted((ROOT / "roles").glob("*.md")):
        text = read(f)
        for anchor in ("【汇报方式】", "未决项", "log()"):
            if anchor not in text:
                note_error(f"{rel(f)}: 缺少 {anchor!r}（汇报契约不完整）")
        if "send_message" not in text:
            note_error(f"{rel(f)}: 未说明跨平台汇报方式（send_message 降级）")

    for f in sorted((ROOT / "templates").glob("*.md")):
        text = read(f)
        for anchor in ("## 适用", "## 步骤序列", "## DoD"):
            if anchor not in text:
                note_error(f"{rel(f)}: 缺少 {anchor!r}")

    for f in sorted((ROOT / "prompts").glob("*.md")):
        text = read(f)
        for anchor in ("{{REPO}}", "问题清单", "不要给"):
            if anchor not in text:
                warnings.append(f"{rel(f)}: 缺少 {anchor!r}，盲审约束可能不完整")


# ---------- 9. 体量 ----------
def check_size() -> None:
    total = 0
    files = md_files()
    for f in files:
        n = len(read(f).splitlines())
        total += n
        if f.name == "SKILL.md" and n > 200:
            warnings.append(f"SKILL.md 已 {n} 行（>200），考虑继续下沉到 references/")
        elif n > 260:
            warnings.append(f"{rel(f)} 已 {n} 行，考虑拆分")
    if not QUIET:
        print(f"  文件 {len(files)} 个，合计 {total} 行")


def main() -> int:
    if not check_args():
        return 2
    if not QUIET:
        print("team-mode 自检")
    check_frontmatter()
    check_links()
    check_registry()
    check_forbidden()
    check_tables()
    check_structure()
    check_size()

    if not QUIET:
        for i in infos:
            print(f"  ℹ️  {i}")
        for w in warnings:
            print(f"  ⚠️  {w}")
    for e in errors:
        print(f"  ❌ {e}")
    if errors:
        print(f"\n失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"\n✅ 通过：0 个错误，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
