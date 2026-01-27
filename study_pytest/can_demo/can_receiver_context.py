#!/usr/bin/env python3
"""
CAN受信デモスクリプト（コンテキストマネージャー版）
使用方法: python3 can_receiver_context.py
"""

import time
import sys
from can_core import CANReceiverContext

def main():
    try:
        # with文を使用してCAN受信者を作成（自動的に接続・切断）
        with CANReceiverContext(interface='vcan0') as receiver:
            print("CAN受信デモを開始します...")
            print("インターフェース: vcan0")
            print("Ctrl+C で終了")
            
            # オプション: フィルターを設定
            # receiver.add_id_filter(0x120, 0x130)  # ID範囲フィルター
            
            timeout_counter = 0
            
            while True:
                # CANメッセージを受信
                message = receiver.receive_once(timeout=1.0)
                
                if message is not None:
                    # メッセージを表示
                    print(f"受信: ID=0x{message.actual_id:03X}, "
                          f"DLC={message.dlc}, "
                          f"Data={message.to_hex_string()}, "
                          f"ASCII={message.to_ascii_string()}, "
                          f"Timestamp={message.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
                    
                    # 特定のIDの場合、詳細な解析を行う
                    if message.actual_id == 0x123:
                        if len(message.data) >= 4:
                            counter = message.data[2] + (message.data[3] << 8)
                            print(f"  -> Counter値: {counter}")
                    
                    timeout_counter = 0
                            
                else:
                    # タイムアウト時の処理
                    timeout_counter += 1
                    if timeout_counter % 5 == 0:
                        print(f"待機中... (総受信数: {receiver.get_received_count()})")
                    
    except KeyboardInterrupt:
        print("\n受信を停止します...")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)
    # withブロックを抜ける時に自動的に接続が切断される

if __name__ == "__main__":
    main()
