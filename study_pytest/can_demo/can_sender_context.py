#!/usr/bin/env python3
"""
CAN送信デモスクリプト（コンテキストマネージャー版）
使用方法: python3 can_sender_context.py
"""

import time
import sys
from can_core import CANSenderContext

def main():
    try:
        # with文を使用してCAN送信者を作成（自動的に接続・切断）
        with CANSenderContext(interface='vcan0') as sender:
            print("CAN送信デモを開始します...")
            print("インターフェース: vcan0")
            print("Ctrl+C で終了")
            
            message_id = 0x123
            counter = 0
            
            while True:
                # メッセージデータを作成
                data = bytes([
                    0x01,  # 固定データ
                    0x02,
                    counter & 0xFF,  # カウンター値（下位バイト）
                    (counter >> 8) & 0xFF,  # カウンター値（上位バイト）
                    0x05,
                    0x06,
                    0x07,
                    0x08
                ])
                
                # CANメッセージを送信
                success = sender.send(message_id, data)
                
                if success:
                    print(f"送信: ID=0x{message_id:03X}, Data={data.hex().upper()}, Counter={counter}")
                else:
                    print(f"送信失敗: ID=0x{message_id:03X}")
                
                counter += 1
                if counter > 0xFFFF:
                    counter = 0
                    
                time.sleep(1)  # 1秒間隔で送信
                
    except KeyboardInterrupt:
        print("\n送信を停止します...")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)
    # withブロックを抜ける時に自動的に接続が切断される

if __name__ == "__main__":
    main()
