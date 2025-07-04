# 診断用スクリプト作成: debug_import.py
import sys
import os

print("=== Import Debug ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")
print("\nPython path:")
for i, path in enumerate(sys.path):
     print(f"  {i}: {path}")

print("\nFiles in current directory:")
for file in os.listdir('.'):
     if file.endswith('.py'):
         print(f"  📄 {file}")

print("\n=== Import Test ===")
try:
     import can_core
     print("✅ can_core imported successfully")
     print(f"📍 can_core file: {can_core.__file__}")
except ImportError as e:
     print(f"❌ can_core import failed: {e}")
except Exception as e:
     print(f"❌ Other error: {e}")
    