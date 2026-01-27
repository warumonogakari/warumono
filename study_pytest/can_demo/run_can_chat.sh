#!/bin/bash
# CAN Chat GUI アプリケーション実行スクリプト
# 使用方法: bash run_can_chat.sh

echo "CAN Chat GUI アプリケーション"
echo "============================"
echo ""

# 仮想CANインターフェースの確認
if ! ip link show vcan0 &> /dev/null; then
    echo "vcan0 インターフェースが見つかりません。作成します..."
    sudo modprobe can
    sudo modprobe can_raw
    sudo modprobe vcan
    sudo ip link add dev vcan0 type vcan
    sudo ip link set up vcan0
    echo "vcan0 インターフェースを作成しました。"
    echo ""
fi

# Python環境の確認
echo "Python環境確認中..."
if ! python3 -c "import tkinter, can" &> /dev/null; then
    echo "❌ 必要なモジュールがインストールされていません。"
    echo "以下のコマンドでインストールしてください："
    echo "pip3 install python-can"
    echo "sudo apt install python3-tk  # tkinterが無い場合"
    exit 1
fi

echo "✅ Python環境 OK"
echo ""

# ファイルの存在確認
required_files=("can_core.py" "can_chat_gui.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 必要ファイルが見つかりません: $file"
        exit 1
    fi
done

echo "✅ 必要ファイル OK"
echo ""

# メニュー表示
echo "実行モードを選択してください："
echo "1) 送信者 (Sender)"
echo "2) 受信者 (Receiver)"
echo "3) 両方起動 (送信者と受信者を別ターミナルで)"
echo "4) テスト実行"
echo "5) 終了"
echo ""

read -p "選択 (1-5): " choice

case $choice in
    1)
        echo "送信者モードで起動中..."
        python3 can_chat_gui.py sender
        ;;
    2)
        echo "受信者モードで起動中..."
        python3 can_chat_gui.py receiver
        ;;
    3)
        echo "送信者と受信者を別ターミナルで起動します..."
        echo ""
        echo "1. まず受信者を起動します（このターミナル）"
        echo "2. 別ターミナルで以下を実行してください："
        echo "   python3 can_chat_gui.py sender"
        echo ""
        read -p "受信者を起動しますか? (y/n): " start_receiver
        if [ "$start_receiver" = "y" ] || [ "$start_receiver" = "Y" ]; then
            python3 can_chat_gui.py receiver
        fi
        ;;
    4)
        echo "テストを実行中..."
        python3 test_can_chat_gui.py
        ;;
    5)
        echo "終了します。"
        exit 0
        ;;
    *)
        echo "無効な選択です。"
        exit 1
        ;;
esac