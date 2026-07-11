# PERMISSIONS.md — 権限とガードレールの3層マップ

CLAUDE.md（毎セッション自動で読み込まれる**指示**）に対し、本ファイルは**機械層に何を設定したか・なぜそうしたかの台帳（記録）**。
権限まわり（`.claude/settings.json` の permissions / hooks）を変更する際は、先に本ファイルを読み、変更と同じ作業の中で本ファイルも更新する。

## 層の定義と使い分け基準

| 層 | 実体 | 保証の強さ | ここに置く基準 |
|---|---|---|---|
| 第1層 ハーネス許可 | `.claude/settings.json` の `permissions.allow` | 機械的・確実 | 常に無条件で許可してよい操作 |
| 第2層 フック強制 | `.claude/settings.json` の `hooks` | 機械的・確実 | 操作は許すが、直前に必ず副作用を挟むもの |
| 第3層 Claudeへの指示 | CLAUDE.md | 判断ベース・確率的 | 文脈判断が必要でルール化しきれないもの |

運用原則：第3層の指示は、可能な限り「義務そのもの」ではなく「機械層への誘導」（例：Editの連打ではなくWriteを使う→フックが発動する）として書く。判断ミスが安全側に倒れる構造にする。

### 記法の注意（2026-07-11 のバグ修正から）

- 絶対パスは `//` で始める。`/` 1つで始まるパターンは「settingsファイルのあるディレクトリからの相対パス」と解釈され、永久にマッチしない
- `*` は1階層のみ（gitignore流マッチで `/` をまたがない）。再帰的に許可するには `**`

## 第1層：ハーネス許可ルール（settings.json の permissions.allow と同期）

| ルール | 理由 |
|---|---|
| `Read / Edit / Write (//Users/katouhiroshi/warumono/claude_prjects/**)` | 作業ディレクトリ全体。CLAUDE.md「配下は自由に読み書き」の機械的実装 |
| `Read(//Users/katouhiroshi/Library/Mobile Documents/iCloud~md~obsidian/**)` | Obsidian ノートの参照用（読みのみ。書き込みは第3層の事前確認ルールに従う） |
| `Bash(python3:*)` | スクリプト実行の頻度が高い |
| `WebFetch(*)` / `WebSearch` | 調査作業で常用 |

注意：Bash 経由のファイル操作（`mv`、`cp`、リダイレクト等）は `Edit/Write` ルールではカバーされない別レール。頻出コマンドの確認が煩わしくなったら `Bash(mv:*)` 等の個別ルール追加か `/fewer-permission-prompts` を検討する。

## 第2層：フック（settings.json の hooks と同期）

| フック | 実体 | 内容 |
|---|---|---|
| Write前バックアップ | `PreToolUse` × `Write` → `.claude/hooks/write_backup.sh` | claude_prjects 配下の **git管理外・既存**ファイルを Write で上書きする直前に `{元ファイル名}_backup.{拡張子}` を同フォルダに自動作成。git追跡済み・新規作成・`_backup` ファイル自体は対象外。既にバックアップがある場合は上書きしない（最初の状態を保持） |

2026-07-11 導入・実発火確認済み。このフックにより、CLAUDE.md のバックアップルールの Write 経路は Claude の判断に依存しない。

**memory は対象外**（2026-07-11 決定）：実体は `~/.claude/projects` 配下で実パスは元々パス判定の対象外。`claude_prjects/memory` シンボリックリンク経由のパスもフック内で明示的に除外している。理由：memory の全面書き換えは整理作業時に限られ、旧内容は会話コンテキストで確認できる。また `_backup` が memory フォルダに紛れると、recall が旧内容を生きた memory として拾う懸念がある。

## 第3層：CLAUDE.md に委ねている判断（一覧）

- パッケージのバージョンが変わる操作の事前確認
- claude_prjects 外への書き込みの事前確認
- git commit/push のスクリプト生成→確認→実行フロー、その他 git 操作の事前確認
- Edit の連続による実質的な全面書き換えの検知（→ Write に切り替えてフックへ誘導）
- セッション終了時の片付け・照合フロー

ここは「破られうる」前提で読む。恒常的に破られる・破られると実害が大きいものは、第1層・第2層への移設を検討する。

## 同期ルール

- `.claude/settings.json`（permissions / hooks）を変更したら、同じ作業の中で本ファイルを更新する
- セッション終了の片付け時に、settings.json と本ファイルの第1層・第2層の一致を照合する（settings.local.json の整理と同時に実施）

本ファイルの照合対象は `.claude/settings.json` のみ。それ以外のセキュリティ対策の記録（サプライチェーン対策等）は `SECURITY_RECORD.md` に置く。
