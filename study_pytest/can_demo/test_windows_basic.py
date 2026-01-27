#!/usr/bin/env python3
"""
Windows環境でのGUI動作確認スクリプト
実行方法: python test_windows_gui.py
"""

import sys
import platform

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
        print("1. Python を python.org から再インストール")
        print("2. インストール時に 'tcl/tk and IDLE' をチェック")
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

def test_simple_gui():
    """簡単なGUI表示テスト"""
    print("\n=== 簡単なGUI表示テスト ===")
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        print("GUI ウィンドウを表示中...")
        print("ウィンドウが表示されたら 'OK' ボタンをクリックしてください")
        
        root = tk.Tk()
        root.title("Windows GUI Test")
        root.geometry("400x300")
        
        # ラベル
        label = tk.Label(root, text="Windows GUI Test", font=("Arial", 16))
        label.pack(pady=20)
        
        # ttk ウィジェット
        ttk_label = ttk.Label(root, text="ttk.Label テスト")
        ttk_label.pack(pady=10)
        
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
            tree.insert('', 'end', values=(timestamp, f"0x{i+1:03X}", f"Test Data {i+1}"))
        
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

def check_display_settings():
    """ディスプレイ設定チェック"""
    print("\n=== ディスプレイ設定チェック ===")
    try:
        import tkinter as tk
        root = tk.Tk()
        
        # 画面サイズ取得
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        print(f"画面解像度: {screen_width} x {screen_height}")
        
        # DPI設定確認
        try:
            dpi = root.winfo_fpixels('1i')
            print(f"DPI: {dpi:.0f}")
        except:
            print("DPI: 取得できません")
        
        root.destroy()
        
        if screen_width > 0 and screen_height > 0:
            print("✅ ディスプレイ設定 OK")
            return True
        else:
            print("❌ ディスプレイ設定に問題があります")
            return False
            
    except Exception as e:
        print(f"❌ ディスプレイ設定エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("Windows GUI環境テストスクリプト")
    print("=" * 50)
    
    checks = [
        check_python_version,
        check_tkinter,
        check_ttk,
        check_display_settings,
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
        print("Windows環境でCAN Chat GUIを実行できます！")
    else:
        print(f"❌ {total_count - success_count} 個のテストが失敗しました ({success_count}/{total_count})")
        print("上記のエラーを解決してから再度実行してください")

if __name__ == "__main__":
    main()