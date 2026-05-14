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

def build_calendar_html(year, month, today, selected_date, completions, tasks):
    task_map = {t["id"]: t["name"] for t in tasks}
    cal = calendar.monthcalendar(year, month)
    day_colors = ["#f0f0f0"] * 5 + ["#3498db", "#e74c3c"]

    header_cells = ""
    for label, color in zip(WEEKDAYS, day_colors):
        header_cells += (
            f'<th style="color:{color};font-size:16px;font-weight:bold;'
            f'text-align:center;padding:8px 2px;border-bottom:1px solid #333;">'
            f'{label}</th>'
        )

    rows_html = ""
    for week in cal:
        row = "<tr>"
        for i, day in enumerate(week):
            if day == 0:
                row += '<td style="padding:4px;"></td>'
                continue

            day_str = f"{year}-{month:02d}-{day:02d}"
            cell_date = date(year, month, day)
            is_today = cell_date == today
            is_selected = cell_date == selected_date

            done_ids = completions.get(day_str, [])
            done_names = [task_map[tid] for tid in done_ids if tid in task_map]
            scheduled_names = [
                t["name"] for t in tasks
                if t.get("recurrence")
                and is_task_scheduled_for(t, cell_date)
                and t["id"] not in done_ids
            ]

            color = day_colors[i]

            if is_selected and is_today:
                cell_bg = "background:#3a3a10;border:2px solid #7c3aed;border-radius:8px;"
            elif is_selected:
                cell_bg = "background:#1e1a2e;border:2px solid #7c3aed;border-radius:8px;"
            elif is_today:
                cell_bg = "background:#2a2a1a;border-radius:8px;"
            else:
                cell_bg = "border-radius:8px;"

            day_fw = "bold" if (is_today or is_selected) else "normal"

            badge = ""
            if done_names:
                badge = (
                    f'<span style="background:#2ecc71;color:#000;border-radius:8px;'
                    f'padding:0 5px;font-size:11px;font-weight:bold;margin-left:2px">'
                    f'{len(done_names)}</span>'
                )

            tasks_html = ""
            for name in done_names[:2]:
                tasks_html += (
                    f'<div style="font-size:11px;color:#2ecc71;overflow:hidden;'
                    f'text-overflow:ellipsis;white-space:nowrap;line-height:1.4">'
                    f'✓{name}</div>'
                )
            for name in scheduled_names[:2]:
                tasks_html += (
                    f'<div style="font-size:11px;color:#e74c3c;overflow:hidden;'
                    f'text-overflow:ellipsis;white-space:nowrap;line-height:1.4">'
                    f'○{name}</div>'
                )

            row += (
                f'<td style="padding:3px 2px;vertical-align:top;min-width:0;cursor:pointer;">'
                f'<a href="?date={day_str}" style="text-decoration:none;display:block;">'
                f'<div style="{cell_bg}padding:4px;">'
                f'<span style="color:{color};font-size:18px;font-weight:{day_fw}">{day}</span>{badge}'
                f'{tasks_html}'
                f'</div></a></td>'
            )
        row += "</tr>"
        rows_html += row

    return (
        f'<table style="width:100%;border-collapse:collapse;table-layout:fixed;">'
        f'<thead><tr>{header_cells}</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table>'
    )

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

@media (max-width: 768px) {
    .stButton > button { min-height: 56px; font-size: 17px; }
    h1 { font-size: 1.4rem !important; }
    h3 { font-size: 1.1rem !important; }
    .stCheckbox label { font-size: 18px !important; }
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
    st.session_state.view = "✅ タスク一覧"

# カレンダーの日付リンクをタップしたとき（?date=YYYY-MM-DD）
raw_date = st.query_params.get("date", "")
if raw_date:
    try:
        sel = date.fromisoformat(raw_date)
        st.session_state.cal_selected = sel
        st.session_state.cal_year = sel.year
        st.session_state.cal_month = sel.month
        st.session_state.view = "📅 カレンダー"
        st.query_params.clear()
        st.rerun()
    except Exception:
        pass

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
    "ナビゲーション",
    NAV_OPTIONS,
    horizontal=True,
    index=NAV_OPTIONS.index(st.session_state.view),
    label_visibility="collapsed",
)
st.session_state.view = view

# ────── タスク一覧 ──────────────────────────────────────────────────────────────

if view == "✅ タスク一覧":
    today = date.today()
    today_str = str(today)
    today_done = set(completions.get(today_str, []))

    today_tasks = [t for t in tasks if is_task_scheduled_for(t, today)]
    other_tasks = [t for t in tasks if not is_task_scheduled_for(t, today)]

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

# ────── カレンダー ──────────────────────────────────────────────────────────────

else:
    today = date.today()
    task_map = {t["id"]: t["name"] for t in tasks}

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

    cal_html = build_calendar_html(
        st.session_state.cal_year,
        st.session_state.cal_month,
        today,
        st.session_state.cal_selected,
        completions,
        tasks,
    )
    st.markdown(cal_html, unsafe_allow_html=True)

    st.divider()
    selected_date = st.session_state.cal_selected
    sel_str = str(selected_date)
    sel_done_ids = completions.get(sel_str, [])
    sel_done_names = [task_map[tid] for tid in sel_done_ids if tid in task_map]
    sel_scheduled = [
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
            st.markdown(
                f'<div style="color:#e74c3c;font-size:16px">○ {name}</div>',
                unsafe_allow_html=True,
            )
    if sel_done_names:
        st.markdown("**🟢 達成**")
        for name in sel_done_names:
            st.markdown(
                f'<div style="color:#2ecc71;font-size:16px">✅ {name}</div>',
                unsafe_allow_html=True,
            )
    if not sel_done_names and not sel_scheduled:
        st.caption("この日のタスクはありません。")
