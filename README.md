# タスク管理アプリ 指示書

## 概要

Streamlit 製のタスク管理アプリ。タスクの追加・削除・完了管理とカレンダーによる進捗確認ができる。

---

## 起動方法

```
起動.bat をダブルクリック
```

または PowerShell で：

```powershell
cd "C:\Users\keisu\OneDrive\ドキュメント\Claude\task-manager"
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動で開く。

---

## ファイル構成

```
task-manager/
├── app.py              # メインアプリ
├── tasks.json          # タスクデータ（自動生成）
├── requirements.txt    # 依存ライブラリ
├── 起動.bat            # ダブルクリックで起動
└── README.md           # この指示書
```

---

## 技術スタック

- **Python** + **Streamlit** (`>= 1.35.0`)
- データ保存: `tasks.json`（JSON ファイル、DB 不要）

---

## 機能一覧

### タスク一覧タブ

- 今日のタスクを **未達成 / 達成** に分けて表示
- **タスク名をクリック → 名前を変更**（インライン編集）
- チェックボックスで **完了 / 取り消し** を切り替え
- 今日の進捗メーター（完了数 / 総数）
- 「他の曜日のタスクを見る」エクスパンダー

### カレンダータブ

- 月カレンダーをボタングリッドで表示（◀ ▶ で月移動）
- **日付ボタンをタップ → その日の詳細を表示**（画面フラッシュなし）
- 達成タスク数（✅N）・未達成タスク数（🔴N）を各日付に表示
- 今日は `**太字**` で強調
- 選択中の日は primary ハイライト

### サイドバー

- タスク追加：名前・カテゴリ・繰り返し曜日 or 期限
- タスク削除：セレクトボックスで選択して削除

---

## データ構造（tasks.json）

```json
{
  "tasks": [
    {
      "id": "1234567890",
      "name": "タスク名",
      "category": "勉強 | 研究 | 生活 | その他",
      "due": "2026-05-31",
      "recurrence": [0, 2, 4],
      "created": "2026-05-14"
    }
  ],
  "completions": {
    "2026-05-14": ["1234567890"]
  }
}
```

- `recurrence`: 繰り返す曜日のインデックス（0=月, 1=火, …, 6=日）
- `due`: 期限なしの場合は `null`
- `completions`: 日付ごとに完了したタスク ID のリスト

---

## 実装上の重要な決定事項

### カレンダーをボタン方式にした理由

`<a href>` リンクはブラウザ全体をリロードするため：
- 毎回画面が白くフラッシュする
- スマホで新規ブラウザタブが開く場合がある

→ `st.button()` に変更することで Streamlit の差分更新のみになりフラッシュなし。

### モバイルで7列を維持するCSS

Streamlit の `st.columns(7)` はデフォルトで `flex-wrap` により縦積みになることがある。
以下の CSS で強制的に7列を維持：

```css
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 3px !important;
}
[data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
    flex: 1 1 0% !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
    min-width: 0 !important;
}
```

### タブ切り替えを保持する方法

`st.radio(key="view")` で `st.session_state["view"]` に直結させる。
セッション状態を変更してから `st.rerun()` すると、ラジオボタンが正しいタブを表示する。

```python
st.session_state["view"] = "📅 カレンダー"
st.rerun()

view = st.radio("nav", NAV_OPTIONS, key="view", ...)
```

---

## 今後の拡張アイデア

- タスクの優先度設定
- 通知機能（期限アラート）
- カテゴリ別の進捗グラフ
- データのエクスポート（CSV）
