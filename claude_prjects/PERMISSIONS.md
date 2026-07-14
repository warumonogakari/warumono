# PERMISSIONS.md — 権限とガードレールの3層マップ

CLAUDE.md（毎セッション自動で読み込まれる**指示**）に対し、本ファイルは**機械層に何を設定したか・なぜそうしたかの台帳（記録）**。
権限まわり（プロジェクト `.claude/settings.json` またはユーザーグローバル `~/.claude/settings.json` の permissions / hooks）を変更する際は、先に本ファイルを読み、変更と同じ作業の中で本ファイルも更新する。

## settings.json の正準配置（2026-07-14 Hiroshi 決定）

`settings.json`（`settings.local.json` を除く）は以下の**2箇所のみ**に置く。これ以外の場所に settings.json を新規作成しない。

1. `~/.claude/settings.json` — ユーザーグローバル（起動場所に依存しない許可・deny）
2. `claude_prjects/.claude/settings.json` — プロジェクト（第1層 allow ＋ 第2層フック）

`settings.local.json` はサブフォルダ起動のたびにハーネスが生成する使い捨て断片であり、この管理の対象外（片付けフローで整理）。なお「既知の構造的問題」の対処選択肢 (c)（サブフォルダへの settings.json 複製）はこの決定により**不採用が確定**。

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

### ユーザーグローバル層（`~/.claude/settings.json` の permissions.allow と同期）

| ルール | 理由（2026-07-12 追加） |
|---|---|
| `Read(//Users/katouhiroshi/.claude/projects/-Users-katouhiroshi-warumono/memory/**)` | memory ファイルの読み取り。プロジェクト設定は**起動ディレクトリの `.claude/` からしか読まれない**ため、サブフォルダ起動セッションでは本ファイル記載の第1層が効かず、memory 読み取りの許可ダイアログが発生する。その際「常に許可」を選ぶとホーム全域 `Read(//Users/katouhiroshi/**)` のような過大な許可が生成される事故が実際に起きた（2026-07-12、当該許可は発見後に削除済み）。起動場所に依存しないユーザーグローバルに、memory ディレクトリ限定の狭い許可を置くことで再発を防止する |

**deny ルール**（`~/.claude/settings.json` の permissions.deny と同期、2026-07-14 追加）

| ルール | 理由 |
|---|---|
| `Read(.env)` / `Read(.env.*)` | 環境変数ファイル（APIキー・パスワード等）の読み取り防止 |
| `Read(**/.ssh/**)` | SSH秘密鍵の読み取り防止 |
| `Bash(sudo:*)` | 管理者権限での誤った実行防止 |

deny はサブフォルダ起動問題（下記）の影響を受けない起動場所非依存のガードとして、プロジェクト設定ではなくユーザーグローバルに置く。**限界も記録しておく**：Read の deny は Read ツールを塞ぐだけで、Bash 経由の `cat .env` 等は別レール（塞ぐなら sandbox の `filesystem.denyRead` が必要）。

### 既知の構造的問題（2026-07-12 発見・未対処）

**`claude_prjects` のサブフォルダから起動したセッションには、上記第1層・第2層が一切適用されない**（設定は起動ディレクトリの `.claude/` から読まれ、親ディレクトリへ遡らない）。今回のブログ作業（`blogs/スクフェス三河プロポーザルフィードバック/` 起動）で実証：Obsidian・WebFetch とも許可済みのはずがプロンプトが発生し、サブフォルダの `settings.local.json` に重複エントリが生成された。**Write前バックアップフック（第2層）も同様に効いていない**点は特に注意。対処の選択肢：(a) 常に `claude_prjects` 直下から起動する運用に統一、(b) 第1層・第2層をユーザーグローバルへ移設、(c) サブフォルダにも settings.json を複製。**当面 (a) を採用（2026-07-12 Hiroshi 決定）**——`claude` はサブフォルダでなく `claude_prjects` 直下で起動する。運用で破られうる（第3層相当の弱さ）ため、サブフォルダ起動が繰り返し起きるようなら (b) への移行を再検討する。

**2026-07-14 照合時の実態**：サブフォルダの `settings.local.json` が9箇所に散在していることを確認（`blogs/`、`blogs/スクフェス三河プロポーザルフィードバック/`、`literature/`、`literature/Russia-Ukraine_War/`、`hotel/`、`hotel/results/`、`slides/`、`slides/2026年スクフェス三河/`、`.claude/.claude/`）。運用 (a) 決定より前の蓄積を含むが、サブフォルダ起動が常態化していた証拠。特に過大許可の実例：`hotel/` に `Read(//Users/katouhiroshi/.claude/**)`（credentials を含む `~/.claude` 全域の読み許可）、`.claude/.claude/` に `Bash(git:*)`（CLAUDE.md の git 確認フローを素通しする全 git 許可）——**この2エントリは同日 Hiroshi 確認のうえ削除済み**。残る9ファイル自体の整理は片付け時に実施する。

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

- プロジェクト `.claude/settings.json` またはユーザーグローバル `~/.claude/settings.json`（permissions / hooks）を変更したら、同じ作業の中で本ファイルを更新する
- セッション終了の片付け時に、両 settings.json と本ファイルの第1層・第2層・ユーザーグローバル層の一致を照合する（settings.local.json の整理と同時に実施）
- 同じ片付け時に、settings.json が正準配置の2箇所以外に増えていないかを確認する：
  `find ~/warumono/claude_prjects ~/.claude -maxdepth 6 -name "settings.json" -not -path "*/node_modules/*"`
  → 出力が2行（正準配置と一致）でなければ乱立として報告し、Hiroshi 確認のうえ整理する

本ファイルの照合対象は上記2ファイルのみ。`settings.local.json`（プロジェクト直下・サブフォルダとも）は使い捨ての許可断片として片付けフローで整理する対象であり、台帳には載せない。それ以外のセキュリティ対策の記録（サプライチェーン対策等）は `SECURITY_RECORD.md` に置く。
