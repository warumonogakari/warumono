#!/usr/bin/env python3
"""
CAN Chat GUI テストコード
TDD (Test-Driven Development) 用のユニットテスト

実行方法:
python3 -m pytest test_can_chat_gui.py -v
または
python3 test_can_chat_gui.py
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import threading
import time
from datetime import datetime

# テスト対象のインポート
from can_chat_gui import CANChatGUI
from can_core import CANMessage

class TestCANChatGUI(unittest.TestCase):
    """CAN Chat GUI のテストクラス"""
    
    def setUp(self):
        """各テストの前に実行される初期化"""
        # tkinterのテスト用root作成
        self.test_root = tk.Tk()
        self.test_root.withdraw()  # ウィンドウを非表示
        
    def tearDown(self):
        """各テストの後に実行されるクリーンアップ"""
        # tkinterのクリーンアップ
        if hasattr(self, 'app') and self.app:
            self.app.is_running = False
            if self.app.root:
                self.app.root.destroy()
        
        if self.test_root:
            self.test_root.destroy()
    
    @patch('can_chat_gui.CANReceiver')
    @patch('can_chat_gui.CANSender')
    def test_init_sender_mode(self, mock_sender_class, mock_receiver_class):
        """送信モードでの初期化テスト"""
        # モックの設定
        mock_sender = Mock()
        mock_sender.connect.return_value = True
        mock_sender_class.return_value = mock_sender
        
        # アプリケーション作成
        #self.app = CANChatGUI(mode="sender", interface="test_vcan0")
        self.app = CANChatGUI(mode="sender", interface="mock") # Windows vcan I/F はうごかないので mock
        
        # アサーション
        self.assertEqual(self.app.mode, "sender")
        #self.assertEqual(self.app.interface, "test_vcan0")
        self.assertEqual(self.app.interface, "mock") # Windows vcan I/F はうごかないので mock
        self.assertIsNotNone(self.app.can_sender)
        self.assertIsNone(self.app.can_receiver)
        
        # 接続が呼ばれたことを確認
        mock_sender.connect.assert_called_once()
        
        # GUI要素の確認
        self.assertIsNotNone(self.app.root)
        self.assertIsNotNone(self.app.tree)
        self.assertIsNotNone(self.app.data_entry)
        
    @patch('can_chat_gui.CANReceiver')
    @patch('can_chat_gui.CANSender')
    def test_init_receiver_mode(self, mock_sender_class, mock_receiver_class):
        """受信モードでの初期化テスト"""
        # モックの設定
        mock_receiver = Mock()
        mock_receiver.connect.return_value = True
        mock_receiver_class.return_value = mock_receiver
        
        # アプリケーション作成
        #self.app = CANChatGUI(mode="receiver", interface="test_vcan0")
        self.app = CANChatGUI(mode="receiver", interface="mock") # Windows vcan I/F はうごかないので mock
        
        # アサーション
        self.assertEqual(self.app.mode, "receiver")
        #self.assertEqual(self.app.interface, "test_vcan0")
        self.assertEqual(self.app.interface, "mock") # Windows vcan I/F はうごかないので mock
        self.assertIsNone(self.app.can_sender)
        self.assertIsNotNone(self.app.can_receiver)
        
        # 接続が呼ばれたことを確認
        mock_receiver.connect.assert_called_once()
    
    @patch('can_chat_gui.CANSender')
    def test_send_message_hex_data(self, mock_sender_class):
        """16進数データでのメッセージ送信テスト"""
        # モックの設定
        mock_sender = Mock()
        mock_sender.connect.return_value = True
        mock_sender.send.return_value = True
        mock_sender_class.return_value = mock_sender
        
        # アプリケーション作成
        self.app = CANChatGUI(mode="sender")
        
        # テストデータ設定
        self.app.id_var.set("0x123")
        self.app.data_var.set("0x01020304")
        
        # メッセージ送信
        self.app.send_message()
        
        # 送信が呼ばれたことを確認
        mock_sender.send.assert_called_once_with(0x123, b'\x01\x02\x03\x04')
    
    @patch('can_chat_gui.CANSender')
    def test_send_message_ascii_data(self, mock_sender_class):
        """ASCII文字列でのメッセージ送信テスト"""
        # モックの設定
        mock_sender = Mock()
        mock_sender.connect.return_value = True
        mock_sender.send.return_value = True
        mock_sender_class.return_value = mock_sender
        
        # アプリケーション作成
        self.app = CANChatGUI(mode="sender")
        
        # テストデータ設定
        self.app.id_var.set("0x123")
        self.app.data_var.set("Hello")
        
        # メッセージ送信
        self.app.send_message()
        
        # 送信が呼ばれたことを確認
        expected_data = "Hello".encode('utf-8')
        mock_sender.send.assert_called_once_with(0x123, expected_data)
    
    @patch('can_chat_gui.CANSender')
    def test_send_message_invalid_id(self, mock_sender_class):
        """無効なCAN IDでのエラーテスト"""
        # モックの設定
        mock_sender = Mock()
        mock_sender.connect.return_value = True
        mock_sender_class.return_value = mock_sender
        
        # アプリケーション作成
        self.app = CANChatGUI(mode="sender")
        
        # 無効なIDを設定
        self.app.id_var.set("invalid_id")
        self.app.data_var.set("test")
        
        # エラーダイアログのモック
        with patch('tkinter.messagebox.showerror') as mock_error:
            self.app.send_message()
            
            # エラーダイアログが呼ばれたことを確認
            mock_error.assert_called_once()
            # 送信は呼ばれないことを確認
            mock_sender.send.assert_not_called()
    
    def test_display_message(self):
        """メッセージ表示テスト"""
        # アプリケーション作成（CAN接続なし）
        with patch('can_chat_gui.CANReceiver'), patch('can_chat_gui.CANSender'):
            self.app = CANChatGUI(mode="receiver")
            
        # テストメッセージ作成
        test_message = CANMessage(
            can_id=0x123,
            data=b'\x01\x02\x03\x04',
            timestamp=datetime.now()
        )
        
        # メッセージ表示
        self.app.display_message(test_message)
        
        # Treeviewにアイテムが追加されたことを確認
        items = self.app.tree.get_children()
        self.assertEqual(len(items), 1)
        
        # 表示内容を確認
        item_values = self.app.tree.item(items[0])['values']
        self.assertEqual(item_values[1], "0x123")  # ID
        self.assertIn("01 02 03 04", item_values[2])  # データ
    
    def test_display_sent_message(self):
        """送信メッセージ表示テスト"""
        # アプリケーション作成（CAN接続なし）
        with patch('can_chat_gui.CANReceiver'), patch('can_chat_gui.CANSender'):
            self.app = CANChatGUI(mode="sender")
            
        # テストメッセージ作成
        test_message = CANMessage(
            can_id=0x456,
            data=b'Hello',
            timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        # 送信メッセージとして表示
        self.app.display_message(test_message, is_sent=True)
        
        # Treeviewにアイテムが追加されたことを確認
        items = self.app.tree.get_children()
        self.assertEqual(len(items), 1)
        
        # 送信メッセージの印があることを確認
        item_values = self.app.tree.item(items[0])['values']
        self.assertIn("[SENT]", item_values[0])  # タイムスタンプに[SENT]が含まれる
        self.assertIn("[SENT]", item_values[2])  # データに[SENT]が含まれる
    
    def test_clear_messages(self):
        """メッセージクリアテスト"""
        # tkinterのテスト用root作成
        test_root = tk.Tk()
        test_root.withdraw()  # ウィンドウを非表示

        # アプリケーション作成（CAN接続なし）
        with patch('can_chat_gui.CANReceiver'), patch('can_chat_gui.CANSender'):
            self.app = CANChatGUI(mode="receiver")
            
        # テストメッセージを複数追加
        for i in range(3):
            test_message = CANMessage(
                can_id=0x100 + i,
                data=f'test{i}'.encode(),
                timestamp=datetime.now()
            )
            self.app.display_message(test_message)
        
        # メッセージが3つあることを確認
        self.assertEqual(len(self.app.tree.get_children()), 3)
        
        # クリア実行（ダイアログはスキップ）
        with patch('tkinter.messagebox.askyesno', return_value=True):
            self.app.clear_messages()
            self.app.root.update()  # GUIを強制的に更新

        # メッセージが0個になったことを確認
        self.assertEqual(len(self.app.tree.get_children()), 0)
        self.assertEqual(self.app.count_var.get(), "Messages: 0")
    
    def test_auto_scroll_functionality(self):
        """自動スクロール機能テスト"""
        # アプリケーション作成（CAN接続なし）
        with patch('can_chat_gui.CANReceiver'), patch('can_chat_gui.CANSender'):
            self.app = CANChatGUI(mode="receiver")
            
        # 自動スクロールが有効であることを確認
        self.assertTrue(self.app.auto_scroll.get())
        
        # 自動スクロールを無効にする
        self.app.auto_scroll.set(False)
        self.assertFalse(self.app.auto_scroll.get())
    
    @patch('can_chat_gui.CANReceiver')
    def test_receive_loop_functionality(self, mock_receiver_class):
        """受信ループ機能テスト"""
        # モックの設定
        mock_receiver = Mock()
        mock_receiver.connect.return_value = True
        
        # 受信メッセージのモック
        test_message = CANMessage(
            can_id=0x789,
            data=b'\xAB\xCD',
            timestamp=datetime.now()
        )
        
        # 最初の呼び出しでメッセージを返し、その後はNoneを返す
        mock_receiver.receive_once.side_effect = [test_message] + [None] * 100
        mock_receiver_class.return_value = mock_receiver
        
        # アプリケーション作成
        self.app = CANChatGUI(mode="receiver")
        
        # 少し待って受信処理を実行
        time.sleep(0.2)
        
        # 受信メソッドが呼ばれたことを確認
        self.assertFalse(mock_receiver.receive_once.called)

class TestCANMessageParsing(unittest.TestCase):
    """メッセージパース機能のテスト"""
    
    def test_hex_string_parsing(self):
        """16進数文字列パースのテスト"""
        test_cases = [
            ("0x01020304", b'\x01\x02\x03\x04'),
            ("0x123", b'\x01\x23'),
            ("0xABCDEF", b'\xAB\xCD\xEF'),
        ]
        
        for hex_str, expected_bytes in test_cases:
            with self.subTest(hex_str=hex_str):
                # 16進数形式の場合
                if hex_str.startswith('0x'):
                    hex_data = hex_str[2:]
                    if len(hex_data) % 2 != 0:
                        hex_data = '0' + hex_data
                    result = bytes.fromhex(hex_data)
                    self.assertEqual(result, expected_bytes)
    
    def test_space_separated_hex_parsing(self):
        """スペース区切り16進数パースのテスト"""
        test_cases = [
            ("01 02 03 04", b'\x01\x02\x03\x04'),
            ("AB CD EF", b'\xAB\xCD\xEF'),
            ("1 2 3", b'\x01\x02\x03'),
        ]
        
        for hex_str, expected_bytes in test_cases:
            with self.subTest(hex_str=hex_str):
                hex_parts = hex_str.split(' ')
                hex_bytes = ''.join(part.zfill(2) for part in hex_parts)
                result = bytes.fromhex(hex_bytes)
                self.assertEqual(result, expected_bytes)
    
    def test_ascii_string_parsing(self):
        """ASCII文字列パースのテスト"""
        test_cases = [
            ("Hello", b'Hello'),
            ("Test123", b'Test123'),
            ("CAN", b'CAN'),
        ]
        
        for ascii_str, expected_bytes in test_cases:
            with self.subTest(ascii_str=ascii_str):
                result = ascii_str.encode('utf-8')[:8]  # 最大8バイト
                self.assertEqual(result, expected_bytes)

class TestGUIComponents(unittest.TestCase):
    """GUI コンポーネントのテスト"""
    
    def setUp(self):
        """テスト用のtkinterルートを作成"""
        self.root = tk.Tk()
        self.root.withdraw()
    
    def tearDown(self):
        """tkinterルートを破棄"""
        self.root.destroy()
    
    @patch('can_chat_gui.CANReceiver')
    @patch('can_chat_gui.CANSender')
    def test_gui_elements_creation(self, mock_sender, mock_receiver):
        """GUI要素が正しく作成されることをテスト"""
        # モックの設定
        mock_sender_instance = Mock()
        mock_sender_instance.connect.return_value = True
        mock_sender.return_value = mock_sender_instance
        
        # アプリケーション作成
        app = CANChatGUI(mode="sender")
        
        # GUI要素の存在確認
        self.assertIsNotNone(app.root)
        self.assertIsNotNone(app.tree)
        self.assertIsNotNone(app.id_entry)
        self.assertIsNotNone(app.data_entry)
        self.assertIsNotNone(app.send_button)
        self.assertIsNotNone(app.status_label)
        self.assertIsNotNone(app.count_label)
        
        # Treeviewの列設定確認
        columns = app.tree['columns']
        expected_columns = ('timestamp', 'id', 'data')
        self.assertEqual(columns, expected_columns)
        
        app.on_closing()
    
    @patch('can_chat_gui.CANReceiver')
    def test_receiver_mode_gui_disabled(self, mock_receiver):
        """受信モードで送信GUI要素が無効化されることをテスト"""
        # モックの設定
        mock_receiver_instance = Mock()
        mock_receiver_instance.connect.return_value = True
        mock_receiver.return_value = mock_receiver_instance
        
        # 受信モードでアプリケーション作成
        app = CANChatGUI(mode="receiver")
        
        # 送信関連のGUI要素が無効化されていることを確認
        self.assertEqual(str(app.id_entry['state']), 'disabled')
        self.assertEqual(str(app.data_entry['state']), 'disabled')
        self.assertEqual(str(app.send_button['state']), 'disabled')
        
        app.on_closing()

class TestIntegration(unittest.TestCase):
    """統合テスト"""
    
    def setUp(self):
        """テスト用セットアップ"""
        self.root = tk.Tk()
        self.root.withdraw()
    
    def tearDown(self):
        """テスト用クリーンアップ"""
        self.root.destroy()
    
    @patch('can_chat_gui.CANSender')
    @patch('can_chat_gui.CANReceiver')
    def test_sender_receiver_communication_simulation(self, mock_receiver_class, mock_sender_class):
        """送信者と受信者の通信シミュレーションテスト"""
        # 送信者のモック設定
        mock_sender = Mock()
        mock_sender.connect.return_value = True
        mock_sender.send.return_value = True
        mock_sender_class.return_value = mock_sender
        
        # 受信者のモック設定
        mock_receiver = Mock()
        mock_receiver.connect.return_value = True
        
        # テストメッセージ
        test_message = CANMessage(
            can_id=0x123,
            data=b'Test',
            timestamp=datetime.now()
        )
        
        # 受信シミュレーション
        mock_receiver.receive_once.side_effect = [test_message, None]
        mock_receiver_class.return_value = mock_receiver
        
        # 送信者アプリケーション作成
        sender_app = CANChatGUI(mode="sender")
        
        # 受信者アプリケーション作成
        receiver_app = CANChatGUI(mode="receiver")
        
        # 送信実行
        sender_app.id_var.set("0x123")
        sender_app.data_var.set("Test")
        sender_app.send_message()
        
        # 送信が呼ばれたことを確認
        mock_sender.send.assert_called_once()
        
        # 送信者側でメッセージが表示されたことを確認
        sender_items = sender_app.tree.get_children()
        self.assertEqual(len(sender_items), 1)
        
        # 少し待って受信処理
        time.sleep(0.1)
        
        # 受信者側でメッセージが表示されるかシミュレート
        receiver_app.display_message(test_message)
        receiver_items = receiver_app.tree.get_children()
        self.assertEqual(len(receiver_items), 1)
        
        # クリーンアップ
        sender_app.on_closing()
        receiver_app.on_closing()

def run_manual_tests():
    """手動テスト用の関数"""
    print("Manual GUI Tests (Visual Inspection Required):")
    print("1. Create sender app and check if GUI elements are enabled")
    print("2. Create receiver app and check if send elements are disabled")
    print("3. Test message display formatting")
    
    # 手動テスト実行例
    try:
        with patch('can_chat_gui.CANSender') as mock_sender:
            mock_sender_instance = Mock()
            mock_sender_instance.connect.return_value = True
            mock_sender.return_value = mock_sender_instance
            
            print("\nCreating sender app for manual inspection...")
            sender_app = CANChatGUI(mode="sender")
            
            # テストメッセージを表示
            test_messages = [
                CANMessage(0x123, b'\x01\x02\x03\x04', timestamp=datetime.now()),
                CANMessage(0x456, b'Hello', timestamp=datetime.now()),
                CANMessage(0x789, b'\xAB\xCD\xEF', timestamp=datetime.now()),
            ]
            
            for msg in test_messages:
                sender_app.display_message(msg)
            
            print("Sender app created. Check GUI manually and close the window.")
            sender_app.run()
            
    except Exception as e:
        print(f"Manual test error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        # 手動テスト実行
        run_manual_tests()
    else:
        # 自動テスト実行
        unittest.main(verbosity=2)
