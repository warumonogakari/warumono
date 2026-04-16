"""
汎用 Markdown → PDF 変換エンジン
使用方法: uv run python md_to_html_core.py <input.md> <output.pdf>
拡張方法: extra_line_rules / extra_inline_rules / extra_css を渡して対話形式などに対応
"""
import sys
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from playwright.sync_api import sync_playwright


@dataclass
class LineRule:
    """1行の特殊処理ルール"""
    match: Callable[[str], bool]   # この行を処理するか判定
    render: Callable[[str], str]   # HTMLに変換（inline_formatは呼び出し側で適用）


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline_format(text: str, extra_inline: list[tuple[str, str]] = []) -> str:
    """インライン書式の変換。extra_inline で追加パターンを先に適用する"""
    for pattern, replacement in extra_inline:
        text = re.sub(pattern, replacement, text)
    # **太字**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # *イタリック*
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    # `コード`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def md_to_html(
    md_text: str,
    extra_line_rules: list[LineRule] = [],
    extra_inline: list[tuple[str, str]] = [],
) -> str:
    """Markdown → HTML 本文変換。extra_line_rules は組み込みルールより先に評価される"""
    lines = md_text.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        # 水平線
        if line.strip() == "---":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr>")
            continue

        # 見出し
        if line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{escape_html(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{escape_html(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{escape_html(line[2:])}</h1>")
            continue

        # リスト
        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = inline_format(line[2:], extra_inline)
            html_lines.append(f"<li>{content}</li>")
            continue
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False

        # 空行
        if line.strip() == "":
            html_lines.append("<p></p>")
            continue

        # 拡張ルール（対話形式など）
        matched = False
        for rule in extra_line_rules:
            if rule.match(line):
                html_lines.append(rule.render(line))
                matched = True
                break
        if matched:
            continue

        # 通常段落
        content = inline_format(line, extra_inline)
        html_lines.append(f"<p>{content}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


_BASE_CSS = """\
  @page { margin: 20mm 18mm; }
  body {
    font-family: "Hiragino Mincho ProN", "Yu Mincho", "MS Mincho", serif;
    font-size: 10.5pt;
    line-height: 1.85;
    color: #1a1a1a;
    max-width: 680px;
    margin: 0 auto;
  }
  h1 {
    font-size: 16pt;
    font-weight: bold;
    text-align: center;
    margin: 1.2em 0 0.3em;
    line-height: 1.5;
  }
  h2 {
    font-size: 11pt;
    font-weight: bold;
    text-align: center;
    color: #444;
    margin: 0 0 1.5em;
  }
  h3 {
    font-size: 11pt;
    font-weight: bold;
    border-left: 4px solid #555;
    padding-left: 8px;
    margin: 1.8em 0 0.6em;
  }
  hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 1.5em 0;
  }
  p {
    margin: 0.3em 0;
  }
  strong { font-weight: bold; }
  ul { margin: 0.5em 0; padding-left: 1.5em; }
  li { margin: 0.2em 0; }"""


def build_html(
    md_text: str,
    title: str,
    extra_line_rules: list[LineRule] = [],
    extra_inline: list[tuple[str, str]] = [],
    extra_css: str = "",
) -> str:
    body = md_to_html(md_text, extra_line_rules, extra_inline)
    css = _BASE_CSS + ("\n" + extra_css if extra_css else "")
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
{css}
</style>
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>"""


def convert(
    md_path: str,
    pdf_path: str,
    extra_line_rules: list[LineRule] = [],
    extra_inline: list[tuple[str, str]] = [],
    extra_css: str = "",
) -> None:
    md_text = Path(md_path).read_text(encoding="utf-8")
    title = Path(md_path).stem
    html = build_html(md_text, title, extra_line_rules, extra_inline, extra_css)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(path=pdf_path, format="A4", print_background=True)
        browser.close()
    print(f"生成完了: {pdf_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用方法: uv run python md_to_html_core.py <input.md> <output.pdf>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
