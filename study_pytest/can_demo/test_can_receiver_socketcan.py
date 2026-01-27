#!/usr/bin/env python3
"""
CAN受信側のテスト（python-can版）
"""

import pytest
import can
import time
from unittest.mock import Mock, patch, MagicMock
from can_core import CANMessage, CANReceiver, CANReceiverContext, create_can_receiver
from datetime import datetime, timedelta

class TestCANReceiver:
    """CANReceiverクラスのテスト"""
    
    @patch('can_core.CANInterface')
    def test_receiver_initialization(self, mock_interface):
        """受信者初期化テスト"""
        receiver = CANReceiver('test_can')
        
        assert receiver.get_received_count() == 0
        assert receiver.message_handler is None
        assert len(receiver.message_filters) == 0
    
    @patch('can_core.CANInterface')
    def test_receive_single_message(self, mock_interface_class):
        """単一メッセージ受信テスト"""
        # モックインターフェース設定
        mock_interface = Mock()
        test_message = CANMessage(0x123, b"Hello")
        mock_interface.receive_message.return_value = test_message
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        received_msg = receiver.receive_once(timeout=1.0)
        
        assert received_msg is not None
        assert received_msg.actual_id == 0x123
        assert received_msg.data == b"Hello"
        assert receiver.get_received_count() == 1
        mock_interface.receive_message.assert_called_once_with(1.0)
    
    @patch('can_core.CANInterface')
    def test_receive_timeout(self, mock_interface_class):
        """受信タイムアウトテスト"""
        mock_interface = Mock()
        mock_interface.receive_message.return_value = None  # タイムアウト
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        received_msg = receiver.receive_once(timeout=0.1)
        
        assert received_msg is None
        assert receiver.get_received_count() == 0
    
    @patch('can_core.CANInterface')
    def test_message_handler(self, mock_interface_class):
        """メッセージハンドラーテスト"""
        mock_interface = Mock()
        test_message = CANMessage(0x456, b"Handler")
        mock_interface.receive_message.return_value = test_message
        mock_interface_class.return_value = mock_interface
        
        # ハンドラー関数作成
        handler_calls = []
        def test_handler(message):
            handler_calls.append(message)
        
        receiver = CANReceiver('test_can')
        receiver.set_message_handler(test_handler)
        receiver.receive_once()
        
        assert len(handler_calls) == 1
        assert handler_calls[0].actual_id == 0x456
        assert handler_calls[0].data == b"Handler"
    
    @patch('can_core.CANInterface')
    def test_receive_multiple_messages(self, mock_interface_class):
        """複数メッセージ受信テスト"""
        mock_interface = Mock()
        
        # 複数のテストメッセージを準備
        test_messages = [
            CANMessage(0x100, b"Msg1"),
            CANMessage(0x200, b"Msg2"),
            CANMessage(0x300, b"Msg3"),
        ]
        mock_interface.receive_message.side_effect = test_messages + [None]  # 最後はタイムアウト
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        
        # 各メッセージを受信
        for i in range(3):
            msg = receiver.receive_once()
            assert msg is not None
            assert msg.actual_id == test_messages[i].actual_id
        
        assert receiver.get_received_count() == 3
    
    @patch('can_core.CANInterface')
    def test_get_messages_by_id(self, mock_interface_class):
        """ID別メッセージ取得テスト"""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        
        # 受信メッセージを直接設定（テスト用）
        receiver.received_messages = [
            CANMessage(0x123, b"First"),
            CANMessage(0x456, b"Second"),
            CANMessage(0x123, b"Third"),  # 同じIDで2回目
            CANMessage(0x789, b"Fourth"),
        ]
        
        # ID=0x123のメッセージを取得
        messages_123 = receiver.get_messages_by_id(0x123)
        assert len(messages_123) == 2
        assert messages_123[0].data == b"First"
        assert messages_123[1].data == b"Third"
        
        # ID=0x999（存在しない）のメッセージを取得
        messages_999 = receiver.get_messages_by_id(0x999)
        assert len(messages_999) == 0
    
    @patch('can_core.CANInterface')
    def test_clear_received_messages(self, mock_interface_class):
        """受信メッセージクリアテスト"""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        
        # テストメッセージを追加
        receiver.received_messages = [
            CANMessage(0x123, b"Test1"),
            CANMessage(0x456, b"Test2"),
        ]
        
        assert receiver.get_received_count() == 2
        
        receiver.clear_received_messages()
        assert receiver.get_received_count() == 0
    
    @patch('can_core.CANInterface')
    @patch('time.time')
    def test_receive_loop_duration(self, mock_time, mock_interface_class):
        """受信ループ時間制限テスト"""
        mock_interface = Mock()
        mock_interface.receive_message.return_value = CANMessage(0x123, b"Loop")
        mock_interface_class.return_value = mock_interface
        
        # 時間の経過をシミュレート
        start_time = 1000.0
        mock_time.side_effect = [start_time, start_time + 0.1, start_time + 0.2, start_time + 5.1]  # 5秒経過
        
        receiver = CANReceiver('test_can')
        receiver.receive_loop(duration=5.0)
        
        # 時間制限により終了
        assert mock_time.call_count >= 3
    
    @patch('can_core.CANInterface')
    def test_receive_loop_message_limit(self, mock_interface_class):
        """受信ループメッセージ数制限テスト"""
        mock_interface = Mock()
        mock_interface.receive_message.return_value = CANMessage(0x123, b"Limit")
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        receiver.receive_loop(duration=10.0, message_limit=3)
        
        # メッセージ数制限により終了
        assert receiver.get_received_count() <= 3

class TestCANReceiverFilters:
    """受信フィルター機能のテスト"""
    
    @patch('can_core.CANInterface')
    def test_id_filter(self, mock_interface_class):
        """ID範囲フィルターテスト"""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        receiver.add_id_filter(0x100, 0x1FF) # id が 0x100～0x1FF の範囲なら受信
        
        # テストメッセージ（フィルター内外の混在）
        test_messages = [
            CANMessage(0x150, b"Accept"),   # フィルター内
            CANMessage(0x250, b"Reject"),   # フィルター外
            CANMessage(0x180, b"Accept2"),  # フィルター内
        ]
        
        # フィルター適用テスト
        filtered = receiver.apply_filters(test_messages)
        
        assert len(filtered) == 2
        assert filtered[0].actual_id == 0x150
        assert filtered[1].actual_id == 0x180
    
    @patch('can_core.CANInterface')
    def test_data_filter(self, mock_interface_class):
        """データパターンフィルターテスト"""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        receiver.add_data_filter(b"ERROR")
        
        # テストメッセージ
        test_messages = [
            CANMessage(0x100, b"ERROR: Something wrong"),  # マッチ
            CANMessage(0x200, b"INFO: All good"),         # 不一致
            CANMessage(0x300, b"CRITICAL ERROR found"),   # マッチ
        ]
        
        # フィルター適用テスト
        filtered = receiver.apply_filters(test_messages)
        
        assert len(filtered) == 2
        assert b"ERROR" in filtered[0].data
        assert b"ERROR" in filtered[1].data
    
    @patch('can_core.CANInterface')
    def test_multiple_filters(self, mock_interface_class):
        """複数フィルター組み合わせテスト"""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        receiver.add_id_filter(0x100, 0x1FF)     # ID範囲フィルター
        receiver.add_data_filter(b"WARN")        # データパターンフィルター
        
        # テストメッセージ
        test_messages = [
            CANMessage(0x150, b"WARN: ID and data match"),   # 両方マッチ
            CANMessage(0x150, b"INFO: ID match only"),       # IDのみマッチ
            CANMessage(0x250, b"WARN: Data match only"),     # データのみマッチ
            CANMessage(0x250, b"INFO: No match"),            # 不一致
        ]
        
        # 複数フィルター適用（AND条件）
        filtered = receiver.apply_filters(test_messages)
        
        assert len(filtered) == 1
        assert filtered[0].actual_id == 0x150
        assert b"WARN" in filtered[0].data
    
    @patch('can_core.CANInterface')
    def test_clear_filters(self, mock_interface_class):
        """フィルタークリアテスト"""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        receiver.add_id_filter(0x100, 0x1FF)
        receiver.add_data_filter(b"TEST")
        
        assert len(receiver.message_filters) == 2
        
        receiver.clear_filters()
        assert len(receiver.message_filters) == 0
    
    @patch('can_core.CANInterface')
    def test_receive_with_filter(self, mock_interface_class):
        """フィルター付き受信テスト"""
        mock_interface = Mock()
        
        # フィルター外のメッセージも含めて設定
        test_messages = [
            CANMessage(0x150, b"Accept"),   # フィルター内
            CANMessage(0x250, b"Reject"),   # フィルター外
            CANMessage(0x180, b"Accept2"),  # フィルター内
        ]
        mock_interface.receive_message.side_effect = test_messages + [None]
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        receiver.add_id_filter(0x100, 0x1FF)  # ID範囲フィルター設定
        
        # 受信テスト（フィルターが自動適用される）
        received_messages = []
        for _ in range(len(test_messages)):
            msg = receiver.receive_once()
            if msg:  # フィルター通過したメッセージのみ
                received_messages.append(msg)
        
        # フィルター内のメッセージのみ受信されることを確認
        assert len(received_messages) == 2  # 0x150, 0x180 のみ
        assert all(0x100 <= msg.actual_id <= 0x1FF for msg in received_messages)

class TestCANReceiverAdvancedFeatures:
    """受信側の高度な機能テスト"""
    
    @patch('can_core.CANInterface')
    def test_extended_frame_handling(self, mock_interface_class):
        """拡張フレーム処理テスト"""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        
        # 標準フレームと拡張フレームを混在
        test_messages = [
            CANMessage(0x123, b"Standard", is_extended=False),
            CANMessage(0x1FFFFFFF, b"Extended", is_extended=True),
            CANMessage(0x456, b"Standard2", is_extended=False),
        ]
        
        receiver.received_messages = test_messages
        
        # 拡張フレームの検証
        extended_msgs = [msg for msg in receiver.received_messages if msg.is_extended]
        standard_msgs = [msg for msg in receiver.received_messages if not msg.is_extended]
        
        assert len(extended_msgs) == 1
        assert len(standard_msgs) == 2
        assert extended_msgs[0].actual_id == 0x1FFFFFFF
    
    @patch('can_core.CANInterface')
    def test_timestamp_ordering(self, mock_interface_class):
        """タイムスタンプ順序テスト"""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        
        # 異なるタイムスタンプのメッセージ
        base_time = datetime.now()
        test_messages = [
            CANMessage(0x100, b"First", timestamp=base_time),
            CANMessage(0x200, b"Second", timestamp=base_time + timedelta(seconds=1)),
            CANMessage(0x300, b"Third", timestamp=base_time + timedelta(seconds=2)),
        ]
        
        receiver.received_messages = test_messages
        
        # タイムスタンプ順序確認
        timestamps = [msg.timestamp for msg in receiver.received_messages]
        assert timestamps == sorted(timestamps)
    
    @patch('can_core.CANInterface')
    def test_error_recovery(self, mock_interface_class):
        """エラー回復テスト"""
        mock_interface = Mock()
        
        # 最初の呼び出しでエラー、2回目で成功
        mock_interface.receive_message.side_effect = [
            RuntimeError("Receive error"),
            CANMessage(0x123, b"Recovery"),
            None
        ]
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        
        # 最初の受信はエラーで失敗
        with pytest.raises(RuntimeError):
            receiver.receive_once()
        
        # 2回目の受信は成功
        msg = receiver.receive_once()
        assert msg is not None
        assert msg.data == b"Recovery"

class TestCANReceiverContext:
    """CANReceiverContextクラスのテスト"""
    
    @patch('can_core.CANInterface')
    def test_context_manager(self, mock_interface_class):
        """コンテキストマネージャーテスト"""
        mock_interface = Mock()
        mock_interface.connect.return_value = True
        mock_interface.receive_message.return_value = CANMessage(0x123, b"Context")
        mock_interface_class.return_value = mock_interface
        
        # with文で使用
        with CANReceiverContext('test_can') as receiver:
            msg = receiver.receive_once(timeout=1.0)
            assert msg is not None
            assert msg.data == b"Context"
            assert receiver.get_received_count() == 1
        
        # 自動でdisconnectが呼ばれる
        mock_interface.disconnect.assert_called_once()
    
    @patch('can_core.CANInterface')
    def test_context_manager_exception(self, mock_interface_class):
        """例外発生時のコンテキストマネージャーテスト"""
        mock_interface = Mock()
        mock_interface.connect.return_value = True
        mock_interface_class.return_value = mock_interface
        
        try:
            with CANReceiverContext('test_can') as receiver:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # 例外が発生してもdisconnectが呼ばれる
        mock_interface.disconnect.assert_called_once()

class TestPerformanceMetrics:
    """パフォーマンス関連テスト"""
    
    @patch('can_core.CANInterface')
    def test_high_frequency_reception(self, mock_interface_class):
        """高頻度受信テスト"""
        mock_interface = Mock()
        
        # 大量のメッセージを生成
        messages = [CANMessage(i % 10, f"Msg{i}".encode()) for i in range(100)]
        mock_interface.receive_message.side_effect = messages + [None]
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        
        # 100メッセージを受信
        for _ in range(100):
            msg = receiver.receive_once()
            if msg is None:
                break
        
        assert receiver.get_received_count() <= 100
        assert len(receiver.received_messages) <= 100
    
    @patch('can_core.CANInterface')
    def test_memory_usage_control(self, mock_interface_class):
        """メモリ使用量制御テスト"""
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        receiver = CANReceiver('test_can')
        
        # 大量のメッセージを追加
        large_messages = [CANMessage(i, b"X" * 8) for i in range(1000)]
        receiver.received_messages = large_messages
        
        assert receiver.get_received_count() == 1000
        
        # クリアしてメモリ解放
        receiver.clear_received_messages()
        assert receiver.get_received_count() == 0

class TestConvenienceFeatures:
    """便利機能のテスト"""
    
    @patch('can_core.CANReceiver')
    def test_create_can_receiver(self, mock_receiver_class):
        """create_can_receiver関数テスト"""
        mock_receiver = Mock()
        mock_receiver.connect.return_value = True
        mock_receiver_class.return_value = mock_receiver
        
        receiver = create_can_receiver('test_interface')
        
        mock_receiver_class.assert_called_once_with('test_interface')
        mock_receiver.connect.assert_called_once()

# 統合テスト用フィクスチャ
@pytest.fixture
def mock_can_environment():
    """モックCAN環境フィクスチャ"""
    with patch('can_core.CANInterface') as mock_interface_class:
        mock_interface = Mock()
        mock_interface.connect.return_value = True
        mock_interface.is_connected.return_value = True
        mock_interface_class.return_value = mock_interface
        yield mock_interface

class TestReceiverIntegration:
    """受信側統合テスト"""
    
    def test_complete_receive_workflow(self, mock_can_environment):
        """完全な受信ワークフローテスト"""
        # テストシナリオ：
        # 1. 受信者を初期化
        # 2. 接続
        # 3. フィルター設定
        # 4. メッセージハンドラー設定
        # 5. 複数メッセージ受信
        # 6. 統計確認
        # 7. 切断
        
        receiver = CANReceiver('test_can')
        
        # ハンドラー追跡用
        handled_messages = []
        def message_handler(msg):
            handled_messages.append(msg)
        
        receiver.set_message_handler(message_handler)
        receiver.add_id_filter(0x100, 0x1FF)  # フィルター設定 id 0x100～0x1FFのフレームしか受信しない
        
        # 接続
        result = receiver.connect()
        assert result == True
        
        # テストメッセージシーケンス（フィルター考慮）
        test_sequence = [
            CANMessage(0x150, b"Start"),    # フィルター内
            CANMessage(0x250, b"Skip"),     # フィルター外
            CANMessage(0x160, b"Data1"),    # フィルター内
            CANMessage(0x170, b"End"),      # フィルター内
        ]
        
        # メッセージを手動で追加（統合テスト用）
        for msg in test_sequence:
            if receiver.apply_filters([msg]):  # フィルター適用
                receiver.received_messages.append(msg)
                if receiver.message_handler:
                    receiver.message_handler(msg)
        
        # 結果確認（フィルター適用後）
        assert receiver.get_received_count() == 3  # フィルター外の1つを除く
        assert len(handled_messages) == 3
        
        # フィルター内のメッセージのみ
        assert all(0x100 <= msg.actual_id <= 0x1FF for msg in receiver.received_messages)
        
        # 切断
        receiver.disconnect()
    
    def test_real_time_processing_simulation(self, mock_can_environment):
        """リアルタイム処理シミュレーションテスト"""
        receiver = CANReceiver('test_can')
        
        # リアルタイム処理追跡
        processing_log = []
        
        def real_time_handler(msg):
            processing_log.append({
                'id': msg.actual_id,
                'data': msg.data,
                'timestamp': msg.timestamp,
                'processed_at': datetime.now()
            })
        
        receiver.set_message_handler(real_time_handler)
        
        # シミュレーション用メッセージ
        simulation_messages = [
            CANMessage(0x100, b"Sensor1"),
            CANMessage(0x101, b"Sensor2"),
            CANMessage(0x102, b"Sensor3"),
        ]
        
        # リアルタイム処理シミュレーション
        for msg in simulation_messages:
            receiver.received_messages.append(msg)
            receiver.message_handler(msg)
        
        # 処理結果確認
        assert len(processing_log) == 3
        assert all('processed_at' in entry for entry in processing_log)
        
        # センサーデータの順序確認
        sensor_ids = [entry['id'] for entry in processing_log]
        assert sensor_ids == [0x100, 0x101, 0x102]

if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])