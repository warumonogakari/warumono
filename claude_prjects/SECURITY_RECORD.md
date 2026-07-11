# SECURITY_RECORD.md — セキュリティ対策の記録

実施済みのセキュリティ対策の記録（台帳）。行動ルールは CLAUDE.md「セキュリティ方針」、Claude Code の権限設定は PERMISSIONS.md を参照。

## サプライチェーン攻撃対策

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
