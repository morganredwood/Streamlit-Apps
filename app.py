import streamlit as st
import json
import random
import os
# ==============================================================================
# 🎨 CENTRAL STYLE CONFIGURATION (Change your fonts and colors here!)
# ==============================================================================
TEXT_COLOR = "black"  
FONT_FAMILY = "Georgia"  

STYLE_WRAPPER = f"<div style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>"

# 🎛️ BUTTON TEXT COLOR SWITCHES (Change individual button text colors here!)
COLOR_ADD_TASK = "green"
COLOR_MOVE_TASK = "blue"
COLOR_DELETE_TASK = "red"
COLOR_DELETE_LIST = "black"

# Bulletproof positional CSS injection targeting column contents at any depth inside the form
st.html(f"""
    <style>
    /* 1. Add Task Button (Column 1) */
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(1) button p {{
        color: {COLOR_ADD_TASK} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    /* 2. Move Task Button (Column 2) */
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(2) button p {{
        color: {COLOR_MOVE_TASK} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    /* 3. Delete Task Button (Column 3) */
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(3) button p {{
        color: {COLOR_DELETE_TASK} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    /* 4. Delete List Button (Column 4) */
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-of-type(4) button p {{
        color: {COLOR_DELETE_LIST} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    </style>
""")
# ==============================================================================

# --- 1. BULLETPROOF LOCAL FILE STORAGE SETUP ---
BACKUP_FILE = "task_backup.json"

def load_tasks_from_file():
    """Instantly reads the JSON backup file on local disk."""
    if os.path.exists(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_tasks_to_file():
    """Instantly saves the current list to local disk."""
    try:
        with open(BACKUP_FILE, "w") as f:
            json.dump(st.session_state.tasks, f, indent=4)
    except Exception as e:
        st.sidebar.error(f"Save Error: {e}")

# Initialize tasks instantly from disk on page load
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks_from_file()

# Title is only shown when building the list now
if "mode" in st.session_state and st.session_state.mode == "adding":
    st.html(f"<h1 style='color: {TEXT_COLOR}; font-family: {'Georgia'};'>Executive Function Assistant</h1>")

if "current_index" not in st.session_state:
    st.session_state.current_index = 0  

if "mode" not in st.session_state:
    st.session_state.mode = "adding"  

if "show_delete_dropdown" not in st.session_state:
    st.session_state.show_delete_dropdown = False

if "show_move_dropdowns" not in st.session_state:
    st.session_state.show_move_dropdowns = False

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

# --- 2. MODE: ADDING TASKS ---
if st.session_state.mode == "adding":
    
    left_col, right_col = st.columns([1, 1.5], gap="large")

    with left_col:
        is_expanded = st.session_state.force_expand_list
        with st.expander("📋 View / Hide Full Task List", expanded=is_expanded):
            if len(st.session_state.tasks) > 0:
                for i, t in enumerate(st.session_state.tasks, 1):
                    if t["prereq"]:
                        st.html(f"{STYLE_WRAPPER}{i}. <b>{t['name']}</b> <br><i>(Requires: {t['prereq']})</i></div>")
                    else:
                        st.html(f"{STYLE_WRAPPER}{i}. <b>{t['name']}</b></div>")
            else:
                st.html(f"{STYLE_WRAPPER}Your list is currently empty.</div>")

        if st.session_state.confirm_delete_list:
            st.sidebar.error("Are you sure you want to delete the WHOLE list? This can't be undone.")

    with right_col:
        st.html(f"<h2 style='text-align: center; margin-bottom: 20px; color: {TEXT_COLOR}; font-family: {'Georgia'};'>Build Your List</h2>")
        st.html(f"{STYLE_WRAPPER}Current task count: {len(st.session_state.tasks)} / {LIMIT}</div><br>")

        with st.form(key="input_form", clear_on_submit=True):
            st.html(f"<div style='color: {'purple'}; font-family: {'Georgia'};'>Enter a task you would like to add:</div>")
            task_text = st.text_input(label="Task Input", label_visibility="collapsed")
            
            st.html(f"<div style='color: {'gray'}; font-family: {'Georgia'};'>What must be completed first? (Optional)</div>")
            prereq_text = st.text_input(label="Prerequisite Input", label_visibility="collapsed")

            # Updated into a 4-column row to fit the new "Move Task" button cleanly
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
            
            with btn_col1:
                submit_task = st.form_submit_button("Add Task", key="btn_add")

            with btn_col2:
                move_task_click = st.form_submit_button("Move Task", key="btn_move")
                if move_task_click:
                    st.session_state.show_move_dropdowns = True
                    st.session_state.show_delete_dropdown = False
                    st.session_state.force_expand_list = True

            with btn_col3:
                delete_task_click = st.form_submit_button("Delete Task", key="btn_delete_task")
                if delete_task_click:
                    st.session_state.show_delete_dropdown = True
                    st.session_state.show_move_dropdowns = False
                    st.session_state.force_expand_list = True

            with btn_col4:
                black_btn_label = "Yes, All" if st.session_state.confirm_delete_list else "Delete List"
                delete_list_click = st.form_submit_button(black_btn_label, key="btn_delete_list")
                if delete_list_click:
                    if not st.session_state.confirm_delete_list:
                        st.session_state.confirm_delete_list = True
                        st.rerun()
                    else:
                        st.session_state.tasks = []
                        st.session_state.current_index = 0
                        st.session_state.confirm_delete_list = False
                        st.session_state.show_delete_dropdown = False
                        st.session_state.show_move_dropdowns = False
                        save_tasks_to_file()
                        st.rerun()

            if submit_task:
                task_text_cleaned = task_text.strip()
                if task_text_cleaned != "":
                    if len(st.session_state.tasks) < LIMIT:
                        task_data = {
                            "name": task_text_cleaned,
                            "prereq": prereq_text.strip() if prereq_text.strip() else None
                        }
                        st.session_state.tasks.append(task_data)
                        save_tasks_to_file()
                        st.session_state.show_delete_dropdown = False
                        st.session_state.show_move_dropdowns = False
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
                st.session_state.show_move_dropdowns = False
                st.rerun()
            st.html("<script>document.getElementById('root').querySelector('button:has(div:contains(\"Go Back\"))').classList.add('giant-goback-btn');</script>")

        # --- MOVE TASK DROPDOWNS ---
        if st.session_state.show_move_dropdowns and len(st.session_state.tasks) > 1:
            st.markdown("---")
            st.html(f"{STYLE_WRAPPER}<b>Rearrange Task Order:</b></div>")
            
            move_col1, move_col2 = st.columns(2)
            task_numbers = [str(i) for i in range(1, len(st.session_state.tasks) + 1)]
            
            with move_col1:
                st.html(f"{STYLE_WRAPPER}Move task number:</div>")
                from_num = st.selectbox(label="From Position", options=["Choose..."] + task_numbers, key="move_from_drop", label_visibility="collapsed")
                
            with move_col2:
                st.html(f"{STYLE_WRAPPER}To new position:</div>")
                to_num = st.selectbox(label="To Position", options=["Choose..."] + task_numbers, key="move_to_drop", label_visibility="collapsed")
            
            if from_num != "Choose..." and to_num != "Choose...":
                if from_num != to_num:
                    from_idx = int(from_num) - 1
                    to_idx = int(to_num) - 1
                    
                    # Pop the task out of the list and slide it into its new index position
                    moved_task = st.session_state.tasks.pop(from_idx)
                    st.session_state.tasks.insert(to_idx, moved_task)
                    
                    save_tasks_to_file()
                    st.session_state.show_move_dropdowns = False
                    st.rerun()
        elif st.session_state.show_move_dropdowns and len(st.session_state.tasks) <= 1:
            st.sidebar.warning("You need at least 2 tasks in your list to rearrange them!")
            st.session_state.show_move_dropdowns = False

        if st.session_state.show_delete_dropdown and len(st.session_state.tasks) > 0:
            st.html(f"{STYLE_WRAPPER}Select task number to remove permanently:</div>")
            task_numbers = [str(i) for i in range(1, len(st.session_state.tasks) + 1)]
            selected_num = st.selectbox(label="Select Task Dropdown", options=["None"] + task_numbers, label_visibility="collapsed")
            
            if selected_num != "None":
                del_idx = int(selected_num) - 1
                del st.session_state.tasks[del_idx]
                save_tasks_to_file()
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
        
        st.html(f"<h1 style='text-align: center; margin-bottom: 20px; color: {TEXT_COLOR}; font-family: {'Georgia'};'>{current_task['name']}</h1>")
        
        if current_task['prereq']:
            st.warning(f"⚠️ **Prerequisite reminder:** You need to finish this task first: **{current_task['prereq']}**")
        
        st.write("")
        st.write("")

        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👍 Yes, I completed it!", use_container_width=True):
                del st.session_state.tasks[st.session_state.current_index]
                save_tasks_to_file()
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
            st.html(f"<div style='text-align: center; font-size: 28px; font-weight: 400; color: {'orange'}; font-family: {'Comic Sans MS'};'>{st.session_state.affirmation}</div>")

    else:
        st.balloons()
        st.success("All tasks have been completed! Hooray!")
        
        if st.button("Restart Program", use_container_width=True):
            st.session_state.tasks = []
            st.session_state.current_index = 0
            st.session_state.mode = "adding"
            st.session_state.affirmation = None
            save_tasks_to_file()
            st.rerun()
            