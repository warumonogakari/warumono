# CAN通信サンプルデモ

## 概要
PythonのSocket CANを使った送受信システムをテスト駆動開発（TDD）で構築するプロジェクト

### 用語
CAN .. Controller Area Network
vcan .. virtual CAN 仮想ネットワークインターフェース(Kernel 内のloop back使用)

## ファイル構成

```
can_demo/
├── can_core.py           # メインの CAN通信クラス
├── test_can_sender.py    # 送信側のテスト
├── pytest.ini           # pytest設定
├── test_can_receiver.py  # 受信側のテスト (まだ)  
├── test_integration.py   # 統合テスト（実際のvcan環境）（まだ）
├── setup_vcan.sh         # vcan環境セットアップスクリプト（まだ）
├── run_tests.py          # テスト実行スクリプト（まだ）
└── readme_can_demo.md         # このファイル
```

## クイックスタート

### 1. 環境準備

```bash
# 必要パッケージのインストール
pip install pytest pytest-cov

# vcan環境セットアップ（Linuxのみ）
chmod +x setup_vcan.sh
bash setup_vcan.sh
```

### 2. テスト実行

```bash
# 全テスト実行
python run_tests.py

# 単体テストのみ（モック使用、ハードウェア不要）
python run_tests.py --unit

# 統合テスト（vcan環境必要）
python run_tests.py --integration

# カバレッジ付きテスト
python run_tests.py --unit --coverage
```

## 🧪 TDD開発フロー

### Phase 1: Red（失敗するテストを書く）

```bash
# 新機能のテストを先に書く
# 例: test_can_sender.py に新しいテストメソッドを追加

def test_new_feature(self):
    # まだ実装されていない機能のテスト
    sender = CANSender()
    result = sender.new_feature()
    assert result == expected_value
```

### Phase 2: Green（最小限の実装で通す）

```bash
# can_core.py に最小限の実装を追加
class CANSender:
    def new_feature(self):
        return expected_value  # 最小限の実装
```

### Phase 3: Refactor（リファクタリング）

```bash
# テストが通ることを確認しながらコードを改善
python run_tests.py --unit

# リファクタリング後もテストが通ることを確認
```

## 📊 テスト戦略

### 単体テスト（Unit Tests）
- **ファイル**: `test_can_sender.py`, `test_can_receiver.py`
- **特徴**: モックを使用、ハードウェア不要
- **テスト内容**:
  - クラスの初期化
  - メッセージの送受信ロジック
  - エラーハンドリング
  - データ変換

```bash
# 単体テストのみ実行
python run_tests.py --unit --verbose
```

### 統合テスト（Integration Tests）
- **ファイル**: `test_integration.py`
- **特徴**: 実際のvcan環境を使用
- **テスト内容**:
  - 実際の送受信
  - 複数メッセージ処理
  - 同期通信
  - パフォーマンス

```bash
# 統合テストのみ実行
python run_tests.py --integration --verbose
```

## 🔧 開発ワークフロー例

### 新機能追加の例: メッセージフィルタリング機能

#### 1. テストファースト（Red）

```python
# test_can_receiver.py に追加
def test_message_filtering(self):
    receiver = CANReceiver('vcan0')

    # フィルター設定: ID 0x100-0x1FF のみ受信
    receiver.set_id_filter(0x100, 0x1FF)

    # テストメッセージ（フィルター内外の混在）
    test_messages = [
        CANMessage(0x150, b"Accept"),   # フィルター内
        CANMessage(0x250, b"Reject"),   # フィルター外
    ]

    # 受信テスト
    filtered_messages = receiver.apply_filter(test_messages)

    assert len(filtered_messages) == 1
    assert filtered_messages[0].actual_id == 0x150
```

#### 2. 最小実装（Green）

```python
# can_core.py の CANReceiver クラスに追加
class CANReceiver:
    def __init__(self, interface='vcan0'):
        # 既存の初期化...
        self.id_filter_min = None
        self.id_filter_max = None

    def set_id_filter(self, min_id, max_id):
        self.id_filter_min = min_id
        self.id_filter_max = max_id

    def apply_filter(self, messages):
        if self.id_filter_min is None:
            return messages

        return [msg for msg in messages
                if self.id_filter_min <= msg.actual_id <= self.id_filter_max]
```

#### 3. テスト実行

```bash
# 新機能のテストが通ることを確認
python run_tests.py --unit -f test_can_receiver

# 既存テストが壊れていないことを確認
python run_tests.py --unit
```

#### 4. リファクタリング

```python
# より柔軟なフィルター設計に改善
from typing import List, Callable

class CANReceiver:
    def __init__(self, interface='vcan0'):
        # 既存の初期化...
        self.message_filters: List[Callable[[CANMessage], bool]] = []

    def add_id_filter(self, min_id: int, max_id: int):
        """ID範囲フィルターを追加"""
        def id_filter(msg: CANMessage) -> bool:
            return min_id <= msg.actual_id <= max_id
        self.message_filters.append(id_filter)

    def add_data_filter(self, pattern: bytes):
        """データパターンフィルターを追加"""
        def data_filter(msg: CANMessage) -> bool:
            return pattern in msg.data
        self.message_filters.append(data_filter)

    def apply_filters(self, messages: List[CANMessage]) -> List[CANMessage]:
        """全フィルターを適用"""
        filtered = messages
        for filter_func in self.message_filters:
            filtered = [msg for msg in filtered if filter_func(msg)]
        return filtered
```

#### 5. 統合テスト追加

```python
# test_integration.py に実際の環境でのテストを追加
@skip_integration
def test_real_message_filtering(self, vcan_environment):
    sender = CANSender('vcan0')
    receiver = CANReceiver('vcan0')

    try:
        sender.connect()
        receiver.connect()

        # フィルター設定
        receiver.add_id_filter(0x100, 0x1FF)

        # 様々なIDでメッセージ送信
        test_cases = [
            (0x150, b"Should receive"),
            (0x250, b"Should filter out"),
            (0x180, b"Should receive"),
        ]

        for can_id, data in test_cases:
            sender.send(can_id, data)

        # 受信とフィルタリング
        received = []
        for _ in range(len(test_cases)):
            msg = receiver.receive_once(timeout=1.0)
            if msg:
                received.append(msg)

        filtered = receiver.apply_filters(received)

        # フィルター結果確認
        assert len(filtered) == 2  # 0x150, 0x180 のみ

    finally:
        sender.disconnect()
        receiver.disconnect()
```

## 📈 コードカバレッジ

```bash
# カバレッジ付きテスト実行
python run_tests.py --unit --coverage

# HTMLレポート確認
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**カバレッジ目標**:
- 単体テスト: 90%以上
- 統合テスト込み: 95%以上

## 🐛 デバッグとトラブルシューティング

### よくある問題

#### 1. vcan環境エラー
```bash
# エラー: vcan0 が見つからない
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

#### 2. 権限エラー
```bash
# 現在のユーザーをdialoutグループに追加
sudo usermod -a -G dialout $USER
# ログアウト/ログインが必要
```

#### 3. テストの分離問題
```python
# setUp/tearDown でクリーンな状態を保つ
class TestCANReceiver:
    def setup_method(self):
        self.receiver = CANReceiver('vcan0')

    def teardown_method(self):
        if self.receiver:
            self.receiver.disconnect()
```

### デバッグテクニック

#### 1. 詳細ログ出力
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# テスト中のメッセージをログ出力
def test_with_logging(self):
    logging.debug(f"Sending message: {message}")
    # テストコード...
```

#### 2. 段階的テスト
```bash
# 特定のテストメソッドのみ実行
python -m pytest test_can_sender.py::TestCANSender::test_send_message -v
```

#### 3. ブレークポイント
```python
def test_debug_point(self):
    sender = CANSender('vcan0')
    import pdb; pdb.set_trace()  # デバッガ起動
    result = sender.send(0x123, b"debug")
```

## 🚀 継続的改善

### 1. 新機能追加のチェックリスト
- [ ] テストファースト（Red）
- [ ] 最小実装（Green）
- [ ] リファクタリング
- [ ] 単体テスト追加
- [ ] 統合テスト追加
- [ ] ドキュメント更新

### 2. 品質指標
- テスト実行時間: 単体テスト < 10秒
- カバレッジ: > 90%
- 統合テスト成功率: > 95%

### 3. 定期的なタスク
```bash
# 毎日の品質チェック
python run_tests.py --unit --coverage
python run_tests.py --integration

# 週次のパフォーマンスチェック
python run_tests.py --performance
```

## 📚 参考資料

- [pytest ドキュメント](https://docs.pytest.org/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Linux CAN](https://www.kernel.org/doc/Documentation/networking/can.txt)
- [TDD実践ガイド](https://martinfowler.com/bliki/TestDrivenDevelopment.html)

---

**Happy Testing! 🧪✨**
