#!/bin/bash
# 仮想CANインターフェースのセットアップ（WSL専用版）

# 色付きoutput用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐧 WSL環境で仮想CANインターフェース (vcan0) をセットアップします...${NC}"

# WSL環境確認
if ! grep -qi microsoft /proc/version; then
    echo -e "${YELLOW}⚠️  WSL環境ではない可能性があります${NC}"
    echo -e "${YELLOW}   通常のLinux環境として続行します${NC}"
fi

# 既存のvcan0があれば削除（エラーは無視）
echo -e "${YELLOW}📋 既存のvcan0インターフェースをクリーンアップ中...${NC}"
sudo ip link delete vcan0 2>/dev/null || true

# WSLでのsudo権限確認
echo -e "${YELLOW}🔑 sudo権限を確認中...${NC}"
if ! sudo -n true 2>/dev/null; then
    echo -e "${YELLOW}⚠️  sudoパスワードが必要です${NC}"
fi

# カーネルモジュール確認・読み込み
echo -e "${YELLOW}📦 vcanモジュールを確認・読み込み中...${NC}"
if ! lsmod | grep -q "^vcan "; then
    if ! sudo modprobe vcan; then
        echo -e "${RED}❌ vcanモジュールの読み込みに失敗しました${NC}"
        echo -e "${YELLOW}💡 WSLでは以下を試してください:${NC}"
        echo "   1. WSL2を使用していることを確認"
        echo "   2. Windows側で: wsl --update"
        echo "   3. WSL再起動: wsl --shutdown && wsl"
        exit 1
    fi
else
    echo -e "${GREEN}✅ vcanモジュールは既に読み込まれています${NC}"
fi

# 仮想CANインターフェースを作成
echo -e "${YELLOW}🔗 vcan0インターフェースを作成中...${NC}"
if ! sudo ip link add dev vcan0 type vcan; then
    echo -e "${RED}❌ vcan0の作成に失敗しました${NC}"
    echo -e "${YELLOW}💡 以下を確認してください:${NC}"
    echo "   - WSL2を使用していますか？"
    echo "   - カーネルバージョン: $(uname -r)"
    exit 1
fi

# インターフェースを有効化
echo -e "${YELLOW}⚡ vcan0インターフェースを有効化中...${NC}"
if ! sudo ip link set up vcan0; then
    echo -e "${RED}❌ vcan0の有効化に失敗しました${NC}"
    sudo ip link delete vcan0 2>/dev/null
    exit 1
fi

# 確認
echo -e "${GREEN}✅ セットアップ完了！${NC}"
echo ""
echo -e "${BLUE}📡 利用可能なCANインターフェース:${NC}"
ip link show type can

# WSL環境情報表示
echo ""
echo -e "${BLUE}🐧 WSL環境情報:${NC}"
echo "  カーネル: $(uname -r)"
echo "  ディストリビューション: $(lsb_release -d -s 2>/dev/null || echo "不明")"
echo "  WSLバージョン: $(cat /proc/version | grep -o 'Microsoft.*' || echo "WSL1")"

echo ""
echo -e "${BLUE}🧪 python-canライブラリの動作確認:${NC}"
if command -v python3 &> /dev/null; then
    python3 -c "
import sys
print(f'Python: {sys.version}')
try:
    import can
    print('✅ python-can: 利用可能')
    try:
        bus = can.Bus(channel='vcan0', bustype='socketcan')
        print('✅ vcan0接続: 成功')
        bus.shutdown()
    except Exception as e:
        print(f'❌ vcan0接続: {e}')
        print('💡 仮想環境が有効化されていることを確認してください')
except ImportError:
    print('❌ python-can: 未インストール')
    print('   以下のコマンドでインストール:')
    print('   source .venv/bin/activate')
    print('   pip install python-can')
" 2>/dev/null || echo -e "${YELLOW}⚠️  Python環境の確認をスキップしました${NC}"
fi

echo ""
echo -e "${GREEN}🚀 WSLでの使用方法:${NC}"
echo ""
echo -e "${BLUE}1. 仮想環境有効化:${NC}"
echo "   source .venv/bin/activate"
echo ""
echo -e "${BLUE}2. テスト実行:${NC}"
echo "   # 単体テスト"
echo "   python -m pytest test_can_sender.py test_can_receiver.py -v"
echo ""
echo "   # 統合テスト"  
echo "   python -m pytest test_integration.py -v -s"
echo ""
echo -e "${BLUE}3. 手動テスト（2つのターミナル）:${NC}"
echo "   ターミナル1: python -c \"from can_core import *; r=CANReceiver('vcan0'); r.connect(); print('受信待機:', r.receive_once())\""
echo "   ターミナル2: python -c \"from can_core import *; s=CANSender('vcan0'); s.connect(); s.send(0x123, b'Hello WSL')\""

echo ""
echo -e "${YELLOW}💡 WSL特有の注意事項:${NC}"
echo "  • WSL2推奨（WSL1ではCANサポートが制限される可能性）"
echo "  • Windowsファイアウォールが無効化されている必要はありません"
echo "  • Windowsとファイルを共有: /mnt/c/Users/..."
echo "  • WSL再起動: wsl --shutdown && wsl"

echo ""
echo -e "${YELLOW}🔧 トラブルシューティング:${NC}"
echo -e "${YELLOW}  問題: vcan module not found${NC}"
echo "    WSLバージョン確認: wsl -l -v"
echo "    WSL2に更新: wsl --set-version Ubuntu 2"
echo ""
echo -e "${YELLOW}  問題: permission denied${NC}"  
echo "    sudoersに追加: sudo usermod -aG sudo \$USER"
echo "    WSL再起動後に再試行"
echo ""
echo -e "${YELLOW}  問題: python-can import error${NC}"
echo "    仮想環境確認: source .venv/bin/activate"
echo "    再インストール: pip install --upgrade python-can"

echo ""
echo -e "${YELLOW}💡 終了時のクリーンアップ:${NC}"
echo "  sudo ip link delete vcan0"
echo "  または: bash cleanup_vcan.sh"