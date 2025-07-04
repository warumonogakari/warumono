#!/usr/bin/env python3
"""
CAN送信側のテスト
"""

import pytest
import socket
import struct
from unittest.mock import Mock, patch, MagicMock
from can_core import CANMessage, CANInterface, CANSender
from datetime import datetime

class TestCANMessage:
    """CANMessageクラスのテスト"""
    
    def test_create_basic_message(self):
        """基本的なメッセージ作成テスト"""
        data = b"Hello"
        msg = CANMessage(can_id=0x123, data=data)
        
        assert msg.actual_id == 0x123
        assert msg.data == data
        assert msg.is_extended == False
        assert msg.dlc == 5
        assert isinstance(msg.timestamp, datetime)
    
    def test_create_extended_message(self):
        """拡張フレームメッセージ作成テスト"""
        msg = CANMessage(can_id=0x1FFFFFFF, data=b"Extended", is_extended=True)
        
        assert msg.actual_id == 0x1FFFFFFF
        assert msg.is_extended == True
    
    def test_data_formatting(self):
        """データフォーマット機能テスト"""
        msg = CANMessage(can_id=0x100, data=b"ABC\x01\x02")
        
        assert msg.to_hex_string() == "41 42 43 01 02"
        assert msg.to_ascii_string() == "ABC.."
    
    def test_empty_data(self):
        """空データのテスト"""
        msg = CANMessage(can_id=0x200, data=b"")
        
        assert msg.dlc == 0
        assert msg.to_hex_string() == ""
        assert msg.to_ascii_string() == ""

class TestCANInterface:
    """CANInterfaceクラスのテスト"""
    
    @patch('socket.socket')
    def test_successful_connection(self, mock_socket):
        """正常接続テスト"""
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        
        can_if = CANInterface('vcan0')
        result = can_if.connect()
        
        assert result == True
        assert can_if.is_connected() == True
        mock_socket.assert_called_once_with(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        mock_sock.bind.assert_called_once_with(('vcan0',))
    
    @patch('socket.socket')
    def test_connection_failure(self, mock_socket):
        """接続失敗テスト"""
        mock_socket.side_effect = OSError("No such device")
        
        can_if = CANInterface('invalid_interface')
        
        with pytest.raises(ConnectionError, match="CAN接続エラー"):
            can_if.connect()
        
        assert can_if.is_connected() == False
    
    @patch('socket.socket')
    def test_send_message_success(self, mock_socket):
        """メッセージ送信成功テスト"""
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        
        can_if = CANInterface('vcan0')
        can_if.connect()
        
        message = CANMessage(can_id=0x123, data=b"Test")
        result = can_if.send_message(message)
        
        assert result == True
        mock_sock.send.assert_called_once()
        
        # 送信されたデータの確認
        call_args = mock_sock.send.call_args[0][0]
        can_id, length, data = struct.unpack('<IB3x8s', call_args)
        assert can_id == 0x123
        assert length == 4
        assert data[:4] == b"Test"
    
    @patch('socket.socket')
    def test_send_extended_frame(self, mock_socket):
        """拡張フレーム送信テスト"""
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        
        can_if = CANInterface('vcan0')
        can_if.connect()
        
        message = CANMessage(can_id=0x1FFFFFFF, data=b"Ext", is_extended=True)
        can_if.send_message(message)
        
        # 拡張フラグが設定されているか確認
        call_args = mock_sock.send.call_args[0][0]
        can_id, _, _ = struct.unpack('<IB3x8s', call_args)
        assert can_id & 0x80000000 != 0  # 拡張フラグが設定されている
    
    @patch('socket.socket')
    def test_send_without_connection(self, mock_socket):
        """未接続状態での送信エラーテスト"""
        can_if = CANInterface('vcan0')
        message = CANMessage(can_id=0x123, data=b"Test")
        
        with pytest.raises(ConnectionError, match="CAN未接続"):
            can_if.send_message(message)
    
    @patch('socket.socket')
    def test_receive_message_success(self, mock_socket):
        """メッセージ受信成功テスト"""
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        
        # モックデータ作成（CAN ID=0x456, データ="RX"）
        test_data = b"RX"
        mock_frame = struct.pack('<IB3x8s', 0x456, len(test_data), test_data.ljust(8, b'\x00'))
        mock_sock.recv.return_value = mock_frame
        
        can_if = CANInterface('vcan0')
        can_if.connect()
        
        message = can_if.receive_message(timeout=1.0)
        
        assert message is not None
        assert message.actual_id == 0x456
        assert message.data == test_data
        assert message.is_extended == False
    
    @patch('socket.socket')
    def test_receive_timeout(self, mock_socket):
        """受信タイムアウトテスト"""
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        mock_sock.recv.side_effect = socket.timeout()
        
        can_if = CANInterface('vcan0')
        can_if.connect()
        
        message = can_if.receive_message(timeout=0.1)
        
        assert message is None

class TestCANSender:
    """CANSenderクラスのテスト"""
    
    @patch('can_core.CANInterface')
    def test_sender_initialization(self, mock_interface):
        """送信者初期化テスト"""
        sender = CANSender('test_can')
        
        assert sender.get_sent_count() == 0
        assert sender.get_last_sent_message() is None
    
    @patch('can_core.CANInterface')
    def test_send_message(self, mock_interface_class):
        """メッセージ送信テスト"""
        mock_interface = Mock()
        mock_interface.send_message.return_value = True
        mock_interface_class.return_value = mock_interface
        
        sender = CANSender('test_can')
        result = sender.send(0x123, b"Hello")
        
        assert result == True
        assert sender.get_sent_count() == 1
        
        last_msg = sender.get_last_sent_message()
        assert last_msg.actual_id == 0x123
        assert last_msg.data == b"Hello"
        assert last_msg.is_extended == False
    
    @patch('can_core.CANInterface')
    def test_send_extended_message(self, mock_interface_class):
        """拡張フレーム送信テスト"""
        mock_interface = Mock()
        mock_interface.send_message.return_value = True
        mock_interface_class.return_value = mock_interface
        
        sender = CANSender('test_can')
        result = sender.send(0x1FFFFFFF, b"Extended", is_extended=True)
        
        assert result == True
        last_msg = sender.get_last_sent_message()
        assert last_msg.is_extended == True
    
    @patch('can_core.CANInterface')
    def test_send_failure(self, mock_interface_class):
        """送信失敗テスト"""
        mock_interface = Mock()
        mock_interface.send_message.return_value = False
        mock_interface_class.return_value = mock_interface
        
        sender = CANSender('test_can')
        result = sender.send(0x123, b"Failed")
        
        assert result == False
        assert sender.get_sent_count() == 0  # 失敗時はカウントしない
    
    @patch('can_core.CANInterface')
    def test_multiple_sends(self, mock_interface_class):
        """複数送信テスト"""
        mock_interface = Mock()
        mock_interface.send_message.return_value = True
        mock_interface_class.return_value = mock_interface
        
        sender = CANSender('test_can')
        
        # 複数メッセージ送信
        sender.send(0x100, b"Msg1")
        sender.send(0x200, b"Msg2")
        sender.send(0x300, b"Msg3")
        
        assert sender.get_sent_count() == 3
        assert sender.get_last_sent_message().actual_id == 0x300

# フィクスチャ
@pytest.fixture
def sample_messages():
    """テスト用サンプルメッセージ"""
    return [
        CANMessage(0x123, b"Hello"),
        CANMessage(0x456, b"World"),
        CANMessage(0x789, b"\x01\x02\x03"),
        CANMessage(0x1FFFFFFF, b"Extended", is_extended=True),
    ]

class TestIntegrationScenarios:
    """統合シナリオテスト"""
    
    def test_message_data_integrity(self, sample_messages):
        """メッセージデータの整合性テスト"""
        for msg in sample_messages:
            # データ長制限テスト
            assert len(msg.data) <= 8
            
            # ID範囲テスト
            if msg.is_extended:
                assert 0 <= msg.actual_id <= 0x1FFFFFFF
            else:
                assert 0 <= msg.actual_id <= 0x7FF
    
    @patch('can_core.CANInterface')
    def test_sender_receiver_workflow(self, mock_interface_class):
        """送信・受信ワークフローテスト"""
        # 送信側設定
        mock_sender_interface = Mock()
        mock_sender_interface.send_message.return_value = True
        
        sender = CANSender('test_can')
        sender.can_interface = mock_sender_interface
        
        # テストメッセージ送信
        test_messages = [
            (0x100, b"Test1"),
            (0x200, b"Test2"),
            (0x300, b"Test3"),
        ]
        
        for can_id, data in test_messages:
            result = sender.send(can_id, data)
            assert result == True
        
        assert sender.get_sent_count() == 3
        
        # 送信されたメッセージの検証
        sent_ids = [msg.actual_id for msg in sender.sent_messages]
        expected_ids = [0x100, 0x200, 0x300]
        assert sent_ids == expected_ids

if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v"])