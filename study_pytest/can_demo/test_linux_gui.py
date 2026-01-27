#!/usr/bin/env python3
"""
Linux環境でのGUI動作確認スクリプト
実行方法: python3 test_linux_gui.py
"""

import sys
import platform
import os
import subprocess

def check_python_version():
    """Python バージョンチェック"""
    print("=== Python 環境チェック ===")
    print(f"Python バージョン: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print("✅ Python バージョン OK")
        return True
    else:
        print("❌ Python 3.8以上が必要です")
        return False

def check_display_environment():
    """X11ディスプレイ環境チェック"""
    print("\n=== X11ディスプレイ環境チェック ===")
    
    # DISPLAY環境変数チェック
    display = os.environ.get('DISPLAY')
    if display:
        print(f"✅ DISPLAY環境変数: {display}")
    else:
        print("❌ DISPLAY環境変数が設定されていません")
        print("解決方法:")
        print("1. 直接ログイン（GUIセッション）")
        print("2. SSH -X: ssh -X user@hostname")
        print("3. VNC/RDP接続")
        return False
    
    # X11サーバー接続テスト
    try:
        result = subprocess.run(['xset', 'q'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ X11サーバー接続 OK")
        else:
            print("❌ X11サーバーに接続できません")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ xset コマンドが見つかりません")
        print("インストール: sudo apt install x11-xserver-utils")
        return False
    
    return True

def check_tkinter():
    """tkinter モジュールチェック"""
    print("\n=== tkinter チェック ===")
    try:
        import tkinter as tk
        print("✅ tkinter インポート成功")
        
        # tkinter バージョン確認
        try:
            print(f"tkinter バージョン: {tk.TkVersion}")
            print(f"Tcl/Tk バージョン: {tk.TclVersion}")
        except:
            print("⚠️  バージョン情報取得失敗")
        
        return True
    except ImportError as e:
        print(f"❌ tkinter インポートエラー: {e}")
        print("解決方法:")
        print("sudo apt install python3-tk")
        return False

def check_ttk():
    """tkinter.ttk モジュールチェック"""
    print("\n=== tkinter.ttk チェック ===")
    try:
        from tkinter import ttk
        print("✅ tkinter.ttk インポート成功")
        return True
    except ImportError as e:
        print(f"❌ tkinter.ttk インポートエラー: {e}")
        return False

def check_fonts():
    """Linux フォントチェック"""
    print("\n=== Linux フォント環境チェック ===")
    try:
        import tkinter as tk
        from tkinter import font
        
        root = tk.Tk()
        root.withdraw()
        
        # Linux環境での推奨フォント
        font_candidates = [
            ("DejaVu Sans", 10),
            ("Liberation Sans", 10),
            ("Ubuntu", 10),
            ("Noto Sans", 10),
            ("Arial", 10),
            ("Helvetica", 10)
        ]
        
        available_fonts = []
        for font_name, font_size in font_candidates:
            try:
                test_font = font.Font(family=font_name, size=font_size)
                # フォントが実際に存在するかテスト
                actual_family = test_font.actual()['family']
                if actual_family.lower() == font_name.lower():
                    available_fonts.append(font_name)
                    print(f"✅ {font_name}: 利用可能")
                else:
                    print(f"⚠️  {font_name}: 代替フォント ({actual_family})")
            except Exception as e:
                print(f"❌ {font_name}: 利用不可 ({e})")
        
        root.destroy()
        
        print(f"利用可能フォント: {len(available_fonts)}/{len(font_candidates)}")
        return len(available_fonts) > 0
        
    except Exception as e:
        print(f"❌ フォントチェックエラー: {e}")
        return False

def check_can_environment():
    """CAN環境チェック"""
    print("\n=== CAN環境チェック ===")
    
    # can-utils確認
    try:
        result = subprocess.run(['candump', '--help'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ can-utils インストール済み")
        else:
            print("❌ can-utils が正しく動作しません")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ can-utils がインストールされていません")
        print("インストール: sudo apt install can-utils")
        return False
    
    # vcan0インターフェース確認
    try:
        result = subprocess.run(['ip', 'link', 'show', 'vcan0'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ vcan0 インターフェース存在")
            if "UP" in result.stdout:
                print("✅ vcan0 インターフェース有効")
            else:
                print("⚠️  vcan0 インターフェース無効")
                print("有効化: sudo ip link set up vcan0")
        else:
            print("❌ vcan0 インターフェースが存在しません")
            print("作成手順:")
            print("  sudo modprobe vcan")
            print("  sudo ip link add dev vcan0 type vcan")
            print("  sudo ip link set up vcan0")
            return False
    except FileNotFoundError:
        print("❌ ip コマンドが見つかりません")
        return False
    
    # python-can確認
    try:
        import can
        print(f"✅ python-can インストール済み (version: {can.__version__})")
    except ImportError:
        print("❌ python-can がインストールされていません")
        print("インストール: pip3 install python-can")
        return False
    
    return True

def check_permissions():
    """権限チェック"""
    print("\n=== 権限チェック ===")
    
    # dialoutグループ確認
    try:
        import grp
        import pwd
        
        username = pwd.getpwuid(os.getuid()).pw_name
        dialout_group = grp.getgrnam('dialout')
        
        if username in dialout_group.gr_mem:
            print("✅ dialout グループメンバー")
        else:
            print("⚠️  dialout グループに所属していません")
            print(f"追加: sudo usermod -a -G dialout {username}")
            print("追加後は再ログインが必要です")
    except KeyError:
        print("⚠️  dialout グループが存在しません")
    except Exception as e:
        print(f"⚠️  権限チェックエラー: {e}")
    
    # X11権限確認
    try:
        result = subprocess.run(['xhost'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ X11権限 OK")
        else:
            print("⚠️  X11権限に問題がある可能性")
    except:
        print("⚠️  X11権限チェック失敗")
    
    return True

def test_simple_gui():
    """簡単なGUI表示テスト"""
    print("\n=== 簡単なGUI表示テスト ===")
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        print("GUI ウィンドウを表示中...")
        print("ウィンドウが表示されたら 'OK' ボタンをクリックしてください")
        
        root = tk.Tk()
        root.title("Linux GUI Test")
        root.geometry("400x300")
        
        # ラベル
        label = tk.Label(root, text="Linux GUI Test", font=("Arial", 16))
        label.pack(pady=20)
        
        # ttk ウィジェット
        ttk_label = ttk.Label(root, text="ttk.Label テスト")
        ttk_label.pack(pady=10)
        
        # システム情報表示
        info_text = f"OS: {platform.system()}\nDistribution: {platform.platform()}"
        info_label = tk.Label(root, text=info_text, font=("monospace", 10))
        info_label.pack(pady=10)
        
        # ボタン
        def on_ok():
            messagebox.showinfo("成功", "GUI表示テスト成功！")
            root.destroy()
        
        ok_button = ttk.Button(root, text="OK", command=on_ok)
        ok_button.pack(pady=20)
        
        # 自動クローズ用タイマー（10秒後）
        def auto_close():
            print("⚠️  10秒経過したため自動でクローズしました")
            root.destroy()
        
        root.after(10000, auto_close)
        
        # メインループ
        root.mainloop()
        
        print("✅ GUI表示テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ GUI表示テストエラー: {e}")
        return False

def test_treeview():
    """Treeview ウィジェットテスト"""
    print("\n=== Treeview ウィジェットテスト ===")
    try:
        import tkinter as tk
        from tkinter import ttk
        
        print("Treeview テストウィンドウを表示中...")
        
        root = tk.Tk()
        root.title("Treeview Test")
        root.geometry("600x400")
        
        # Treeview作成
        columns = ('timestamp', 'id', 'data')
        tree = ttk.Treeview(root, columns=columns, show='headings', height=10)
        
        # 列設定
        tree.heading('timestamp', text='TIMESTAMP')
        tree.heading('id', text='ID')
        tree.heading('data', text='DATA')
        
        tree.column('timestamp', width=150)
        tree.column('id', width=100)
        tree.column('data', width=300)
        
        # サンプルデータ追加
        import datetime
        for i in range(5):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            tree.insert('', 'end', values=(timestamp, f"0x{i+1:03X}", f"Linux Test Data {i+1}"))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 閉じるボタン
        def close_test():
            root.destroy()
        
        close_button = ttk.Button(root, text="閉じる", command=close_test)
        close_button.pack(pady=10)
        
        # 5秒後に自動クローズ
        root.after(5000, close_test)
        
        root.mainloop()
        
        print("✅ Treeview テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ Treeview テストエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("Linux GUI環境テストスクリプト")
    print("=" * 50)
    
    checks = [
        check_python_version,
        check_display_environment,
        check_tkinter,
        check_ttk,
        check_fonts,
        check_can_environment,
        check_permissions,
        test_simple_gui,
        test_treeview,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ チェック中にエラー: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("=== テスト結果 ===")
    
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"✅ 全てのテストが成功しました ({success_count}/{total_count})")
        print("Linux環境でCAN Chat GUIを実行できます！")
        print("\n実行方法:")
        print("  python3 can_chat_gui.py receiver  # 受信者")
        print("  python3 can_chat_gui.py sender    # 送信者")
    else:
        print(f"❌ {total_count - success_count} 個のテストが失敗しました ({success_count}/{total_count})")
        print("上記のエラーを解決してから再度実行してください")

if __name__ == "__main__":
    main()