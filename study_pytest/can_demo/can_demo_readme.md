# CAN送受信デモ

## 前提条件
- Ubuntu 24.04
- Python 3.8
- インターネット接続（パッケージインストール用）

## 事前準備（セットアップ）

### 1. システムパッケージの更新とcan-utilsのインストール
```bash
# パッケージリストを更新
sudo apt update

# CAN関連のユーティリティをインストール
sudo apt install -y can-utils

# Pythonの開発ツールをインストール（pipが古い場合のため）
sudo apt install -y python3-pip python3-dev
```

### 2. Pythonモジュールのインストール
```bash
# pip を最新に更新
python3 -m pip install --upgrade pip

# python-can ライブラリをインストール
pip3 install python-can

# 依存関係も確認
pip3 list | grep -E "(can|python-can)"
```

### 3. インストール確認
```bash
# python-canが正しくインストールされているか確認
python3 -c "import can; print('python-can version:', can.__version__)"

# can-utilsが正しくインストールされているか確認
candump --help | head -5
```

### 4. 仮想CANインターフェースの作成と設定
```bash
# vcanモジュールをロード
sudo modprobe vcan

# 仮想CANインターフェース vcan0 を作成
sudo ip link add dev vcan0 type vcan

# インターフェースを有効化
sudo ip link set up vcan0

# 作成されたインターフェースを確認
ip link show vcan0

# 正常に作成されている場合、以下のような出力が表示される：
# 3: vcan0: <NOARP,UP,LOWER_UP> mtu 72 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
#     link/can
```

### 5. 権限設定（必要に応じて）
```bash
# ユーザーをdialoutグループに追加（実機CAN使用時に必要な場合がある）
sudo usermod -a -G dialout $USER

# グループ変更を反映するために一度ログアウト・ログイン
# または新しいターミナルを開く
```

## ファイル構成
プロジェクトディレクトリに以下のファイルを配置：
```
can_demo/
├── can_core.py              # 送信・受信クラス（既存）
├── can_sender.py            # 送信用スクリプト
├── can_receiver.py          # 受信用スクリプト
├── can_sender_context.py    # コンテキストマネージャー版送信スクリプト
├── can_receiver_context.py  # コンテキストマネージャー版受信スクリプト
└── README.md                # このファイル
```

## 完全なセットアップ手順

### 方法1: 自動セットアップ（最も簡単）
```bash
# 1. セットアップスクリプトを実行
bash setup_can_demo.sh

# 2. デモ実行
# ターミナル1
python3 can_receiver_context.py

# ターミナル2  
python3 can_sender_context.py
```

### 方法2: 手動セットアップ
```bash
# 1. 事前準備（上記の手順1-5を実行）
# 2. セットアップ確認
python3 test_setup.py

# 3. デモ実行
# ターミナル1
python3 can_receiver.py

# ターミナル2
python3 can_sender.py
```

## 動作確認

### can-utilsでの確認
別のターミナルで以下を実行すると、CANメッセージを監視できます：
```bash
candump vcan0
```

### 手動でのメッセージ送信テスト
```bash
cansend vcan0 123#0102030405060708
```

## トラブルシューティング

### 仮想CANインターフェースが見つからない場合
```bash
# インターフェースを確認
ip link show

# 再作成
sudo ip link delete vcan0
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

### 権限エラーが発生する場合
```bash
# ユーザーをdialoutグループに追加
sudo usermod -a -G dialout $USER

# 再ログインが必要
```

## 注意事項

- 実際のCANハードウェアを使用する場合は、can_core.pyのインターフェース設定を変更してください
- 送信間隔やメッセージ内容は用途に応じて調整してください
- Ctrl+C で各プログラムを停止できます

## カスタマイズ例

### 送信間隔の変更
can_sender.py の `time.sleep(1)` を変更

### メッセージIDの変更
`message_id = 0x123` を別の値に変更

### データ内容の変更
`data` リストの内容を変更
