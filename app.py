import streamlit as st
import json
import random

# 🚀 Setup for wide layout
st.set_page_config(layout="wide")

# ==============================================================================
# 🎨 CENTRAL STYLE CONFIGURATION
# ==============================================================================
TEXT_COLOR = "black"  
FONT_FAMILY = "Georgia"  
STYLE_WRAPPER = f"<div style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>"

st.html(f"""
    <style>
    div[class*="st-key-btn"] button p {{ font-family: {FONT_FAMILY} !important; }}
    </style>
""")

# ==============================================================================
# 🗄️ STATE INITIALIZATION
# ==============================================================================
if "tasks" not in st.session_state: st.session_state.tasks = []
if "current_index" not in st.session_state: st.session_state.current_index = 0  
if "mode" not in st.session_state: st.session_state.mode = "adding"  
if "show_delete_dropdown" not in st.session_state: st.session_state.show_delete_dropdown = False
if "show_move_dropdowns" not in st.session_state: st.session_state.show_move_dropdowns = False
if "confirm_delete_list" not in st.session_state: st.session_state.confirm_delete_list = False
if "affirmation" not in st.session_state: st.session_state.affirmation = None

LIMIT = 500
AFFIRMATIONS = [
    "✨ Fantastic job getting that done!", "🎉 Way to cross that off your list!",
    "🚀 Outstanding momentum! Keep it going!", "⭐ Brilliant effort on this task!",
    "🎯 Crushing your goals one step at a time!", "🏆 Victory! Another item successfully completed!",
    "🌈 Spectacular execution!", "⚡ Pure efficiency! You're doing amazing!"
]

# ==============================================================================
# 💾 SIDEBAR: EXPORT / IMPORT
# ==============================================================================
with st.sidebar:
    st.markdown("### 💾 Save & Backup Data")
    if len(st.session_state.tasks) > 0:
        st.download_button("📤 Export Task List (.json)", json.dumps(st.session_state.tasks, indent=4), "my_task_list.json", "application/json", use_container_width=True)
    
    uploaded_file = st.file_uploader("📥 Import a saved Task List File", type=["json"])
    if uploaded_file is not None:
        try:
            loaded = json.load(uploaded_file)
            if isinstance(loaded, list):
                st.session_state.tasks = loaded
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ==============================================================================
# 🏗️ MAIN APP LOGIC
# ==============================================================================
if st.session_state.mode == "adding":
    st.html(f"<h1 style='color: {TEXT_COLOR}; font-family: {'Georgia'};'>Executive Function Assistant</h1>")
    left_col, right_col = st.columns([1.5, 1.2], gap="large")

    with left_col:
        st.html(f"<h3 style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>📋 Your Task List</h3>")
        with st.container(height=450, border=True):
            for i, t in enumerate(st.session_state.tasks, 1):
                st.html(f"{STYLE_WRAPPER}{i}. <b>{t['name']}</b> {f'<i>(Requires: {t['prereq']})</i>' if t.get('prereq') else ''}</div><hr style='margin: 8px 0;'>")

    with right_col:
        st.html(f"<h2 style='text-align: center; color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>Build Your List</h2>")
        st.html(f"<div style='text-align: center; padding: 6px; background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 5px; margin-bottom: 15px;'>⚠️ <b>Important:</b> Refer to sidebar to <b>Export</b> before refreshing!</div>")
        
        with st.form(key="input_form"):
            task_text = st.text_input("Task Input", placeholder="Add a new task...")
            prereq_text = st.text_input("Prerequisite Input", placeholder="What must be done first?")
            
            c1, c2, c3, c4 = st.columns(4)
            if c1.form_submit_button("Add Task"):
                if task_text.strip():
                    st.session_state.tasks.append({"name": task_text.strip(), "prereq": prereq_text.strip() if prereq_text.strip() else None})
                    st.rerun()
            if c2.form_submit_button("Move Task"):
                st.session_state.show_move_dropdowns, st.session_state.show_delete_dropdown = True, False
            if c3.form_submit_button("Delete Task"):
                st.session_state.show_delete_dropdown, st.session_state.show_move_dropdowns = True, False
            if c4.form_submit_button("Delete List" if not st.session_state.confirm_delete_list else "Confirm All"):
                if not st.session_state.confirm_delete_list: st.session_state.confirm_delete_list = True
                else: 
                    st.session_state.tasks, st.session_state.confirm_delete_list = [], False
                    st.rerun()

        if st.session_state.show_move_dropdowns:
            col_a, col_b, col_c = st.columns(3)
            from_idx = col_a.number_input("Move #", 1, len(st.session_state.tasks)) - 1
            to_idx = col_b.number_input("To #", 1, len(st.session_state.tasks)) - 1
            if col_c.button("Confirm Move"):
                task = st.session_state.tasks.pop(from_idx)
                st.session_state.tasks.insert(to_idx, task)
                st.session_state.show_move_dropdowns = False
                st.rerun()

        if st.session_state.show_delete_dropdown:
            del_idx = st.number_input("Select # to delete", 1, len(st.session_state.tasks)) - 1
            if st.button("Confirm Deletion"):
                st.session_state.tasks.pop(del_idx)
                st.session_state.show_delete_dropdown = False
                st.rerun()

        if len(st.session_state.tasks) > 0 and st.button("Start Working", use_container_width=True):
            st.session_state.mode = "working"
            st.rerun()

elif st.session_state.mode == "working":
    current_task = st.session_state.tasks[st.session_state.current_index]
    st.html(f"<h1 style='text-align: center; color: {TEXT_COLOR}; font-family: 'Georgia';'>{current_task['name']}</h1>")
    if current_task.get('prereq'): st.warning(f"⚠️ Prerequisite: **{current_task['prereq']}**")
    
    col1, col2, col3 = st.columns(3)
    if col1.button("👍 Completed"):
        st.session_state.tasks.pop(st.session_state.current_index)
        st.session_state.affirmation = random.choice(AFFIRMATIONS)
        if st.session_state.current_index >= len(st.session_state.tasks): st.session_state.current_index = 0
        st.rerun()
    if col2.button("👎 Skip"):
        st.session_state.current_index = (st.session_state.current_index + 1) % len(st.session_state.tasks)
        st.rerun()
    if col3.button("↩️ Back to List"):
        st.session_state.mode = "adding"
        st.rerun()
    
    if st.session_state.affirmation:
        st.write(st.session_state.affirmation)
        