"""
縦書き日本語 OCR バッチ処理スクリプト（ndlocr-lite 使用）

使い方:
    uv run python tategaki_ocr_run.py --start 1 --end 50
    uv run python tategaki_ocr_run.py --start 42 --end 42      # 1ページだけやり直し
    uv run python tategaki_ocr_run.py --start 1 --end 50 \\
        --imgdir /path/to/images \\
        --output /path/to/output.md

オプション:
    --start     開始ページ番号（必須）
    --end       終了ページ番号（必須）
    --imgdir    入力画像ディレクトリ（省略時: 省察的実践とは何か/）
    --output    出力 MD ファイルパス（省略時: 省察的実践とは何か/省察的実践とは何か.md）
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR     = Path(__file__).parent
NDLOCR_PY    = BASE_DIR / "ndlocr-lite/.venv/bin/python"
NDLOCR_SCRIPT = BASE_DIR / "ndlocr-lite/src/ocr.py"
NDLOCR_CWD   = BASE_DIR / "ndlocr-lite/src"
IMG_DIR      = BASE_DIR / "省察的実践とは何か"
OUT_MD       = BASE_DIR / "省察的実践とは何か/省察的実践とは何か.md"
TOTAL_PAGES  = 460
MAX_RETRIES  = 3


# ------------------------------------------------------------------ #
# OCR                                                                  #
# ------------------------------------------------------------------ #

def run_ndlocr(img_path: Path, tmp_dir: Path) -> str | None:
    """1ページをOCR処理してテキストを返す。失敗したら None。"""
    cmd = [
        str(NDLOCR_PY), str(NDLOCR_SCRIPT),
        "--sourceimg", str(img_path.resolve()),
        "--output",    str(tmp_dir.resolve()),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(NDLOCR_CWD),
    )
    if result.returncode != 0:
        return None

    txt_path = tmp_dir / f"{img_path.stem}.txt"
    if not txt_path.exists():
        return None

    return txt_path.read_text(encoding="utf-8").strip()


# ------------------------------------------------------------------ #
# MD の読み書き                                                         #
# ------------------------------------------------------------------ #

def page_marker(n: int) -> str:
    return f"<!-- page {n:03d} -->"


def parse_md(md_path: Path) -> dict[int, str]:
    """MD ファイルを読み込み {ページ番号: テキスト} の辞書を返す。"""
    if not md_path.exists():
        return {}

    content = md_path.read_text(encoding="utf-8")
    pages: dict[int, str] = {}

    pattern = re.compile(
        r"<!-- page (\d+) -->\n(.*?)(?=<!-- page \d+ -->|\Z)",
        re.DOTALL,
    )
    for m in pattern.finditer(content):
        pages[int(m.group(1))] = m.group(2).strip()

    return pages


def build_md(md_path: Path, pages: dict[int, str]) -> None:
    """ページ辞書から MD ファイルを再構築する（上書き）。"""
    chunks = []
    for n in sorted(pages.keys()):
        chunks.append(page_marker(n))
        chunks.append(pages[n])
        chunks.append("")  # ページ間の空行
    md_path.write_text("\n".join(chunks) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ #
# メイン                                                               #
# ------------------------------------------------------------------ #

def main() -> None:
    parser = argparse.ArgumentParser(description="縦書き OCR バッチ処理")
    parser.add_argument("--start",  type=int, required=True, help="開始ページ番号")
    parser.add_argument("--end",    type=int, required=True, help="終了ページ番号")
    parser.add_argument("--imgdir", type=Path, default=IMG_DIR,
                        help=f"入力画像ディレクトリ (デフォルト: {IMG_DIR})")
    parser.add_argument("--output", type=Path, default=OUT_MD,
                        help=f"出力 MD ファイルパス (デフォルト: {OUT_MD})")
    args = parser.parse_args()

    img_dir = args.imgdir
    out_md  = args.output

    if args.start < 1 or args.end > TOTAL_PAGES or args.start > args.end:
        print(f"エラー: ページ範囲は 1〜{TOTAL_PAGES} で start <= end にしてください")
        sys.exit(1)

    if not img_dir.is_dir():
        print(f"エラー: 画像ディレクトリが見つかりません: {img_dir}")
        sys.exit(1)

    print(f"=== OCR 処理開始: page {args.start:03d} 〜 {args.end:03d} ===")
    print(f"    画像ディレクトリ: {img_dir}")
    print(f"    出力 MD:          {out_md}\n")

    pages  = parse_md(out_md)
    failed = []

    for n in range(args.start, args.end + 1):
        img_path = img_dir / f"page_{n:03d}.png"

        if not img_path.exists():
            print(f"[SKIP ] page_{n:03d}: 画像ファイルが見つかりません")
            continue

        print(f"[{n:03d}/{args.end:03d}] 処理中 ...", end=" ", flush=True)

        text = None
        for attempt in range(1, MAX_RETRIES + 1):
            with tempfile.TemporaryDirectory() as tmp_dir:
                text = run_ndlocr(img_path, Path(tmp_dir))
            if text is not None:
                break
            if attempt < MAX_RETRIES:
                print(f"リトライ {attempt}/{MAX_RETRIES} ...", end=" ", flush=True)

        if text is None:
            print("失敗")
            failed.append(n)
        else:
            pages[n] = text
            print("完了")

    # MD 再構築
    build_md(out_md, pages)

    # サマリー
    processed = args.end - args.start + 1 - len(failed)
    total_done = len(pages)
    print(f"\n=== 処理完了 ===")
    print(f"今回: {processed} ページ完了 / {len(failed)} ページ失敗")
    if failed:
        print(f"失敗ページ: {failed}")
    print(f"MD 累計: {total_done} / {TOTAL_PAGES} ページ")


if __name__ == "__main__":
    main()
