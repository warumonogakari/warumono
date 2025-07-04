'''
猫の年齢を人間の年齢にたとえるとどのくらいになるか、テストプログラム
トリプルクオートで複文のコメントアウトができる
'''

from main.cat_old import Cat_old

def test_cat_old_01():
    assert Cat_old().age(1) == 15 #１歳は人間にたとえると 15歳

def test_cat_old_02():
    assert Cat_old().age(2) == 24 #２歳は人間にたとえると 24歳

def test_cat_old_03():
    assert Cat_old().age(0.5) == 7.5 # 半年だと、7.5歳

def test_cat_old_04():
    assert Cat_old().age(13) == 68 # はちみつさん

def test_cat_old_05():
    assert Cat_old().age(8) == 48 # カステラさん

def test_cat_old_06():
    assert Cat_old().age(3) == 28 # しゅくれくん

def test_display_versions():
    import pytest
    import sys
    print(f"\nPytest Version: {pytest.__version__}")
    print(f"Python Version: {sys.version}")
    assert True  # This test always passes
