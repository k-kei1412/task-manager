import streamlit as st
import json
import os
import calendar
from datetime import date, datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tasks": [], "completions": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def recurrence_label(recurrence):
    if not recurrence:
        return ""
    return "・".join(WEEKDAYS[d] for d in sorted(recurrence))

def is_task_scheduled_for(task, target_date):
    recurrence = task.get("recurrence", [])
    if not recurrence:
        return True
    return target_date.weekday() in recurrence

# ── ページ設定 ──────────────────────────────────────────────────────────────────

st.set_page_config(page_title="タスク管理", page_icon="✅", layout="wide")

st.markdown("""
<style>
.stApp { font-size: 16px; }
.stButton > button {
    min-height: 48px;
    font-size: 16px;
    border-radius: 10px;
}
.stCheckbox label {
    font-size: 17px !important;
    line-height: 1.6 !important;
}
.stTextInput input { font-size: 16px !important; }
.stMultiSelect div[data-baseweb] { font-size: 15px !important; }

/* ─ カレンダー: モバイルでも7列を維持 ─ */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 3px !important;
}
[data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
    flex: 1 1 0% !important;
    overflow: hidden !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
    min-width: 0 !important;
    padding: 4px 2px !important;
    border-radius: 6px !important;
    line-height: 1.3 !important;
    word-break: break-word !important;
}

@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] {
        gap: 2px !important;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
        font-size: 11px !important;
        min-height: 44px !important;
        padding: 2px 1px !important;
    }
    h1 { font-size: 1.4rem !important; }
    h3 { font-size: 1.1rem !important; }
    .stCheckbox label { font-size: 18px !important; }
    .stButton > button { min-height: 56px; font-size: 17px; }
}
</style>
""", unsafe_allow_html=True)

st.title("📋 タスク管理アプリ")

data = load_data()
tasks = data["tasks"]
completions = data["completions"]

# ── セッション初期化 ────────────────────────────────────────────────────────────

if "cal_selected" not in st.session_state:
    st.session_state.cal_selected = date.today()
if "cal_year" not in st.session_state:
    st.session_state.cal_year = date.today().year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = date.today().month
if "view" not in st.session_state:
    st.session_state["view"] = "✅ タスク一覧"

# ── サイドバー ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("➕ タスクを追加")

    task_name = st.text_input("タスク名", placeholder="例：レポートを書く", key="inp_name")
    task_category = st.selectbox("カテゴリ", ["勉強", "研究", "生活", "その他"], key="inp_cat")
    use_recurrence = st.toggle("毎週繰り返す", key="inp_recur")

    if use_recurrence:
        selected_labels = st.multiselect("繰り返す曜日を選択", options=WEEKDAYS, key="inp_days")
        recurrence = [WEEKDAYS.index(d) for d in selected_labels]
        task_due = None
    else:
        task_due = st.date_input("期限（任意）", value=None, key="inp_due")
        recurrence = []

    if st.button("追加", use_container_width=True, type="primary"):
        if not task_name.strip():
            st.error("タスク名を入力してください")
        elif use_recurrence and not recurrence:
            st.error("曜日を1つ以上選んでください")
        else:
            new_task = {
                "id": str(int(datetime.now().timestamp() * 1000)),
                "name": task_name.strip(),
                "category": task_category,
                "due": str(task_due) if task_due else None,
                "recurrence": recurrence,
                "created": str(date.today()),
            }
            tasks.append(new_task)
            save_data(data)
            for k in ["inp_name", "inp_cat", "inp_recur", "inp_days", "inp_due"]:
                st.session_state.pop(k, None)
            st.success(f"「{new_task['name']}」を追加しました！")
            st.rerun()

    st.divider()
    st.header("🗑️ タスク削除")
    if tasks:
        task_to_delete = st.selectbox(
            "削除するタスクを選択",
            options=[t["id"] for t in tasks],
            format_func=lambda tid: next((t["name"] for t in tasks if t["id"] == tid), tid),
        )
        if st.button("削除", use_container_width=True, type="secondary"):
            tasks[:] = [t for t in tasks if t["id"] != task_to_delete]
            for day in completions:
                if task_to_delete in completions[day]:
                    completions[day].remove(task_to_delete)
            save_data(data)
            st.rerun()
    else:
        st.caption("タスクがありません")

# ── ナビゲーション ──────────────────────────────────────────────────────────────

NAV_OPTIONS = ["✅ タスク一覧", "📅 カレンダー"]
view = st.radio(
    "nav",
    NAV_OPTIONS,
    horizontal=True,
    key="view",
    label_visibility="collapsed",
)

# ────── タスク一覧 ──────────────────────────────────────────────────────────────

if view == "✅ タスク一覧":
    today = date.today()
    today_str = str(today)
    today_done = set(completions.get(today_str, []))
    today_tasks = [t for t in tasks if is_task_scheduled_for(t, today)]
    other_tasks  = [t for t in tasks if not is_task_scheduled_for(t, today)]

    if not tasks:
        st.info("タスクがありません。サイドバーからタスクを追加してください。")
    else:
        def render_task_row(task):
            task_id = task["id"]
            is_done = task_id in today_done
            editing = st.session_state.get(f"editing_{task_id}", False)
            rec = recurrence_label(task.get("recurrence", []))

            col1, col2 = st.columns([5, 2])
            with col1:
                if editing:
                    new_name = st.text_input(
                        "タスク名を変更",
                        value=task["name"],
                        key=f"edit_input_{task_id}",
                    )
                    c_save, c_cancel = st.columns(2)
                    with c_save:
                        if st.button("保存", key=f"save_{task_id}", type="primary", use_container_width=True):
                            if new_name.strip():
                                task["name"] = new_name.strip()
                                save_data(data)
                            st.session_state.pop(f"editing_{task_id}", None)
                            st.rerun()
                    with c_cancel:
                        if st.button("キャンセル", key=f"cancel_{task_id}", use_container_width=True):
                            st.session_state.pop(f"editing_{task_id}", None)
                            st.rerun()
                else:
                    icon = "✅" if is_done else "○"
                    if st.button(
                        f"{icon}  {task['name']}",
                        key=f"name_btn_{task_id}",
                        use_container_width=True,
                        help="クリックして名前を変更",
                    ):
                        st.session_state[f"editing_{task_id}"] = True
                        st.rerun()
                    if rec:
                        st.caption(f"🔁 毎週 {rec}")
                    checked = st.checkbox(
                        "完了" if not is_done else "取り消し",
                        value=is_done,
                        key=f"chk_{task_id}",
                    )
                    if checked != is_done:
                        if checked:
                            today_done.add(task_id)
                        else:
                            today_done.discard(task_id)
                        completions[today_str] = list(today_done)
                        save_data(data)
                        st.rerun()
            with col2:
                if task.get("due") and not editing:
                    due = date.fromisoformat(task["due"])
                    days_left = (due - today).days
                    if days_left < 0:
                        st.error("期限切れ")
                    elif days_left == 0:
                        st.warning("今日が期限！")
                    elif days_left <= 3:
                        st.warning(f"あと {days_left} 日")
                    else:
                        st.caption(f"期限: {task['due']}")

        st.subheader(f"📅 今日のタスク（{WEEKDAYS[today.weekday()]}曜日）")
        if today_tasks:
            incomplete = [t for t in today_tasks if t["id"] not in today_done]
            complete   = [t for t in today_tasks if t["id"] in today_done]
            if incomplete:
                st.markdown("#### 🔴 未達成")
                for cat in sorted(set(t["category"] for t in incomplete)):
                    st.markdown(f"**📁 {cat}**")
                    for task in [t for t in incomplete if t["category"] == cat]:
                        render_task_row(task)
            if complete:
                st.markdown("#### 🟢 達成")
                for cat in sorted(set(t["category"] for t in complete)):
                    st.markdown(f"**📁 {cat}**")
                    for task in [t for t in complete if t["category"] == cat]:
                        render_task_row(task)
        else:
            st.caption("今日のタスクはありません")

        done_count  = len([t for t in today_tasks if t["id"] in today_done])
        total_today = len(today_tasks)
        pct = done_count / total_today if total_today > 0 else 0
        st.metric("今日の進捗", f"{done_count} / {total_today} 完了")
        st.progress(pct)

        if other_tasks:
            with st.expander("📋 他の曜日のタスクを見る"):
                for task in other_tasks:
                    rec = recurrence_label(task.get("recurrence", []))
                    st.markdown(f"- {task['name']}　🔁 *毎週 {rec}*" if rec else f"- {task['name']}")

# ────── カレンダー ──────────────────────────────────────────────────────────────

else:
    today = date.today()
    task_map = {t["id"]: t["name"] for t in tasks}
    day_colors = ["#f0f0f0"] * 5 + ["#3498db", "#e74c3c"]

    # 月ナビゲーション
    col_prev, col_month, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀", use_container_width=True, key="cal_prev"):
            if st.session_state.cal_month == 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.rerun()
    with col_month:
        st.markdown(
            f"<h3 style='text-align:center;margin:0'>"
            f"{st.session_state.cal_year}年 {st.session_state.cal_month}月</h3>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("▶", use_container_width=True, key="cal_next"):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.rerun()

    year  = st.session_state.cal_year
    month = st.session_state.cal_month
    cal_grid = calendar.monthcalendar(year, month)

    # 曜日ヘッダー（HTML: 色付き）
    header_html = (
        '<table style="width:100%;table-layout:fixed;border-collapse:collapse;margin-bottom:2px;">'
        '<tr>'
    )
    for label, color in zip(WEEKDAYS, day_colors):
        header_html += (
            f'<th style="color:{color};font-weight:bold;font-size:15px;'
            f'text-align:center;padding:6px 0;border-bottom:1px solid #444;">'
            f'{label}</th>'
        )
    header_html += '</tr></table>'
    st.markdown(header_html, unsafe_allow_html=True)

    # 日付グリッド（Streamlit ボタン: リロードなし）
    for week in cal_grid:
        cols = st.columns(7)
        for col, day in zip(cols, week):
            with col:
                if day == 0:
                    st.write("")
                    continue

                cell_date = date(year, month, day)
                day_str   = str(cell_date)
                is_today    = cell_date == today
                is_selected = cell_date == st.session_state.cal_selected

                done_ids    = set(completions.get(day_str, []))
                done_count  = len([tid for tid in done_ids if tid in task_map])
                sched_undone = len([
                    t for t in tasks
                    if t.get("recurrence")
                    and is_task_scheduled_for(t, cell_date)
                    and t["id"] not in done_ids
                ])

                # ラベル
                num = f"**{day}**" if is_today else str(day)
                badges = []
                if done_count:   badges.append(f"✅{done_count}")
                if sched_undone: badges.append(f"🔴{sched_undone}")
                label = num + ("\n" + " ".join(badges) if badges else "")

                if st.button(
                    label,
                    key=f"d_{year}_{month}_{day}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                ):
                    st.session_state.cal_selected = cell_date
                    st.rerun()

    # 選択日の詳細
    st.divider()
    selected_date  = st.session_state.cal_selected
    sel_str        = str(selected_date)
    sel_done_ids   = completions.get(sel_str, [])
    sel_done_names = [task_map[tid] for tid in sel_done_ids if tid in task_map]
    sel_scheduled  = [
        t["name"] for t in tasks
        if t.get("recurrence")
        and is_task_scheduled_for(t, selected_date)
        and t["id"] not in sel_done_ids
    ]

    wd = WEEKDAYS[selected_date.weekday()]
    st.subheader(f"📋 {selected_date.month}月{selected_date.day}日（{wd}）の詳細")

    if sel_scheduled:
        st.markdown("**🔴 未達成**")
        for name in sel_scheduled:
            st.markdown(f'<div style="color:#e74c3c;font-size:16px">○ {name}</div>', unsafe_allow_html=True)
    if sel_done_names:
        st.markdown("**🟢 達成**")
        for name in sel_done_names:
            st.markdown(f'<div style="color:#2ecc71;font-size:16px">✅ {name}</div>', unsafe_allow_html=True)
    if not sel_done_names and not sel_scheduled:
        st.caption("この日のタスクはありません。")
