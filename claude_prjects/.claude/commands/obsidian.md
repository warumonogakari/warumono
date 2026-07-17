# Obsidian への保管

指定されたファイル・コンテンツを Obsidian vault に保管する。

## 指示内容

$ARGUMENTS

## vault の構成（2026-07-17 確認）

- `claude_prjects/Obsidian` は**シンボリックリンク** → 実体は
  `~/Library/Mobile Documents/iCloud~md~obsidian`（iCloud Drive の Obsidian 領域）。
  書き込んだファイルは他デバイスにも同期される
- ノート本体は `Obsidian/Documents/Obsidian/` 配下：
  - `Clippings/` — Webクリップ・文字起こし・記事メモの保管場所。**デフォルトの保管先**
  - `Attachments/` — 添付ファイル（画像等）
- vault root 直下や `Documents/` 直下には置かない（迷子になる）

## 進め方

1. 保管対象を特定する（指示になければ直近の作業対象を確認する）
2. YAML フロントマターを先頭に付ける：

   ```yaml
   ---
   title: <ノートのタイトル>
   source: <出典URL。ローカル生成物なら省略可>
   date: <コンテンツの日付（公開日等）。YYYY-MM-DD>
   tags: [<内容に応じたタグ、ケバブケース英語>]
   ---
   ```

3. `Obsidian/Documents/Obsidian/Clippings/` に保存する。
   ファイル名は日本語可、内容がわかる名前にする
4. 元ファイルが作業フォルダ（`tech_research/` 等）に残る場合は、
   二重管理になることを指摘し、元を消すか残すか Hiroshi さんに確認する

## 注意

- サンドボックスの `find` はシンボリックリンク先（`~/Library/Mobile Documents`）に
  入れないことがある。中身の確認は `ls` を使う
- 書き込みは `claude_prjects/Obsidian/...` パス経由でよい（物理的には iCloud だが了承済み）

## 発動条件

「Obsidianに保管して」「Obsidianに入れて」等、自然文で求められた場合も
このコマンドの手順に従う。
