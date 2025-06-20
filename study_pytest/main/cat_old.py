class Cat_old:
    def age(self, age):
        """
        猫の年齢を人間の年齢に換算します。
        Args:
            age (int): 猫の年齢
        Returns:
            int: 人間の年齢に換算した値
        """
        if age < 0:
            return -1
        
        human_age = 0  # age()メソッド内だけで使用する変数
        match age:
            case _ if age <= 1:
                human_age = age * 15
            case _ if age <= 2:
                human_age = 15 + (age - 1) * 9
            case _:
                human_age = 24 + (age - 2) * 4
        return human_age

# 使用例:
# cat = Cat_old()
# human_age = cat.age(2)  # 2歳の猫の人間年齢を計算
# print(human_age)  # 結果を表示
