from main.cat_old import Cat_old

def test_cat_old_01():
    assert Cat_old().age(1) == 15

def test_cat_old_02():
    assert Cat_old().age(2) == 24

def test_cat_old_03():
    assert Cat_old().age(0.5) == 7.5

def test_cat_old_04():
    assert Cat_old().age(13) == 68

def test_cat_old_05():
    assert Cat_old().age(8) == 48

def test_cat_old_06():
    assert Cat_old().age(3) == 28

