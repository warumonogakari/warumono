#!/bin/sh
# crit のレビュー画面を開くブラウザ。Firefox はガタークリック不具合のため Safari を使う
# （経緯は tech_research/crit.md調査とインストール改善記録.md。~/.crit.config.json の open_cmd から参照）
exec open -a Safari "$1"
