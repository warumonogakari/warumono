# CLAUDE.md

Claude Code（claude.ai/code）がこのリポジトリで作業する際のガイドライン。

## 言語

コメント・ドキュメントは日本語で記述する。

## 呼び名

- ユーザーは **Hiroshi さん**
- Claude Code は **Claude さん**

## セッション終了フロー

- Hiroshiさんが「終わり」「クリアして」などセッション終了を示すキーワードを言ったら、Claudeは中間生成物の片付けを確認する
- 削除対象をリストアップしてHiroshiさんの確認を取ってから削除し、その後 `/clear` を促す
- Hiroshiさんが直接 `/clear` を打った場合は確認不要でリセット（片付け不要の意思表示として扱う）
- Hiroshiさんが片付けを先に「片付けて」と言ってきた場合はそのまま対応する

### settings.local.json の整理（片付け時に実施）

- `settings.local.json` の現在の内容を確認し、ベースライン（`settings.json` で許可済みのものや明らかに不要な断片）と比較する
- 新たに追加されたパーミッションをHiroshiさんに提示し、残す/削除を確認してから整理する

## 作業権限

| 操作 | 方針 |
|---|---|
| `/Users/katouhiroshi/warumono/claude_prjects/` 配下のファイル読み書き | 自由に実行してよい |
| それ以外のディレクトリへの書き込み | 必ず確認してから実行する |
| パッケージのバージョンが変わる操作（`uv pip install <pkg>`、`uv add`、`npm install <pkg>`、`brew upgrade` 等） | 必ず確認してから実行する |
| lock fileに基づく再現インストール（`uv sync`、`npm ci` 等） | 自由に実行してよい |
| git操作（add / commit / push / rebase 等） | 必ず確認してから実行する |
| `/zenndev` による zenn.dev への投稿 | コマンド自体が投稿の意思表示なので追加確認不要 |

## File Placement

ファイルは原則 `/Users/katouhiroshi/warumono/claude_prjects/` に置く。
`~/.claude/projects/` には Claude Code が必須とするファイル（memory ファイルなど）のみ置く。

## Memory → Skill 移行ルール

memoryファイルの内容が手順の羅列になり、3セッション以上変更なく使われた場合、Claudeはskillへの移行を提案する。
移行後は対応するmemoryファイルを削除して二重管理を防ぐ。

## セキュリティ方針（サプライチェーン攻撃対策）

2026-04-01 に確認・方針を策定。参考記事: https://zenn.dev/dely_jp/articles/supply-chain-kowai

### 管理対象パッケージ

| 場所 | パッケージマネージャ | 主なパッケージ |
|---|---|---|
| `claude_prjects/` | uv (Python) | pdf2image, pillow, playwright |
| `warumono/` | npm | zenn-cli |

### 対策状況

| 対策 | 状態 | 備考 |
|---|---|---|
| `uv.lock` をコミット | ✅ 対応済み | `claude_prjects/` にあり |
| `package-lock.json` をコミット | ✅ 対応済み | `warumono/` にあり |
| npm クールダウン（`min-release-age=7`） | ✅ 対応済み・動作確認済み | `~/.npmrc` に設定済み（マシン全体に適用）。内部では `before` キーに変換されて機能するため `npm config get min-release-age` は `null` を返すが正常。`npm config list` で `before` の日付を確認できる。 |
| uv クールダウン（`exclude-newer = "1 week"`） | ✅ 対応済み | `pyproject.toml` に設定済み |
| 依存パッケージの更新は慎重に | ✅ 方針あり | 公開後1週間は様子見を推奨 |

### 今後の方針

- 依存パッケージをアップデートする際は、公開から **1週間以上**経過したバージョンを選ぶ
- lock file は必ずコミットに含める
- GitHub Actions を使う場合は、タグではなく **コミットハッシュで固定**（SHA pinning）する
