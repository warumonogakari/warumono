"""
縦書き OCR 後処理スクリプト

A: パターンベースの自動修正
B: 明らかな崩壊箇所に <!-- OCR_CHECK --> タグを付与

使い方:
    uv run python tategaki_ocr_fix.py
    uv run python tategaki_ocr_fix.py --input /path/to/input.md --output /path/to/output.md
    uv run python tategaki_ocr_fix.py --dry-run   # MD を書き換えず結果だけ表示
"""

import argparse
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DEFAULT_MD = BASE_DIR / "省察的実践とは何か/省察的実践とは何か.md"

# ------------------------------------------------------------------ #
# A: 自動修正ルール  (pattern, replacement)                            #
# ------------------------------------------------------------------ #

AUTO_FIX_RULES: list[tuple[str, str]] = [
    # 訳注番号: ! → 1、? → 7 など誤認識しやすい文字
    (r"訳注!", "訳注1"),
    (r"訳注\?", "訳注?"),  # 本物の?は残す
    # 半角山括弧 → 全角（〈〉で囲まれた強調表現）
    (r"<(わざ|直観|省察|先生方|特殊な|アカデミック|管理された実験)>", r"〈\1〉"),
    # >>>>> などの角括弧連続 → 〉
    (r">{3,}", "〉"),
    # 明白な英単語スペルミス
    (r"\barlistry\b", "artistry"),
    (r"\bSchn\b", "Schön"),
    # 括弧+数字の繰り返し崩壊: (22 → (2)、(33 → (3) など
    (r"\((\d)\1+", r"(\1)"),
    # Copyright 記号の誤認識
    (r"Copyright @", "Copyright ©"),
]

# ------------------------------------------------------------------ #
# B: 崩壊検知条件                                                       #
# ------------------------------------------------------------------ #

# 条件1: 同一文字の4連続以上（日本語文字以外）
RE_REPEAT_CHAR = re.compile(r"([^\u3040-\u9FFF\s])\1{3,}")

# 条件4: 10文字以上なのに日本語文字がゼロの行
RE_NO_JAPANESE = re.compile(r"^[^\u3040-\u9FFF]{10,}$")

# 日本語文字カウント用
RE_JAPANESE = re.compile(r"[\u3040-\u9FFF]")


def count_japanese(text: str) -> int:
    return len(RE_JAPANESE.findall(text))


def is_blank_page(text: str) -> bool:
    return text.strip() == ""


def detect_b_issues(page_num: int, text: str) -> list[str]:
    """崩壊検知。問題の説明リストを返す（空なら問題なし）。"""
    if is_blank_page(text):
        return []

    issues = []
    lines = text.splitlines()
    jp_count = count_japanese(text)

    # 条件1: 同一文字の4連続以上
    for line in lines:
        m = RE_REPEAT_CHAR.search(line)
        if m:
            issues.append(f"同一文字連続: {m.group()!r}")
            break

    # 条件2: 2文字以下の行が3行以上
    short_lines = [l for l in lines if 0 < len(l.strip()) <= 2]
    if len(short_lines) >= 3:
        issues.append(f"短行多発: {len(short_lines)}行 ({short_lines[:3]}…)")

    # 条件3: テキストが50文字以上あるのに日本語が20文字未満
    # （扉ページ・タイトルページなど意図的に短いページは除外）
    total_len = len(text.strip())
    if total_len >= 50 and jp_count < 20:
        issues.append(f"日本語文字少なすぎ: {jp_count}文字 (全体{total_len}文字)")

    # 条件4: ページ全体の日本語が50文字未満 かつ 日本語ゼロの長い行がある
    # （英日混在の正常ページは除外し、本当に崩壊しているページのみ検知）
    if jp_count < 50:
        for line in lines:
            if RE_NO_JAPANESE.match(line.strip()):
                issues.append(f"日本語ゼロ行: {line.strip()[:40]!r}")
                break

    return issues


# ------------------------------------------------------------------ #
# MD パース・シリアライズ                                               #
# ------------------------------------------------------------------ #

PAGE_MARKER_RE = re.compile(r"<!-- page (\d+) -->\n(.*?)(?=<!-- page \d+ -->|\Z)", re.DOTALL)


def parse_md(md_path: Path) -> dict[int, str]:
    content = md_path.read_text(encoding="utf-8")
    return {int(m.group(1)): m.group(2).strip() for m in PAGE_MARKER_RE.finditer(content)}


def build_md(md_path: Path, pages: dict[int, str]) -> None:
    chunks = []
    for n in sorted(pages.keys()):
        chunks.append(f"<!-- page {n:03d} -->")
        chunks.append(pages[n])
        chunks.append("")
    md_path.write_text("\n".join(chunks) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ #
# 処理本体                                                              #
# ------------------------------------------------------------------ #

def apply_auto_fixes(text: str) -> tuple[str, list[str]]:
    """自動修正を適用して (修正後テキスト, 修正ログ) を返す。"""
    logs = []
    for pattern, replacement in AUTO_FIX_RULES:
        new_text, count = re.subn(pattern, replacement, text)
        if count:
            logs.append(f"  A修正: {pattern!r} → {replacement!r} ({count}箇所)")
            text = new_text
    return text, logs


def apply_check_tag(text: str, issues: list[str]) -> str:
    """崩壊検知されたテキストに OCR_CHECK タグを付与する。"""
    tag_lines = ["<!-- OCR_CHECK"] + [f"     {i}" for i in issues] + ["-->"]
    return "\n".join(tag_lines) + "\n" + text


def main() -> None:
    parser = argparse.ArgumentParser(description="縦書き OCR 後処理")
    parser.add_argument("--input",   type=Path, default=DEFAULT_MD, help="入力 MD ファイル")
    parser.add_argument("--output",  type=Path, default=None,       help="出力 MD ファイル（省略時は上書き）")
    parser.add_argument("--dry-run", action="store_true",           help="MD を書き換えず結果だけ表示")
    args = parser.parse_args()

    in_path  = args.input
    out_path = args.output or args.input

    if not in_path.exists():
        print(f"エラー: ファイルが見つかりません: {in_path}")
        sys.exit(1)

    pages = parse_md(in_path)
    print(f"=== OCR 後処理開始: {len(pages)} ページ ===\n")

    fixed_pages: dict[int, str] = {}
    total_a_fixes = 0
    check_pages: list[int] = []

    for n in sorted(pages.keys()):
        text = pages[n]

        # A: 自動修正
        text, a_logs = apply_auto_fixes(text)
        if a_logs:
            total_a_fixes += len(a_logs)
            print(f"[page {n:03d}] 自動修正")
            for log in a_logs:
                print(log)

        # B: 崩壊検知
        issues = detect_b_issues(n, text)
        if issues:
            check_pages.append(n)
            print(f"[page {n:03d}] 要確認タグ付与")
            for issue in issues:
                print(f"  B検知: {issue}")
            text = apply_check_tag(text, issues)

        fixed_pages[n] = text

    print(f"\n=== 後処理完了 ===")
    print(f"自動修正: {total_a_fixes} 箇所")
    print(f"要確認タグ: {len(check_pages)} ページ {check_pages if check_pages else ''}")

    if args.dry_run:
        print("\n（dry-run: MD は書き換えていません）")
    else:
        build_md(out_path, fixed_pages)
        print(f"MD 書き込み完了: {out_path}")


if __name__ == "__main__":
    main()
