"""
対話形式 Markdown → PDF 変換スクリプト（AnticipationDialogue 向け）
使用方法: uv run python dialogue_md_to_pdf.py <input.md> <output.pdf>

汎用エンジン（md_to_html_core）に対話特有のルールを注入する。
追加ルール:
  - ト書き《 》行  → .stage-direction スタイル
  - セリフ行（**名前**：テキスト） → .dialogue スタイル
"""
import sys
import re
from md_to_pdf import LineRule, convert, inline_format

# ---- 対話形式の拡張ルール ----

_DIALOGUE_LINE_RULES: list[LineRule] = [
    LineRule(
        match=lambda line: "《" in line and "》" in line,
        render=lambda line: f'<p class="stage-direction">{inline_format(line, _DIALOGUE_INLINE_RULES)}</p>',
    ),
    LineRule(
        match=lambda line: bool(re.match(r"^\*\*[^*]+\*\*[：:]", line)),
        render=lambda line: f'<p class="dialogue">{inline_format(line, _DIALOGUE_INLINE_RULES)}</p>',
    ),
]

_DIALOGUE_INLINE_RULES: list[tuple[str, str]] = [
    (r"《([^》]+)》", r'<span class="stage-note">《\1》</span>'),
]

_DIALOGUE_CSS = """\
  .stage-direction {
    color: #555;
    font-size: 9.5pt;
    margin: 0.6em 0;
  }
  .stage-note {
    color: #555;
    font-size: 9.5pt;
  }
  .dialogue {
    margin: 0.5em 0 0.5em 1em;
  }"""

# ---- エントリポイント ----

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用方法: uv run python dialogue_md_to_pdf.py <input.md> <output.pdf>")
        sys.exit(1)
    convert(
        sys.argv[1],
        sys.argv[2],
        extra_line_rules=_DIALOGUE_LINE_RULES,
        extra_inline=_DIALOGUE_INLINE_RULES,
        extra_css=_DIALOGUE_CSS,
    )
