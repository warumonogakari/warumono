# /confengine — ConfEngineへプロポーザル下書きを投入する

引数: プロポーザルmdのパスと、カンファレンスのslug（例: `scrummatsuri-2026`）。どちらか不明なら最初に確認する。

## 原則（必ず守る）

- **「Submit Proposal」は絶対に押さない。押すのはHiroshiさんだけ。** 自動化してよいのは「Save as Draft」まで。
- ConfEngineはWebFetchだと403を返す。必ずPlaywright実ブラウザ（mcp__playwright__*）を使う。
- 投稿フォームはログイン必須。`/login?requested_url=...` に飛ばされたら、Playwrightのブラウザ画面でHiroshiさんにログインしてもらい、完了の連絡を待ってから再開する。
- 本文の転記はモデルが手打ちせず、スクリプトの出力JSONからコピーする（転記ミス防止）。

## 手順

1. **フィールド生成**（決定的変換）:
   ```
   python3 /Users/katouhiroshi/warumono/claude_prjects/slides/confengine_fields.py <プロポーザル.md> <scratchpad>/confengine_fields.json
   ```
   - 空フィールド警告が出たらmdのセクション見出しを確認する。
   - mdの想定構成: `## Title` / `## Target Audience` / `## Learning Outcome` / `## Prerequisites for Attendees` / `## Abstract` / `## Outline...` / `## 参考文献`（この形式は `slides/` 配下のプロポーザルの標準）。
   - スクリプトが `**` `*` を除去し、参考文献をOutline末尾に連結する。

2. **フォームを開く**: `browser_navigate` → `https://confengine.com/conferences/<slug>/proposal/new`

3. **選択肢を列挙してHiroshiさんに確認**（Theme / Session Type / Duration / Level）。`browser_evaluate`:
   ```js
   () => { const r = {}; document.querySelectorAll('select').forEach(s => { r[s.id || s.name] = [...s.options].map(o => o.textContent.trim()); }); return r; }
   ```
   - **DurationはSession Typeに連動して変わる**（例: Talk→20/45、Keynote→60）。Type選択後に再列挙する。

4. **選択の設定**:
   - Theme / Session Type / Level はカスタムドロップダウン: 表示テキストボックスをクリック→スナップショットで選択肢のrefを取得→クリック。
   - Durationはネイティブselect: `browser_select_option`（セレクタ `#inputDuration`）。

5. **プレーン入力欄**を `browser_type` で埋める:
   - Title: role=textbox name="Title of the session"
   - Target Audience: role=textbox name="Who should attend this session?"（改行はそのまま入る）

6. **リッチテキスト欄（TinyMCE）のIDを列挙**:
   ```js
   () => (typeof tinymce !== 'undefined' && tinymce.get) ? tinymce.get().map(e => e.id) : 'no tinymce'
   ```
   既知のマッピング（2026-07時点）: `inputAbstract`=Abstract / `inputPrerequisite`=Prerequisites / `inputProcess`=Outline/Structure / `inputLearningOutcome`=Learning Outcome。IDが違ったらDOM順（Abstract→Prerequisites→Outline→Learning Outcome）で対応づけ、投入後にスナップショットで実際の見出しと突き合わせる。

7. **各欄へ投入**（1欄ずつ `browser_evaluate`。`<HTML>` はJSONから正確にコピー。バッククォートと `${` が本文に無いことを先に確認）:
   ```js
   () => { const ed = tinymce.get('<ID>'); ed.setContent(`<HTML>`); ed.save(); ed.fire('change'); return ed.getContent({format:'text'}).length; }
   ```
   返り値の文字数を控えて報告に使う。

8. **「Save as Draft」をクリック**。成功メッセージ `Successfully saved your draft proposal.` とドラフトURL（`/proposal/<番号>`）を確認する。

9. **報告**: ドラフトURL／各フィールドの文字数／**残る手動項目**を必ず列挙——Levelの最終判断、Slides・Video・Links・Tags（Hiroshiさんしか埋められない）、Outlineの時間配分（ConfEngine公式ガイダンスは time-wise breakup を要求）、そしてSubmit本番。

## 既知の落とし穴

- markdown記法（`**` `*` `#` など）はConfEngineでは効かない。装飾はHTML（h3/ul/li/p）で入れる。
- 参考文献の専用欄は無い → Outline末尾に入れる（スクリプトが自動でやる）。
- ConfEngine側のUI更新でエディタIDやselect名が変わりうる。手順3と6の「列挙→確認」を省略しない。
- 作業後、カレントディレクトリに `.playwright-mcp/`（スナップショット類）が残る。セッション終了時の片付け候補として報告する。

## 実績

- 2026-07-04: scrummatsuri-2026 に draft 50513 を投入（この手順の初出。モデル: Fable 5）。
