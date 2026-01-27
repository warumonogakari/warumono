#!/usr/bin/env python3
"""
CAN送信デモスクリプト
使用方法: python3 can_sender.py
"""

import time
import sys
from can_core import CANSender, CANMessage  # can_core.pyから送信クラスをインポート

def main():
    try:
        # CANSenderインスタンスを作成（vcan0を使用）
        sender = CANSender(interface='vcan0')
        
        # 接続
        if not sender.connect():
            print("CAN接続に失敗しました")
            sys.exit(1)
        
        print("CAN送信デモを開始します...")
        print("インターフェース: vcan0")
        print("Ctrl+C で終了")
        
        message_id = 0x123
        counter = 0
        
        while True:
            # メッセージデータを作成（bytesで作成）
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
                
                # 送信統計を表示
                if counter % 10 == 0:
                    print(f"  総送信数: {sender.get_sent_count()}")
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
    finally:
        try:
            sender.disconnect()
            print("CANインターフェースをクローズしました")
        except:
            pass

if __name__ == "__main__":
    main()
