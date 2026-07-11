# 文献調査

書籍・論文の調査を以下のワークフローで進める。

## 指示内容

$ARGUMENTS

## フォルダ構成

成果物は `literature/[書名]/` に保存する。

- PDF は `literature/[書名]/PDFs/` に保存する（`.gitignore` で除外済み）
- `notes.md` に書誌情報・章別PDFリンク・調査メモ・次やることを蓄積する
- 継続調査のときは `notes.md` の「次やること」から再開する
- 書籍でないテーマ調査の場合は、notes.md 形式でなく単一調査ファイルでもよい

## フロー全体像

```
Obsidian/Clippings（起点：文献メモ）
    ↓ 取り出す
literature/[書名]/（作業フォルダ：精読・議論・壁打ち）
    ↓ マージして戻す
Obsidian/Clippings（終点：完成した読書メモ）
```

作業フォルダ内の行ったり来たりは問題なし。調査完了後は `notes.md` の内容を
Obsidian/Clippings の対応ファイルにマージする。

## 調査手順（コストゼロ経路）

0. **引用文献の調査では、検索を始める前に手元の論文PDFの References セクションを読み、
   書誌情報（著者フルネーム・所属・年・タイトル・誌名・巻号）を確定させる**
1. `Obsidian/Documents/Obsidian/Clippings/` を grep して関連 Clipping を探す
2. WebFetch で学術サイトの目次・章URLを取得する
3. `curl -s <URL>` で PDF をダウンロード → `pdftotext` でテキスト変換する
   （取得できたら確認を挟まず変換・中身確認まで進め、何の文献だったかを報告する）
4. `sed -n '行範囲p'` や `grep -n` で必要箇所だけ精読する（全文をコンテキストに読み込まない）

## 調査状態の管理

現在調査中の文献リストは memory（`project_literature.md`）で管理する。
調査の開始・完了時に memory 側を更新する（このファイルには状態を書かない）。
