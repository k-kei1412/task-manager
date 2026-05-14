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
st.title("📋 タスク管理アプリ")

data = load_data()
tasks = data["tasks"]
completions = data["completions"]

# ── サイドバー：タスク追加 ──────────────────────────────────────────────────────
# ※ toggle は form の外に置かないと再描画されないため、フォームを使わない設計

with st.sidebar:
    st.header("➕ タスクを追加")

    task_name = st.text_input("タスク名", placeholder="例：レポートを書く", key="inp_name")
    task_category = st.selectbox("カテゴリ", ["勉強", "研究", "生活", "その他"], key="inp_cat")
    use_recurrence = st.toggle("毎週繰り返す", key="inp_recur")

    if use_recurrence:
        selected_labels = st.multiselect(
            "繰り返す曜日を選択",
            options=WEEKDAYS,
            key="inp_days",
        )
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
            # 入力フィールドをリセット
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

# ── メインエリア：タブ ──────────────────────────────────────────────────────────

tab_tasks, tab_calendar = st.tabs(["✅ タスク一覧", "📅 カレンダー"])

# ────── タスク一覧タブ ──────────────────────────────────────────────────────────

with tab_tasks:
    today = date.today()
    today_str = str(today)
    today_done = set(completions.get(today_str, []))

    today_tasks = [t for t in tasks if is_task_scheduled_for(t, today)]
    other_tasks = [t for t in tasks if not is_task_scheduled_for(t, today)]

    if not tasks:
        st.info("タスクがありません。サイドバーからタスクを追加してください。")
    else:
        def render_task_row(task):
            col1, col2 = st.columns([5, 2])
            with col1:
                is_done = task["id"] in today_done
                label = f"~~{task['name']}~~" if is_done else task["name"]
                checked = st.checkbox(label, value=is_done, key=f"chk_{task['id']}")
                rec = recurrence_label(task.get("recurrence", []))
                if rec:
                    st.caption(f"🔁 毎週 {rec}")
                if checked != is_done:
                    if checked:
                        today_done.add(task["id"])
                    else:
                        today_done.discard(task["id"])
                    completions[today_str] = list(today_done)
                    save_data(data)
                    st.rerun()
            with col2:
                if task.get("due"):
                    due = date.fromisoformat(task["due"])
                    days_left = (due - today).days
                    if days_left < 0:
                        st.error(f"期限切れ")
                    elif days_left == 0:
                        st.warning("今日が期限！")
                    elif days_left <= 3:
                        st.warning(f"あと {days_left} 日")
                    else:
                        st.caption(f"期限: {task['due']}")

        st.subheader(f"📅 今日のタスク（{WEEKDAYS[today.weekday()]}曜日）")
        if today_tasks:
            categories = sorted(set(t["category"] for t in today_tasks))
            for cat in categories:
                st.markdown(f"**📁 {cat}**")
                for task in [t for t in today_tasks if t["category"] == cat]:
                    render_task_row(task)
        else:
            st.caption("今日のタスクはありません")

        st.divider()
        done_count = len([t for t in today_tasks if t["id"] in today_done])
        total_today = len(today_tasks)
        pct = done_count / total_today if total_today > 0 else 0
        st.metric("今日の進捗", f"{done_count} / {total_today} 完了")
        st.progress(pct)

        if other_tasks:
            with st.expander("📋 他の曜日のタスクを見る"):
                for task in other_tasks:
                    rec = recurrence_label(task.get("recurrence", []))
                    st.markdown(f"- {task['name']}　🔁 *毎週 {rec}*" if rec else f"- {task['name']}")

# ────── カレンダータブ ──────────────────────────────────────────────────────────

with tab_calendar:
    today = date.today()

    if "cal_year" not in st.session_state:
        st.session_state.cal_year = today.year
    if "cal_month" not in st.session_state:
        st.session_state.cal_month = today.month

    col_prev, col_month, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀", use_container_width=True):
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
        if st.button("▶", use_container_width=True):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.rerun()

    year = st.session_state.cal_year
    month = st.session_state.cal_month
    cal = calendar.monthcalendar(year, month)
    task_map = {t["id"]: t["name"] for t in tasks}

    header_cols = st.columns(7)
    for i, label in enumerate(WEEKDAYS):
        color = "#e74c3c" if i == 6 else ("#3498db" if i == 5 else "#f0f0f0")
        header_cols[i].markdown(
            f"<div style='text-align:center;font-weight:bold;color:{color}'>{label}</div>",
            unsafe_allow_html=True,
        )

    for week in cal:
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            with week_cols[i]:
                if day == 0:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    continue

                day_str = f"{year}-{month:02d}-{day:02d}"
                cell_date = date(year, month, day)
                is_today = cell_date == today

                done_ids = completions.get(day_str, [])
                done_names = [task_map[tid] for tid in done_ids if tid in task_map]
                scheduled_names = [
                    t["name"] for t in tasks
                    if t.get("recurrence")
                    and is_task_scheduled_for(t, cell_date)
                    and t["id"] not in done_ids
                ]

                day_color = "#e74c3c" if i == 6 else ("#3498db" if i == 5 else "#f0f0f0")
                bg = "background-color:#2a2a1a;border-radius:6px;padding:4px;" if is_today else "padding:4px;"
                badge = f'<span style="background:#2ecc71;color:white;border-radius:10px;padding:1px 6px;font-size:11px">{len(done_names)}</span>' if done_names else ""

                st.markdown(
                    f"<div style='{bg}'>"
                    f"<span style='color:{day_color};font-weight:{'bold' if is_today else 'normal'}'>{day}</span> {badge}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                for name in done_names:
                    st.markdown(
                        f"<div style='font-size:10px;color:#2ecc71;overflow:hidden;text-overflow:ellipsis;white-space:nowrap' title='{name}'>✓ {name}</div>",
                        unsafe_allow_html=True,
                    )
                for name in scheduled_names:
                    st.markdown(
                        f"<div style='font-size:10px;color:#666;overflow:hidden;text-overflow:ellipsis;white-space:nowrap' title='{name}'>○ {name}</div>",
                        unsafe_allow_html=True,
                    )

    st.divider()
    st.subheader("📋 日別 タスク詳細")
    selected_day = st.date_input("日付を選択", value=today, key="detail_date")
    sel_str = str(selected_day)
    sel_done_ids = completions.get(sel_str, [])
    sel_done_names = [task_map[tid] for tid in sel_done_ids if tid in task_map]
    sel_scheduled = [
        t["name"] for t in tasks
        if t.get("recurrence")
        and is_task_scheduled_for(t, selected_day)
        and t["id"] not in sel_done_ids
    ]

    if sel_done_names:
        st.markdown("**完了したタスク**")
        for name in sel_done_names:
            st.markdown(f"- ✅ {name}")
    if sel_scheduled:
        st.markdown("**予定（未完了）**")
        for name in sel_scheduled:
            st.markdown(f"- ○ {name}")
    if not sel_done_names and not sel_scheduled:
        st.caption("この日のタスクはありません。")
