#!/usr/bin/env python3
"""校验书稿结构：章节登记、章级锚点、引用键与交叉引用目标。"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_ROOT = ROOT / "book" / "outline.md"
XREF_PREFIXES = ("fig-", "tbl-", "eq-", "sec-", "lst-")
CITE_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9_][A-Za-z0-9_:.#$%&-]*)")
ANCHOR_RE = re.compile(r"\{#([A-Za-z0-9][\w.-]*)(?:[ \t]+[^}\n]*)?\}")
CHAPTER_ROW_RE = re.compile(
    r"^[ \t]*\|[^|\n]*\|[ \t]*`(chapters/\d{2}-[a-z0-9-]+\.qmd)`[ \t]*\|",
    re.MULTILINE,
)
# 短于起始围栏的标记可以出现在代码示例里。
FENCED_CODE_RE = re.compile(
    r"^ {0,3}(?P<fence>(?P<marker>`|~)(?P=marker){2,})(?!(?P=marker))[^\n]*\n"
    r".*?^ {0,3}(?P=fence)(?P=marker)*[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


def strip_code(text):
    text = FENCED_CODE_RE.sub("", text)
    return re.sub(r"`[^`\n]*`", "", text)


def inspect_project():
    output = subprocess.check_output(["quarto", "inspect", "."], cwd=str(ROOT), text=True)
    return json.loads(output)


def bib_keys():
    text = (ROOT / "references.bib").read_text(encoding="utf-8")
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", text))


def main():
    issues = []
    try:
        info = inspect_project()
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print("无法读取 Quarto 项目信息：%s" % error, file=sys.stderr)
        return 1

    chapters = info.get("config", {}).get("book", {}).get("chapters", [])
    if not chapters:
        issues.append("_quarto.yml 没有登记 book.chapters")

    registered = set()
    for relative in chapters:
        path = ROOT / relative
        registered.add(path.resolve())
        if not path.is_file():
            issues.append("登记的章节不存在：%s" % relative)

    chapters_dir = ROOT / "chapters"
    for path in sorted(chapters_dir.rglob("*.qmd")):
        if path.resolve() not in registered:
            issues.append("chapters/ 下未登记的 .qmd：%s" % path.relative_to(ROOT))

    if BOOK_ROOT.is_file():
        expected = CHAPTER_ROW_RE.findall(BOOK_ROOT.read_text(encoding="utf-8"))
        actual = [item for item in chapters if item.startswith("chapters/")]
        if expected != actual:
            issues.append(
                "book/outline.md 的章节顺序与 _quarto.yml 不一致：大纲 %s，配置 %s"
                % (expected, actual)
            )
    else:
        issues.append("缺少写作大纲：book/outline.md")

    keys = bib_keys()
    anchored = {}
    cited = set()
    for relative in chapters:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = strip_code(path.read_text(encoding="utf-8"))
        for anchor in ANCHOR_RE.findall(text):
            if anchor in anchored:
                issues.append(
                    "锚点重复：%s（%s 与 %s）"
                    % (anchor, anchored[anchor], path.relative_to(ROOT))
                )
            anchored[anchor] = str(path.relative_to(ROOT))
        for key in CITE_RE.findall(text):
            if key.startswith(XREF_PREFIXES):
                continue
            cited.add(key)
            if key not in keys:
                issues.append(
                    "引用键未在 references.bib 定义：@%s（%s）" % (key, path.relative_to(ROOT))
                )

    for relative in chapters:
        path = ROOT / relative
        if not path.is_file():
            continue
        for key in CITE_RE.findall(strip_code(path.read_text(encoding="utf-8"))):
            if key.startswith(XREF_PREFIXES) and key not in anchored:
                issues.append(
                    "交叉引用目标不存在：@%s（%s）" % (key, path.relative_to(ROOT))
                )

    for path in sorted(chapters_dir.rglob("*.qmd")):
        match = re.match(r"(\d{2})-", path.name)
        if not match:
            issues.append("章节文件名缺少两位编号：%s" % path.relative_to(ROOT))
            continue
        expected_anchor = "sec-ch%d" % int(match.group(1))
        if anchored.get(expected_anchor) != str(path.relative_to(ROOT)):
            issues.append(
                "缺少章级锚点 {#%s}：%s" % (expected_anchor, path.relative_to(ROOT))
            )

    for key in sorted(keys - cited):
        print("警告：references.bib 中的键未在正文引用：@%s" % key)

    if issues:
        for issue in issues:
            print("错误：%s" % issue, file=sys.stderr)
        print("校验失败：%d 个错误" % len(issues), file=sys.stderr)
        return 1

    print(
        "校验通过：%d 个章节，%d 个文献键，%d 个锚点"
        % (len(chapters), len(keys), len(anchored))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
