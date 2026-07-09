import streamlit as st
import json
from streamlit_cookies_manager import EncryptedCookieManager

# --- 1. SECURE BROWSER STORAGE SETUP ---
cookies = EncryptedCookieManager(
    prefix="allons_y_tasks/",
    password=st.secrets.get("cookie_password", "KeepItSecretKeepItSafe123!")
)

if not cookies.ready():
    st.stop()

# Title is only shown when building the list now to accommodate the working mode changes
if "mode" in st.session_state and st.session_state.mode == "adding":
    st.title("Executive Function Assistant")

if "tasks" not in st.session_state:
    saved_tasks_raw = cookies.get("tasks_data")
    if saved_tasks_raw:
        try:
            st.session_state.tasks = json.loads(saved_tasks_raw)
        except Exception:
            st.session_state.tasks = []
    else:
        st.session_state.tasks = []  

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

LIMIT = 50

def save_tasks_locally():
    tasks_string = json.dumps(st.session_state.tasks)
    cookies["tasks_data"] = tasks_string
    cookies.save()

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
            
            st.html("""
                <style>
                div[data-testid="stVerticalBlock"] div:has(> button.purple-btn) { text-align: left; }
                button.purple-btn {
                    border: 3px solid #800080 !important;
                    background-color: transparent !important;
                }
                </style>
            """)
            if st.button("Go Back", key="go_back_btn", help="Cancel list clearing", type="secondary"):
                st.session_state.confirm_delete_list = False
                st.session_state.show_delete_dropdown = False
                st.rerun()

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

            st.html("""
                <style>
                button.green-btn { border: 3px solid #28a745 !important; background-color: transparent !important; }
                button.red-btn { border: 3px solid #dc3545 !important; background-color: transparent !important; }
                button.black-btn { border: 3px solid #000000 !important; background-color: transparent !important; }
                </style>
            """)

            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                submit_task = st.form_submit_button("Add Task")
                st.html("<script>document.querySelectorAll('button[form=\"input_form\"]')[0].classList.add('green-btn');</script>")

            with btn_col2:
                delete_task_click = st.form_submit_button("Delete Task")
                st.html("<script>document.querySelectorAll('button[form=\"input_form\"]')[1].classList.add('red-btn');</script>")
                if delete_task_click:
                    st.session_state.show_delete_dropdown = True
                    st.session_state.force_expand_list = True

            with btn_col3:
                black_btn_label = "Yes, Everything" if st.session_state.confirm_delete_list else "Delete List"
                delete_list_click = st.form_submit_button(black_btn_label)
                st.html("<script>document.querySelectorAll('button[form=\"input_form\"]')[2].classList.add('black-btn');</script>")
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
                        st.sidebar.error("You have reached the task limit of 50!")
                else:
                    st.sidebar.warning("Please type a task name first!")

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
            st.html("""
                <style>
                .centered-big-button {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin-top: 25px;
                }
                button.blue-giant-btn {
                    border: 4px solid #007bff !important;
                    background-color: transparent !important;
                    font-size: 26px !important;
                    padding: 20px 44px !important;
                    height: auto !important;
                    width: auto !important;
                    font-weight: bold !important;
                    border-radius: 8px !important;
                }
                </style>
            """)
            
            st.html("<div class='centered-big-button'>")
            if st.button("Start Working", key="start_working_big"):
                st.session_state.mode = "working"
                st.session_state.current_index = 0
                st.rerun()
            st.html("<script>document.getElementById('root').querySelector('button:has(div:contains(\"Start Working\"))').classList.add('blue-giant-btn');</script>")
            st.html("</div>")

# --- 3. MODE: WORKING ON TASKS ---
elif st.session_state.mode == "working":
    # Added layout adjustments to push content down and keep things centered vertically
    st.write("")
    st.write("")

    if len(st.session_state.tasks) > 0:
        if st.session_state.current_index >= len(st.session_state.tasks):
            st.session_state.current_index = 0

        current_task = st.session_state.tasks[st.session_state.current_index]
        
        # Styles for the non-clickable focus frame block matching original title typography
        st.html("""
            <style>
            .task-focus-container {
                border: 4px solid #007bff;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 35px;
                background-color: transparent;
            }
            .task-focus-title {
                font-size: 42px;
                font-weight: 700;
                color: inherit;
                margin-bottom: 10px;
            }
            .task-focus-prereq {
                font-size: 18px;
                margin-top: 15px;
            }
            </style>
        """)

        # Main Attention-Grabbing Blue Frame Container
        st.html("<div class='task-focus-container'>")
        st.html(f"<div class='task-focus-title'>Current Task: {current_task['name']}</div>")
        if current_task['prereq']:
            st.html(f"<div class='task-focus-prereq'>⚠️ <strong>Prerequisite reminder:</strong> You need to finish this task first:<br> {current_task['prereq']}</div>")
        st.html("</div>")

        # Three perfectly centered action columns replacing the original dual setup
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👍 Yes, I completed it!", use_container_width=True):
                del st.session_state.tasks[st.session_state.current_index]
                save_tasks_locally()
                if st.session_state.current_index >= len(st.session_state.tasks):
                    st.session_state.current_index = 0
                st.rerun()

        with col2:
            if st.button("👎 No, skip it for now", use_container_width=True):
                st.session_state.current_index += 1
                if st.session_state.current_index >= len(st.session_state.tasks):
                    st.session_state.current_index = 0
                st.rerun()

        with col3:
            # New navigation switch to return directly to editing view
            if st.button("↩️ Check the list again", use_container_width=True):
                st.session_state.mode = "adding"
                st.rerun()

    else:
        st.balloons()
        st.success("All tasks have been completed! Hooray!")
        
        if st.button("Restart Program", use_container_width=True):
            st.session_state.tasks = []
            st.session_state.current_index = 0
            st.session_state.mode = "adding"
            save_tasks_locally()
            st.rerun()
            