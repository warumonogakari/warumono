ホテル空室検索を実行します。

## 引数
$ARGUMENTS

## 処理手順

1. 引数を確認する
   - 引数が2つ（場所・日付）の場合: そのまま使用
   - 引数が0個の場合: 前回の条件で再検索（スクリプトが last_search.json から読み込む）
   - 上記以外: エラーを表示して終了
     ```
     エラー: 引数が正しくありません。
     使用方法: /hotel <場所> <YYYY/M/D>  # 新規検索
              /hotel                    # 前回と同じ条件で再検索
     例: /hotel 新宿 2026/4/11
     ```

2. 以下のコマンドを実行する:
   - 引数あり: `uv run python /Users/katouhiroshi/warumono/claude_prjects/hotel/hotel_search.py <場所> <日付>`
   - 引数なし: `uv run python /Users/katouhiroshi/warumono/claude_prjects/hotel/hotel_search.py`

3. 実行結果をそのまま表示する

4. [NEW] が付いているホテルがあれば「新たに空きが出たホテル」として強調して案内する

## 仕様（参考）
- 検索条件: 1泊・男性1名・20,000円以内・カプセルホテル不可
- 検索順: じゃらん → Booking.com → 楽天トラベル（結果が出たら打ち切り）
- 前回との比較: 同じ場所・日付の直前の結果と比較し、新規ホテルに [NEW] を付与
- 結果保存先: /Users/katouhiroshi/warumono/claude_prjects/hotel/results/
