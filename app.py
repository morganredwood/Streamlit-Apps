import streamlit as st
import json
import random

# Initialize fallback session tracker instantly
if "tasks" not in st.session_state:
    # Pull instantly from the URL query parameter on page load before anything else renders
    saved_tasks_raw = st.query_params.get("tasks_data")
    if saved_tasks_raw:
        try:
            st.session_state.tasks = json.loads(saved_tasks_raw)
        except Exception:
            st.session_state.tasks = []
    else:
        st.session_state.tasks = []

# Title is only shown when building the list now
if "mode" in st.session_state and st.session_state.mode == "adding":
    st.title("Executive Function Assistant")

if "current_index" not in st.session_state:
    st.session_state.current_index = 0  

if "mode" not in st.session_state:
    st.session_state.mode = "adding"  

if "show_delete_dropdown" not in st.session_state:
    st.session_state.show_delete_dropdown = False

if "confirm_delete_list" not in st.session_state:
    st.session_state.confirm_delete_list = False

if "force_expand_list" not in st.session_state:
    st.session_state.force_expand_list = True

if "affirmation" not in st.session_state:
    st.session_state.affirmation = None

LIMIT = 100

AFFIRMATIONS = [
    "✨ Fantastic job getting that done!",
    "🎉 Way to cross that off your list!",
    "🚀 Outstanding momentum! Keep it going!",
    "⭐ Brilliant effort on this task!",
    "🎯 Crushing your goals one step at a time!",
    "🏆 Victory! Another item successfully completed!",
    "🌈 Spectacular execution!",
    "⚡ Pure efficiency! You're doing amazing!"
]

def save_tasks_locally():
    tasks_string = json.dumps(st.session_state.tasks)
    # Native synchronous write—saves instantly to the browser URL string with no timing delays
    st.query_params["tasks_data"] = tasks_string

# --- 2. MODE: ADDING TASKS ---
if st.session_state.mode == "adding":
    
    left_col, right_col = st.columns([1, 1.5], gap="large")

    with left_col:
        is_expanded = st.session_state.force_expand_list
        with st.expander("📋 View / Hide Full Task List", expanded=is_expanded):
            if len(st.session_state.tasks) > 0:
                for i, t in enumerate(st.session_state.tasks, 1):
                    if t["prereq"]:
                        st.write(f"{i}. **{t['name']}** \n*(Requires: {t['prereq']})*")
                    else:
                        st.write(f"{i}. **{t['name']}**")
            else:
                st.write("Your list is currently empty.")

        if st.session_state.confirm_delete_list:
            st.sidebar.error("Are you sure you want to delete the WHOLE list? This can't be undone.")

    with right_col:
        st.html("<h2 style='text-align: center; margin-bottom: 20px;'>Build Your List</h2>")
        st.write(f"Current task count: {len(st.session_state.tasks)} / {LIMIT}")

        has_prereq = st.selectbox(
            "Does this task have a prerequisite?", 
            ["No", "Yes"],
            key="has_prereq_select"
        )

        with st.form(key="input_form", clear_on_submit=True):
            task_text = st.text_input("Enter a task you would like to add:")

            prereq_text = ""
            if has_prereq == "Yes":
                prereq_text = st.text_input("What must be completed first?")

            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                submit_task = st.form_submit_button("Add Task")

            with btn_col2:
                delete_task_click = st.form_submit_button("Delete Task")
                if delete_task_click:
                    st.session_state.show_delete_dropdown = True
                    st.session_state.force_expand_list = True

            with btn_col3:
                black_btn_label = "Yes, Everything" if st.session_state.confirm_delete_list else "Delete List"
                delete_list_click = st.form_submit_button(black_btn_label)
                if delete_list_click:
                    if not st.session_state.confirm_delete_list:
                        st.session_state.confirm_delete_list = True
                        st.rerun()
                    else:
                        st.session_state.tasks = []
                        st.session_state.current_index = 0
                        st.session_state.confirm_delete_list = False
                        st.session_state.show_delete_dropdown = False
                        save_tasks_locally()
                        st.rerun()

            if submit_task:
                task_text_cleaned = task_text.strip()
                if task_text_cleaned != "":
                    if len(st.session_state.tasks) < LIMIT:
                        task_data = {
                            "name": task_text_cleaned,
                            "prereq": prereq_text.strip() if has_prereq == "Yes" and prereq_text.strip() else None
                        }
                        st.session_state.tasks.append(task_data)
                        save_tasks_locally()
                        st.session_state.show_delete_dropdown = False
                        st.rerun()
                    else:
                        st.sidebar.error(f"You have reached the task limit of {LIMIT}!")
                else:
                    st.sidebar.warning("Please type a task name first!")

        if st.session_state.confirm_delete_list:
            st.html("""
                <style>
                button.giant-goback-btn {
                    font-size: 24px !important;
                    padding: 16px 32px !important;
                    height: auto !important;
                    width: 100% !important;
                }
                </style>
            """)
            if st.button("Go Back", key="go_back_btn"):
                st.session_state.confirm_delete_list = False
                st.session_state.show_delete_dropdown = False
                st.rerun()
            st.html("<script>document.getElementById('root').querySelector('button:has(div:contains(\"Go Back\"))').classList.add('giant-goback-btn');</script>")

        if st.session_state.show_delete_dropdown and len(st.session_state.tasks) > 0:
            task_numbers = [str(i) for i in range(1, len(st.session_state.tasks) + 1)]
            selected_num = st.selectbox("Select task number to remove permanently:", ["None"] + task_numbers)
            
            if selected_num != "None":
                del_idx = int(selected_num) - 1
                del st.session_state.tasks[del_idx]
                save_tasks_locally()
                st.session_state.show_delete_dropdown = False
                st.rerun()

        st.markdown("---")
        
        if len(st.session_state.tasks) > 0:
            st.html("<div style='display: flex; justify-content: center; margin-top: 25px;'>")
            if st.button("Start Working", key="start_working_big"):
                st.session_state.mode = "working"
                st.session_state.current_index = 0
                st.session_state.affirmation = None
                st.rerun()
            st.html("</div>")

# --- 3. MODE: WORKING ON TASKS ---
elif st.session_state.mode == "working":
    st.write("")
    st.write("")

    if len(st.session_state.tasks) > 0:
        if st.session_state.current_index >= len(st.session_state.tasks):
            st.session_state.current_index = 0

        current_task = st.session_state.tasks[st.session_state.current_index]
        
        st.html(f"<h1 style='text-align: center; margin-bottom: 20px;'>{current_task['name']}</h1>")
        
        if current_task['prereq']:
            st.warning(f"⚠️ **Prerequisite reminder:** You need to finish this task first: **{current_task['prereq']}**")
        
        st.write("")
        st.write("")

        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👍 Yes, I completed it!", use_container_width=True):
                del st.session_state.tasks[st.session_state.current_index]
                save_tasks_locally()
                st.session_state.affirmation = random.choice(AFFIRMATIONS)
                if st.session_state.current_index >= len(st.session_state.tasks):
                    st.session_state.current_index = 0
                st.rerun()

        with col2:
            if st.button("👎 No, skip it for now", use_container_width=True):
                st.session_state.current_index += 1
                st.session_state.affirmation = None
                if st.session_state.current_index >= len(st.session_state.tasks):
                    st.session_state.current_index = 0
                st.rerun()

        with col3:
            if st.button("↩️ Check the list again", use_container_width=True):
                st.session_state.mode = "adding"
                st.session_state.affirmation = None
                st.rerun()

        if st.session_state.affirmation:
            st.write("")
            st.write("")
            st.html(f"<div style='text-align: center; font-size: 28px; font-weight: 400; color: inherit;'>{st.session_state.affirmation}</div>")

    else:
        st.balloons()
        st.success("All tasks have been completed! Hooray!")
        
        if st.button("Restart Program", use_container_width=True):
            st.session_state.tasks = []
            st.session_state.current_index = 0
            st.session_state.mode = "adding"
            st.session_state.affirmation = None
            save_tasks_locally()
            st.rerun()
            