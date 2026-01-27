#!/usr/bin/env python3
"""
CAN環境のセットアップ確認スクリプト
使用方法: python3 test_setup.py
"""

import sys
import subprocess
import socket

def check_python_version():
    """Python バージョンチェック"""
    print("=== Python バージョンチェック ===")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✓ Python バージョン OK")
        return True
    else:
        print("✗ Python 3.8以上が必要です")
        return False

def check_python_can():
    """python-can モジュールチェック"""
    print("\n=== python-can モジュールチェック ===")
    try:
        import can
        print(f"✓ python-can がインストールされています (version: {can.__version__})")
        return True
    except ImportError:
        print("✗ python-can がインストールされていません")
        print("  インストール: pip3 install python-can")
        return False

def check_can_utils():
    """can-utils チェック"""
    print("\n=== can-utils チェック ===")
    try:
        result = subprocess.run(['cansend', '--help'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ can-utils がインストールされています")
            return True
        else:
            print("✗ can-utils が正しく動作しません")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ can-utils がインストールされていません")
        print("  インストール: sudo apt install can-utils")
        return False

def check_vcan_interface():
    """仮想CANインターフェースチェック"""
    print("\n=== 仮想CANインターフェースチェック ===")
    try:
        result = subprocess.run(['ip', 'link', 'show', 'vcan0'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ vcan0 インターフェースが存在します")
            # 状態もチェック
            if "UP" in result.stdout:
                print("✓ vcan0 インターフェースは有効です")
                return True
            else:
                print("! vcan0 インターフェースが無効です")
                print("  有効化: sudo ip link set up vcan0")
                return False
        else:
            print("✗ vcan0 インターフェースが存在しません")
            print("  作成手順:")
            print("    sudo modprobe vcan")
            print("    sudo ip link add dev vcan0 type vcan")
            print("    sudo ip link set up vcan0")
            return False
    except FileNotFoundError:
        print("✗ ip コマンドが見つかりません")
        return False

def check_can_core():
    """can_core.py ファイルチェック"""
    print("\n=== can_core.py ファイルチェック ===")
    try:
        from can_core import CANSender, CANReceiver
        print("✓ can_core.py が正しくインポートできます")
        print("✓ CANSender, CANReceiver クラスが利用可能です")
        return True
    except ImportError as e:
        print(f"✗ can_core.py のインポートに失敗: {e}")
        print("  can_core.py が同じディレクトリにあることを確認してください")
        return False

def test_can_connection():
    """CAN接続テスト"""
    print("\n=== CAN接続テスト ===")
    try:
        from can_core import CANSender, CANReceiver
        
        # 送信者テスト
        sender = CANSender(interface='vcan0')
        if sender.connect():
            print("✓ CAN送信者の接続成功")
            sender.disconnect()
        else:
            print("✗ CAN送信者の接続失敗")
            return False
        
        # 受信者テスト
        receiver = CANReceiver(interface='vcan0')
        if receiver.connect():
            print("✓ CAN受信者の接続成功")
            receiver.disconnect()
        else:
            print("✗ CAN受信者の接続失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ CAN接続テストに失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("CAN環境セットアップ確認スクリプト")
    print("=" * 50)
    
    checks = [
        check_python_version,
        check_python_can,
        check_can_utils,
        check_vcan_interface,
        check_can_core,
        test_can_connection
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"✗ チェック中にエラー: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("=== セットアップ確認結果 ===")
    
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"✓ 全てのチェックが成功しました ({success_count}/{total_count})")
        print("CAN送受信デモを実行できます！")
        print("\n実行方法:")
        print("  ターミナル1: python3 can_receiver.py")
        print("  ターミナル2: python3 can_sender.py")
    else:
        print(f"✗ {total_count - success_count} 個のチェックが失敗しました ({success_count}/{total_count})")
        print("上記のエラーを解決してから再度実行してください")
        sys.exit(1)

if __name__ == "__main__":
    main()
