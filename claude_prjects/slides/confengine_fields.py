#!/usr/bin/env python3
"""ConfEngine投稿用フィールド生成スクリプト

プロポーザルmarkdown（このリポジトリの標準構成）を読み、ConfEngineの
各入力欄に流し込めるHTML/テキストをJSONで出力する。

想定するmdのセクション構成（## 見出し）:
  Title / Target Audience / Learning Outcome / Prerequisites for Attendees /
  Abstract / Outline（見出しが「## Outline」で始まればよい） / 参考文献

変換ルール:
  - ** と * は除去する（ConfEngineはmarkdown非対応。装飾はリッチテキスト側で行う）
  - Title: セクション内の最初の非空行（"> " で始まるメモ行は無視）
  - Abstract / Prerequisites / Learning Outcome: 非空行ごとに <p>
  - Target Audience: プレーンテキスト（段落は空行のまま保持）
  - Outline: "### " → <h3>、"#### " → <h4>、"- " → <li>、"  - " → 入れ子の <li>
  - 参考文献: Outline末尾に <hN>参考文献</hN><ul>...</ul> として連結
    （見出しレベルNはOutline本文の見出しに追随。h4があればh4、なければh3。
      「### スライド付録送り」以降の内部メモは除外）

使い方:
  python3 confengine_fields.py <プロポーザル.md> <出力.json>
"""
import argparse
import json
import pathlib
import re


def find_section(src: str, prefix: str) -> str:
    m = re.search(rf"^## {re.escape(prefix)}[^\n]*\n(.*?)(?=\n## |\Z)", src, re.S | re.M)
    if not m:
        return ""
    body = m.group(1)
    body = re.sub(r"\n---\s*$", "", body.strip())
    return body.strip()


def strip_md(text: str) -> str:
    return text.replace("**", "").replace("*", "")


def paras(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("> ")]
    return "".join(f"<p>{l}</p>" for l in lines)


def outline_html(text: str) -> str:
    out, in_ul, in_sub = [], False, False

    def close_all():
        nonlocal in_ul, in_sub
        if in_sub:
            out.append("</ul></li>")
            in_sub = False
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in text.splitlines():
        if line.startswith("#### "):
            close_all()
            out.append(f"<h4>{line[5:].strip()}</h4>")
        elif line.startswith("### "):
            close_all()
            out.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("  - "):
            if not in_sub:
                out.append("<ul>")
                in_sub = True
            out.append(f"<li>{line[4:].strip()}</li>")
        elif line.startswith("- "):
            if in_sub:
                out.append("</ul></li>")
                in_sub = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{line[2:].strip()}</li>")
    close_all()
    return "".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="プロポーザルmd→ConfEngine入力用JSON")
    ap.add_argument("proposal_md")
    ap.add_argument("output_json")
    args = ap.parse_args()

    src = strip_md(pathlib.Path(args.proposal_md).read_text(encoding="utf-8"))

    title_body = find_section(src, "Title")
    title_lines = [l.strip() for l in title_body.splitlines() if l.strip() and not l.strip().startswith(">")]
    if not title_lines:
        raise SystemExit("エラー: ## Title セクションからタイトルを抽出できない")

    outline_sec = ""
    m = re.search(r"^## (Outline[^\n]*)", src, re.M)
    if m:
        outline_sec = find_section(src, m.group(1))

    refs = find_section(src, "参考文献").split("### スライド付録送り")[0].strip()
    refs_items = [l[2:].strip() for l in refs.splitlines() if l.startswith("- ")]
    outline_body_html = outline_html(outline_sec)
    refs_tag = "h4" if "<h4>" in outline_body_html else "h3"
    refs_html = (
        f"<{refs_tag}>参考文献</{refs_tag}><ul>"
        + "".join(f"<li>{r}</li>" for r in refs_items)
        + "</ul>"
        if refs_items
        else ""
    )

    data = {
        "title": title_lines[0],
        "abstract": paras(find_section(src, "Abstract")),
        "target_audience": find_section(src, "Target Audience"),
        "prerequisites": paras(find_section(src, "Prerequisites for Attendees")),
        "outline": outline_body_html + refs_html,
        "learning_outcome": paras(find_section(src, "Learning Outcome")),
    }

    for key, value in data.items():
        if not value:
            print(f"警告: {key} が空。mdのセクション見出しを確認すること")

    out = pathlib.Path(args.output_json)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"書き出し: {out}")
    for k, v in data.items():
        print(f"  {k}: {len(v)} 文字")


if __name__ == "__main__":
    main()
