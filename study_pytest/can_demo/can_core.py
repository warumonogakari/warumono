#!/usr/bin/env python3
"""
CAN通信のコアクラス（テスト可能な設計）
"""

import socket
import struct
import time
from dataclasses import dataclass
from typing import Optional, Callable, List
from datetime import datetime

@dataclass
class CANMessage:
    """CANメッセージを表すデータクラス"""
    can_id: int
    data: bytes
    is_extended: bool = False
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def actual_id(self) -> int:
        """実際のCAN ID（フラグを除いた値）"""
        return self.can_id & 0x7FFFFFFF
    
    @property
    def dlc(self) -> int:
        """データ長"""
        return len(self.data)
    
    def to_hex_string(self) -> str:
        """データを16進文字列で表現"""
        return ' '.join(f'{b:02X}' for b in self.data)
    
    def to_ascii_string(self) -> str:
        """データをASCII文字列で表現（表示可能文字のみ）"""
        return ''.join(chr(b) if 32 <= b <= 126 else '.' for b in self.data)

class CANInterface:
    """CAN通信インターフェースの抽象化"""
    
    def __init__(self, interface: str = 'vcan0'):
        self.interface = interface
        self.socket = None
        self._is_connected = False
    
    def connect(self) -> bool:
        """CANインターフェースに接続"""
        try:
            self.socket = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
            self.socket.bind((self.interface,))
            self._is_connected = True
            return True
        except OSError as e:
            self._is_connected = False
            raise ConnectionError(f"CAN接続エラー: {e}")
    
    def disconnect(self):
        """接続を閉じる"""
        if self.socket:
            self.socket.close()
        self._is_connected = False
    
    def is_connected(self) -> bool:
        """接続状態を確認"""
        return self._is_connected
    
    def send_message(self, message: CANMessage) -> bool:
        """CANメッセージを送信"""
        if not self._is_connected:
            raise ConnectionError("CAN未接続")
        
        try:
            can_id = message.can_id
            if message.is_extended:
                can_id |= 0x80000000
            
            # データの長さ制限
            data = message.data[:8]
            
            # CANフレーム作成
            can_frame = struct.pack('<IB3x8s', can_id, len(data), data.ljust(8, b'\x00'))
            self.socket.send(can_frame)
            return True
            
        except Exception as e:
            raise RuntimeError(f"送信エラー: {e}")
    
    def receive_message(self, timeout: float = 1.0) -> Optional[CANMessage]:
        """CANメッセージを受信"""
        if not self._is_connected:
            raise ConnectionError("CAN未接続")
        
        try:
            self.socket.settimeout(timeout)
            can_frame = self.socket.recv(16)
            
            # フレーム解析
            can_id, length, data = struct.unpack('<IB3x8s', can_frame)
            
            # 拡張フレームチェック
            is_extended = bool(can_id & 0x80000000)
            actual_id = can_id & 0x7FFFFFFF if is_extended else can_id & 0x7FF
            
            return CANMessage(
                can_id=actual_id,
                data=data[:length],
                is_extended=is_extended,
                timestamp=datetime.now()
            )
            
        except socket.timeout:
            return None
        except Exception as e:
            raise RuntimeError(f"受信エラー: {e}")

class CANSender:
    """CAN送信クラス"""
    
    def __init__(self, interface: str = 'vcan0'):
        self.can_interface = CANInterface(interface)
        self.sent_messages: List[CANMessage] = []
    
    def connect(self) -> bool:
        """接続"""
        return self.can_interface.connect()
    
    def disconnect(self):
        """切断"""
        self.can_interface.disconnect()
    
    def send(self, can_id: int, data: bytes, is_extended: bool = False) -> bool:
        """メッセージ送信"""
        message = CANMessage(can_id, data, is_extended)
        success = self.can_interface.send_message(message)
        if success:
            self.sent_messages.append(message)
        return success
    
    def get_sent_count(self) -> int:
        """送信メッセージ数を取得"""
        return len(self.sent_messages)
    
    def get_last_sent_message(self) -> Optional[CANMessage]:
        """最後に送信したメッセージを取得"""
        return self.sent_messages[-1] if self.sent_messages else None

class CANReceiver:
    """CAN受信クラス"""
    
    def __init__(self, interface: str = 'vcan0'):
        self.can_interface = CANInterface(interface)
        self.received_messages: List[CANMessage] = []
        self.message_handler: Optional[Callable[[CANMessage], None]] = None
    
    def connect(self) -> bool:
        """接続"""
        return self.can_interface.connect()
    
    def disconnect(self):
        """切断"""
        self.can_interface.disconnect()
    
    def set_message_handler(self, handler: Callable[[CANMessage], None]):
        """メッセージハンドラーを設定"""
        self.message_handler = handler
    
    def receive_once(self, timeout: float = 1.0) -> Optional[CANMessage]:
        """1つのメッセージを受信"""
        message = self.can_interface.receive_message(timeout)
        if message:
            self.received_messages.append(message)
            if self.message_handler:
                self.message_handler(message)
        return message
    
    def receive_loop(self, duration: float = 10.0, message_limit: int = 100):
        """指定時間または指定数のメッセージを受信"""
        start_time = time.time()
        
        while (time.time() - start_time) < duration and len(self.received_messages) < message_limit:
            message = self.receive_once(timeout=0.1)
            if not message:
                continue
    
    def get_received_count(self) -> int:
        """受信メッセージ数を取得"""
        return len(self.received_messages)
    
    def get_messages_by_id(self, can_id: int) -> List[CANMessage]:
        """指定IDのメッセージを取得"""
        return [msg for msg in self.received_messages if msg.actual_id == can_id]
    
    def clear_received_messages(self):
        """受信メッセージリストをクリア"""
        self.received_messages.clear()