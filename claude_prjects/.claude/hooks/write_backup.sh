#!/bin/bash
# Write実行前バックアップフック（PreToolUse × Write）
# claude_prjects 配下の git管理外・既存ファイルを Write で上書きする直前に
# {元ファイル名}_backup.{拡張子} を同じフォルダに自動作成する。
# - git追跡済みファイルは対象外（git restore で戻せる）
# - バックアップファイル自体は対象外（_backup の連鎖を防ぐ）
# - 既にバックアップがある場合は上書きしない（最初の状態を保持する）

f=$(jq -r '.tool_input.file_path // empty')
[ -z "$f" ] && exit 0

# 対象は claude_prjects 配下のみ
case "$f" in
  /Users/katouhiroshi/warumono/claude_prjects/*) ;;
  *) exit 0 ;;
esac

# バックアップファイル自体は対象外
case "$f" in
  *_backup | *_backup.*) exit 0 ;;
esac

# 新規作成（既存ファイルなし）は対象外
[ -f "$f" ] || exit 0

# git追跡済みは対象外
git -C "$(dirname "$f")" ls-files --error-unmatch "$f" >/dev/null 2>&1 && exit 0

# バックアップ先: foo.md → foo_backup.md、拡張子なしは foo → foo_backup
ext="${f##*.}"
base="${f%.*}"
if [ "$base" = "$f" ]; then
  b="${f}_backup"
else
  b="${base}_backup.${ext}"
fi

[ -f "$b" ] && exit 0
cp "$f" "$b"
