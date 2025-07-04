# path_checker.py
import sys
import os

print("=== Python Environment Info ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

print("\n=== PATH ===")
for i, path in enumerate(os.environ.get('PATH', '').split(os.pathsep)):
     if path:  # 空文字列をスキップ
         print(f"{i:2d}: {path}")

print("\n=== Python in PATH ===")
import shutil
python_path = shutil.which('python')
pytest_path = shutil.which('pytest')
print(f"python: {python_path}")
print(f"pytest: {pytest_path}")