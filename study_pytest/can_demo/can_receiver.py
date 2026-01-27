#!/usr/bin/env python3
"""
CAN受信デモスクリプト
使用方法: python3 can_receiver.py
"""

import time
import sys
from can_core import CANReceiver, CANMessage  # can_core.pyから受信クラスをインポート

def message_handler(message: CANMessage):
    """受信メッセージのハンドラー（オプション）"""
    print(f"[ハンドラー] ID=0x{message.actual_id:03X}, Data={message.to_hex_string()}")

def main():
    try:
        # CANReceiverインスタンスを作成（vcan0を使用）
        receiver = CANReceiver(interface='vcan0')
        
        # 接続
        if not receiver.connect():
            print("CAN接続に失敗しました")
            sys.exit(1)
        
        print("CAN受信デモを開始します...")
        print("インターフェース: vcan0")
        print("Ctrl+C で終了")
        
        # メッセージハンドラーを設定（オプション）
        # receiver.set_message_handler(message_handler)
        
        # フィルターを設定（オプション）
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
                
                # 受信統計を表示
                if receiver.get_received_count() % 10 == 0:
                    print(f"  総受信数: {receiver.get_received_count()}")
                
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
    finally:
        try:
            receiver.disconnect()
            print("CANインターフェースをクローズしました")
            print(f"最終受信数: {receiver.get_received_count()}")
        except:
            pass

if __name__ == "__main__":
    main()
