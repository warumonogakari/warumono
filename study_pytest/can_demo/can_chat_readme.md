# CAN Chat GUI アプリケーション

tkinter + ttk.Treeview を使用したCAN通信チャットアプリケーション

## 概要

- **目的**: 2つのターミナルでCAN送受信を行うGUIチャットアプリ
- **表示形式**: TIMESTAMP, ID, DATA の列表示
- **入力**: 1行テキスト入力（CAN ID + データ）
- **開発手法**: TDD (Test-Driven Development)
- **対応環境**: Ubuntu 22.04, Windows 10/11, Python 3.8

## ファイル構成

```
can_chat_project/
├── can_core.py                   # CAN通信コアクラス（Linux用）
├── can_chat_gui.py               # Linux版GUIアプリケーション
├── test_can_chat_gui.py          # Linux版テスト
├── test_windows_basic.py           # Windows基本環境テスト
├── run_can_chat.sh               # Linux実行スクリプト
└── can_chat_readme.md                     # このファイル
```

## 対応環境

### 🐧 Linux環境（Ubuntu 22.04）
- **CAN通信**: 実機CAN / vcan0仮想インターフェース
- **GUI**: ネイティブtkinterスタイル
- **テスト**: 実CAN通信を含む完全テスト

### 🖥️ Windows環境（Windows 10/11）
- **CAN通信**: Mockモード（シミュレーション）
- **GUI**: Windows最適化デザイン
- **テスト**: GUI機能特化テスト

## 事前準備

### 1. 必要なパッケージのインストール
```bash
# システムパッケージ
sudo apt update
sudo apt install python3-tk can-utils

# Pythonパッケージ
pip3 install python-can pytest
```

### 2. 仮想CANインターフェースの作成
```bash
sudo modprobe can
sudo modprobe can_raw
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

### 3. インストール確認
```bash
# Python環境確認
python3 -c "import tkinter, can; print('OK')"

# vcan0確認
ip link show vcan0
```

## 使用方法

### 自動実行（推奨）
```bash
# 実行スクリプトを使用
bash run_can_chat.sh
```

### 手動実行

#### ターミナル1: 受信者
```bash
python3 can_chat_gui.py receiver
```

#### ターミナル2: 送信者
```bash
python3 can_chat_gui.py sender
```

## 機能説明

### 共通機能
- **メッセージ表示**: Treeviewで一覧表示（TIMESTAMP, ID, DATA）
- **リアルタイム表示**: 送受信メッセージの即座反映
- **自動スクロール**: 新しいメッセージに自動追従
- **データ形式サポート**: 16進数、ASCII、日本語対応

### 送信者モード
- **CAN ID入力**: 16進数（0x123）または10進数（291）
- **データ入力**: 以下の形式をサポート
  - 16進数: `0x01020304` または `01 02 03 04`
  - ASCII文字列: `Hello World`
  - 日本語: `こんにちは`（Windows版）
- **送信ボタン**: メッセージ送信
- **Enter キー**: データ入力フィールドでEnterキーを押すと送信

### 受信者モード
- **メッセージ受信**: リアルタイム表示
- **送信機能無効**: 受信専用モード
- **統計表示**: 受信メッセージ数の表示

### 表示フォーマット
- **TIMESTAMP**: `HH:MM:SS.mmm` 形式
- **ID**: `0xXXX` 16進数表示
- **DATA**: `01 02 03 04 (ASCII)` 形式
  - 16進数バイト表示
  - 表示可能ASCII文字は括弧内に表示
  - 送信メッセージには `[SENT]` マーク

### 🖥️ Windows版追加機能
- **絵文字アイコン**: 視覚的に分かりやすいUI
- **日本語フォント**: システム最適フォントの自動選択
- **DPI対応**: 高解像度ディスプレイ対応
- **Mock通信**: CAN通信のシミュレーション
- **ネイティブスタイル**: Windows 10/11ライクなデザイン

## TDD テスト実行

### 🐧 Linux環境

#### 全テスト実行
```bash
# pytest使用（推奨）
python3 -m pytest test_can_chat_gui.py -v

# または個別実行
python3 test_can_chat_gui.py
```

#### 特定テストクラス実行
```bash
# GUI コンポーネントテストのみ
python3 -m pytest test_can_chat_gui.py::TestGUIComponents -v

# メッセージユーティリティテストのみ
python3 -m pytest test_can_message_utils.py::TestCANMessageUtils -v
```

### 🖥️ Windows環境

#### 環境テスト
```cmd
# 基本環境テスト
python test_windows_gui.py