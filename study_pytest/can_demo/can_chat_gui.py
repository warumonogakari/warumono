#!/usr/bin/env python3
"""
CAN Chat GUI アプリケーション - Linux版（最終修正版）
問題：is_runningのタイミング問題を修正

使用方法: python3 can_chat_gui_final.py [sender|receiver]
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import threading
import time
from datetime import datetime
from typing import Optional, Callable, List

try:
    from can_core import CANSender, CANReceiver, CANMessage
except ImportError as e:
    messagebox.showerror("Import Error", f"can_core.pyが見つかりません: {e}")
    sys.exit(1)

class CANChatGUI:
    """CAN Chat GUIアプリケーションのメインクラス - 最終修正版"""
    
    def __init__(self, mode: str = "receiver", interface: str = "vcan0"):
        self.mode = mode  # "sender" or "receiver"
        self.interface = interface
        
        # 重要：is_runningを最初にTrueに設定
        self.is_running = True
        
        # CAN関連（初期化）
        self.can_sender: Optional[CANSender] = None
        self.can_receiver: Optional[CANReceiver] = None
        
        # 受信スレッド（必ず初期化）
        self.receive_thread: Optional[threading.Thread] = None
        
        # GUI関連
        self.root = tk.Tk()
        
        try:
            self.setup_gui()
            self.setup_can()
        except Exception as e:
            self.cleanup_on_error()
            raise e
        
    def cleanup_on_error(self):
        """エラー時のクリーンアップ"""
        self.is_running = False
        if hasattr(self, 'can_sender') and self.can_sender:
            try:
                self.can_sender.disconnect()
            except:
                pass
        if hasattr(self, 'can_receiver') and self.can_receiver:
            try:
                self.can_receiver.disconnect()
            except:
                pass
        
    def setup_gui(self):
        """GUI セットアップ"""
        self.root.title(f"CAN Chat - {self.mode.title()}")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # タイトルラベル
        title_label = ttk.Label(main_frame, 
                               text=f"CAN Chat - {self.mode.title()} Mode",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # メッセージ表示エリア（Treeview）
        self.setup_message_display(main_frame)
        
        # 入力エリア
        self.setup_input_area(main_frame)
        
        # ステータスバー
        self.setup_status_bar(main_frame)
        
    def setup_message_display(self, parent):
        """メッセージ表示エリアのセットアップ"""
        # フレーム
        display_frame = ttk.LabelFrame(parent, text="Messages", padding="5")
        display_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(0, weight=1)
        
        # Treeview作成
        columns = ('timestamp', 'id', 'data')
        self.tree = ttk.Treeview(display_frame, 
                                columns=columns,
                                show='headings',
                                height=15)
        
        # 列の設定
        self.tree.heading('timestamp', text='TIMESTAMP')
        self.tree.heading('id', text='ID')
        self.tree.heading('data', text='DATA')
        
        self.tree.column('timestamp', width=180, minwidth=150)
        self.tree.column('id', width=100, minwidth=80)
        self.tree.column('data', width=400, minwidth=200)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # グリッド配置
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 自動スクロール用
        self.auto_scroll = tk.BooleanVar(value=True)
        auto_scroll_cb = ttk.Checkbutton(display_frame, 
                                        text="Auto Scroll",
                                        variable=self.auto_scroll)
        auto_scroll_cb.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # クリアボタン
        clear_button = ttk.Button(display_frame, text="Clear Messages", 
                                 command=self.clear_messages)
        clear_button.grid(row=1, column=1, sticky=tk.E, pady=(5, 0))
        
    def setup_input_area(self, parent):
        """入力エリアのセットアップ"""
        input_frame = ttk.LabelFrame(parent, text="Send Message", padding="5")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        # CAN ID入力
        ttk.Label(input_frame, text="CAN ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.id_var = tk.StringVar(value="0x123")
        self.id_entry = ttk.Entry(input_frame, textvariable=self.id_var, width=10)
        self.id_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # データ入力
        ttk.Label(input_frame, text="Data:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.data_var = tk.StringVar()
        self.data_entry = ttk.Entry(input_frame, textvariable=self.data_var)
        self.data_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 送信ボタン
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=4, sticky=tk.E)
        
        # ヘルプテキスト
        help_text = "Data formats: 0x01020304, 01 02 03 04, or ASCII text"
        help_label = ttk.Label(input_frame, text=help_text, 
                              font=("Arial", 8))
        help_label.grid(row=1, column=0, columnspan=5, sticky=tk.W, pady=(5, 0))
        
        # Enterキーで送信
        self.data_entry.bind('<Return>', lambda e: self.send_message())
        self.id_entry.bind('<Return>', lambda e: self.data_entry.focus())
        
        # senderモードでない場合は無効化
        if self.mode != "sender":
            self.id_entry.config(state="disabled")
            self.data_entry.config(state="disabled")
            self.send_button.config(state="disabled")
    
    def setup_status_bar(self, parent):
        """ステータスバーのセットアップ"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(1, weight=1)
        
        # 接続状態
        self.status_var = tk.StringVar(value="Connecting...")
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # メッセージカウント
        self.count_var = tk.StringVar(value="Messages: 0")
        self.count_label = ttk.Label(status_frame, textvariable=self.count_var)
        self.count_label.grid(row=0, column=2, sticky=tk.E)
        
        # 現在時刻表示
        self.time_var = tk.StringVar()
        self.time_label = ttk.Label(status_frame, textvariable=self.time_var)
        self.time_label.grid(row=0, column=3, sticky=tk.E, padx=(15, 0))
        
        # 時刻更新
        self.update_time()
        
    def update_time(self):
        """現在時刻の更新"""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_var.set(current_time)
            if self.is_running:  # アプリが実行中の場合のみ続行
                self.root.after(1000, self.update_time)
        except:
            pass  # 終了処理中のエラーを無視
        
    def setup_can(self):
        """CAN インターフェースのセットアップ - 修正版"""
        try:
            if self.mode == "sender":
                print(f"[SETUP] Connecting to CAN interface: {self.interface} (sender mode)")
                self.can_sender = CANSender(interface=self.interface)
                if self.can_sender.connect():
                    self.status_var.set(f"Connected (Sender) - {self.interface}")
                    print("[SETUP] CAN Sender connected successfully")
                else:
                    raise ConnectionError("Failed to connect sender")
            else:
                print(f"[SETUP] Connecting to CAN interface: {self.interface} (receiver mode)")
                self.can_receiver = CANReceiver(interface=self.interface)
                if self.can_receiver.connect():
                    self.status_var.set(f"Connected (Receiver) - {self.interface}")
                    print("[SETUP] CAN Receiver connected successfully")
                    print(f"[SETUP] is_running before start_receiving: {self.is_running}")
                    self.start_receiving()
                else:
                    raise ConnectionError("Failed to connect receiver")
                    
            print(f"[SETUP] CAN setup completed, is_running: {self.is_running}")
            
        except Exception as e:
            error_msg = f"Failed to setup CAN: {e}\n\n"
            error_msg += "チェック項目:\n"
            error_msg += f"• vcan0インターフェースが存在するか: ip link show {self.interface}\n"
            error_msg += f"• vcan0インターフェースが有効か: ip link show {self.interface} | grep UP\n"
            error_msg += "• can_core.pyが正しく配置されているか\n"
            error_msg += "• python-canがインストールされているか"
            
            print(f"[ERROR] CAN setup error: {e}")
            messagebox.showerror("Connection Error", error_msg)
            self.status_var.set(f"Error: {e}")
            # エラーが発生してもGUIは表示し続ける
    
    def start_receiving(self):
        """受信スレッドを開始 - 修正版"""
        if self.can_receiver and self.receive_thread is None:
            print(f"[THREAD] Starting receive thread, is_running: {self.is_running}")
            self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
            self.receive_thread.start()
            print("[THREAD] Receive thread started")
    
    def receive_loop(self):
        """受信ループ（別スレッドで実行）- 終了処理改善版"""
        print(f"[LOOP] Receive loop started")
        print(f"[LOOP] Initial state - is_running: {self.is_running}, can_receiver: {self.can_receiver is not None}")
        
        if not self.is_running:
            print("[LOOP] ERROR: is_running is False at loop start!")
            return
            
        if not self.can_receiver:
            print("[LOOP] ERROR: can_receiver is None at loop start!")
            return
        
        loop_count = 0
        last_message_time = time.time()
        
        while self.is_running and self.can_receiver:
            try:
                loop_count += 1
                
                # 詳細ログ（最初の10回と100回ごと）
                if loop_count <= 10 or loop_count % 100 == 0:
                    print(f"[LOOP] Iteration {loop_count}, is_running: {self.is_running}")
                
                # 終了チェック（受信前）
                if not self.is_running:
                    print("[LOOP] Stopping due to is_running=False")
                    break
                    
                message = self.can_receiver.receive_once(timeout=1.0)
                if message:
                    last_message_time = time.time()
                    print(f"[LOOP] Received message: ID=0x{message.actual_id:03X}, Data={message.to_hex_string()}")
                    # GUIスレッドで表示更新
                    if self.is_running:  # 表示前にも確認
                        self.root.after(0, self.display_message, message)
                else:
                    # 長時間メッセージが来ない場合の生存確認
                    if time.time() - last_message_time > 30:  # 30秒
                        print(f"[LOOP] No message for 30s, loop count: {loop_count}")
                        last_message_time = time.time()
                        
            except RuntimeError as e:
                # 終了時の "Bad file descriptor" エラーは正常
                if "Bad file descriptor" in str(e) and not self.is_running:
                    print("[LOOP] Normal shutdown - CAN interface already closed")
                    break
                else:
                    print(f"[LOOP] Receive error: {e}")
                    time.sleep(0.1)
            except Exception as e:
                print(f"[LOOP] Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
                
        print(f"[LOOP] Receive loop ended - is_running: {self.is_running}, can_receiver: {self.can_receiver is not None}")
    
    def send_message(self):
        """メッセージ送信"""
        if not self.can_sender:
            messagebox.showwarning("Warning", "Sender not initialized")
            return
            
        try:
            # CAN ID の解析
            id_str = self.id_var.get().strip()
            if not id_str:
                messagebox.showwarning("Warning", "Please enter CAN ID")
                self.id_entry.focus()
                return
                
            if id_str.startswith('0x') or id_str.startswith('0X'):
                can_id = int(id_str, 16)
            else:
                can_id = int(id_str)
                
            # CAN ID範囲チェック
            if can_id < 0 or can_id > 0x7FF:
                messagebox.showwarning("Warning", "CAN ID must be between 0x000 and 0x7FF")
                self.id_entry.focus()
                return
                
            # データの解析
            data_str = self.data_var.get().strip()
            if not data_str:
                messagebox.showwarning("Warning", "Please enter data")
                self.data_entry.focus()
                return
                
            # データをバイト列に変換
            data = self.parse_data_string(data_str)
            if data is None:
                return  # エラーメッセージは parse_data_string 内で表示済み
                
            # 送信
            print(f"[SEND] Sending message: ID=0x{can_id:03X}, Data={data.hex().upper()}")
            success = self.can_sender.send(can_id, data)
            if success:
                # 送信したメッセージも表示
                sent_message = CANMessage(can_id, data)
                self.display_message(sent_message, is_sent=True)
                self.data_var.set("")  # 入力クリア
                self.data_entry.focus()  # フォーカスを戻す
                print("[SEND] Message sent successfully")
            else:
                messagebox.showerror("Error", "Failed to send message")
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            self.id_entry.focus()
        except Exception as e:
            messagebox.showerror("Error", f"Send error: {e}")
    
    def parse_data_string(self, data_str: str) -> Optional[bytes]:
        """データ文字列をバイト列に変換"""
        try:
            if data_str.startswith('0x') or data_str.startswith('0X'):
                # 16進数形式: "0x01020304"
                hex_str = data_str[2:]
                if len(hex_str) % 2 != 0:
                    hex_str = '0' + hex_str
                if len(hex_str) > 16:  # 8バイト = 16文字
                    messagebox.showwarning("Warning", "Data too long (max 8 bytes)")
                    return None
                return bytes.fromhex(hex_str)
            elif all(c in '0123456789abcdefABCDEF ' for c in data_str):
                # スペース区切り16進数: "01 02 03 04"
                hex_bytes = data_str.replace(' ', '')
                if len(hex_bytes) % 2 != 0:
                    hex_bytes = '0' + hex_bytes
                if len(hex_bytes) > 16:
                    messagebox.showwarning("Warning", "Data too long (max 8 bytes)")
                    return None
                return bytes.fromhex(hex_bytes)
            else:
                # ASCII文字列
                data_bytes = data_str.encode('utf-8')
                if len(data_bytes) > 8:
                    messagebox.showwarning("Warning", "ASCII data too long (max 8 bytes)")
                    return None
                return data_bytes
        except ValueError:
            messagebox.showerror("Error", "Invalid data format")
            return None
    
    def display_message(self, message: CANMessage, is_sent: bool = False):
        """メッセージをTreeviewに表示"""
        try:
            timestamp = message.timestamp.strftime("%H:%M:%S.%f")[:-3]
            can_id = f"0x{message.actual_id:03X}"
            data = message.to_hex_string()
            
            # ASCII表示も追加
            ascii_data = message.to_ascii_string()
            if ascii_data and ascii_data != '.' * len(message.data):
                data += f" ({ascii_data})"
                
            # 送信メッセージには印を付ける
            if is_sent:
                data = "[SENT] " + data
                
            # Treeviewに追加
            item = self.tree.insert('', 'end', values=(timestamp, can_id, data))
            
            # 自動スクロール
            if self.auto_scroll.get():
                self.tree.see(item)
                
            # メッセージカウント更新
            count = len(self.tree.get_children())
            self.count_var.set(f"Messages: {count}")
            
            # 色分け（送信メッセージ）
            if is_sent:
                self.tree.set(item, 'timestamp', f"[SENT] {timestamp}")
                
            print(f"[GUI] Message displayed: {timestamp} {can_id} {data}")
        except Exception as e:
            print(f"[GUI] Display message error: {e}")
    
    def clear_messages(self):
        """メッセージリストをクリア"""
        result = messagebox.askyesno("Clear Messages", 
                                   "Are you sure you want to clear all messages?")
        if result:
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.count_var.set("Messages: 0")
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        print("[CLOSE] Application closing...")
        self.is_running = False
        
        # CAN接続を閉じる
        try:
            if self.can_sender:
                print("[CLOSE] Disconnecting CAN sender...")
                self.can_sender.disconnect()
        except Exception as e:
            print(f"[CLOSE] Error disconnecting sender: {e}")
            
        try:
            if self.can_receiver:
                print("[CLOSE] Disconnecting CAN receiver...")
                self.can_receiver.disconnect()
        except Exception as e:
            print(f"[CLOSE] Error disconnecting receiver: {e}")
            
        # 受信スレッドの終了を待つ
        if hasattr(self, 'receive_thread') and self.receive_thread and self.receive_thread.is_alive():
            print("[CLOSE] Waiting for receive thread to finish...")
            self.receive_thread.join(timeout=2.0)
            if self.receive_thread.is_alive():
                print("[CLOSE] Receive thread did not finish in time")
            else:
                print("[CLOSE] Receive thread finished")
        
        try:
            self.root.destroy()
            print("[CLOSE] GUI destroyed")
        except Exception as e:
            print(f"[CLOSE] Error destroying GUI: {e}")
    
    def run(self):
        """アプリケーション実行"""
        try:
            print(f"[MAIN] Starting CAN Chat GUI in {self.mode} mode...")
            print(f"[MAIN] Initial is_running: {self.is_running}")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("[MAIN] Application interrupted by user")
        except Exception as e:
            print(f"[MAIN] Application error: {e}")
        finally:
            self.cleanup_on_error()

def main():
    """メイン関数"""
    mode = "receiver"  # デフォルト
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
    if mode not in ["sender", "receiver"]:
        print("Usage: python3 can_chat_gui_final.py [sender|receiver]")
        sys.exit(1)
        
    try:
        app = CANChatGUI(mode=mode)
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted")
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Application Error", f"アプリケーションエラー: {e}")

if __name__ == "__main__":
    main()