import streamlit as st
import json
import random
from streamlit_cookies_controller import CookieController

# 🚀 Unlocks the entire width of your monitor, removing restricted side margins
st.set_page_config(layout="wide")

# ==============================================================================
# 🎨 CENTRAL STYLE CONFIGURATION (Change your fonts and colors here!)
# ==============================================================================
TEXT_COLOR = "black"  
FONT_FAMILY = "Georgia"  

STYLE_WRAPPER = f"<div style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>"

# 🎛️ BUTTON TEXT COLOR SWITCHES
COLOR_ADD_TASK = "green"
COLOR_MOVE_TASK = "blue"
COLOR_DELETE_TASK = "red"
COLOR_DELETE_LIST = "black"

# Bulletproof targeting using native Streamlit key classes
st.html(f"""
    <style>
    /* 1. Add Task Button */
    div[class*="st-key-btn_add"] button p {{
        color: {COLOR_ADD_TASK} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    /* 2. Move Task Button */
    div[class*="st-key-btn_move"] button p {{
        color: {COLOR_MOVE_TASK} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    /* 3. Delete Task Button */
    div[class*="st-key-btn_delete_task"] button p {{
        color: {COLOR_DELETE_TASK} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    /* 4. Delete List Button */
    div[class*="st-key-btn_delete_list"] button p {{
        color: {COLOR_DELETE_LIST} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    /* 5. Confirm Move Action Button */
    div[class*="st-key-btn_confirm_move"] button p {{
        color: {COLOR_MOVE_TASK} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    /* 6. Confirm Delete Action Button */
    div[class*="st-key-btn_confirm_delete"] button p {{
        color: {COLOR_DELETE_TASK} !important;
        font-family: {FONT_FAMILY} !important;
    }}
    </style>
""")
# ==============================================================================


# ==============================================================================
# 🍪 BROWSER COOKIE CONFIGURATION (Ensures private, permanent user lists)
# ==============================================================================
# Initialize the browser cookie controller
controller = CookieController()

def load_tasks_from_browser():
    """Reads the private task list stored in the visitor's browser cookies."""
    try:
        saved_cookie = controller.get('user_task_list')
        if saved_cookie:
            # Decode the stored JSON string back into a Python list, and signal True (Ready)
            return json.loads(saved_cookie), True
        return [], True  # No cookie found, but the controller is ready and empty
    except TypeError:
        # The cookie controller isn't fully initialized yet, signal False (Not Ready)
        return [], False
    except Exception:
        return [], True

def save_tasks_to_browser():
    """Saves the current list directly into the visitor's browser cookies."""
    try:
        # Convert the task list to a text string and store it for up to 30 days
        json_str = json.dumps(st.session_state.tasks)
        controller.set('user_task_list', json_str, max_age=2592000)
    except Exception as e:
        st.sidebar.error(f"Storage Error: {e}")

# Read and initialize the private list on the very first page load with a safety switch
if "cookie_loaded" not in st.session_state:
    st.session_state.cookie_loaded = False

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if not st.session_state.cookie_loaded:
    saved_tasks, controller_ready = load_tasks_from_browser()
    if controller_ready:
        st.session_state.tasks = saved_tasks
        st.session_state.cookie_loaded = True
        st.rerun()
    else:
        # If the browser handshake isn't complete yet, pause briefly and try again
        st.html("<div style='display:none;'></div>")
        st.rerun()
# ==============================================================================

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
    
    # Perfectly balanced for wide mode: generous task list, spacious flat button form
    left_col, right_col = st.columns([1.5, 1.2], gap="large")

    with left_col:
        st.html(f"<h3 style='margin-bottom: 5px; color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>📋 Your Task List</h3>")
        
        with st.container(height=450, border=True):
            if len(st.session_state.tasks) > 0:
                for i, t in enumerate(st.session_state.tasks, 1):
                    if t["prereq"]:
                        st.html(f"{STYLE_WRAPPER}{i}. <b>{t['name']}</b> <br><i>(Requires: {t['prereq']})</i></div><hr style='margin: 8px 0;'>")
                    else:
                        st.html(f"{STYLE_WRAPPER}{i}. <b>{t['name']}</b></div><hr style='margin: 8px 0;'>")
            else:
                st.html(f"{STYLE_WRAPPER}Your list is currently empty.</div>")

        if st.session_state.confirm_delete_list:
            st.sidebar.error("Are you sure you want to delete the WHOLE list? This can't be undone.")

    with right_col:
        st.html(f"<h2 style='text-align: center; margin-bottom: 20px; color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>Build Your List</h2>")
        st.html(f"{STYLE_WRAPPER}Current task count: {len(st.session_state.tasks)} / {LIMIT}</div><br>")

        with st.form(key="input_form", clear_on_submit=True):
            st.html(f"<div style='color: purple; font-family: {FONT_FAMILY};'>Enter a task you would like to add:</div>")
            task_text = st.text_input(label="Task Input", label_visibility="collapsed")
            
            st.html(f"<div style='color: gray; font-family: {FONT_FAMILY};'>What must be completed first? (Optional)</div>")
            prereq_text = st.text_input(label="Prerequisite Input", label_visibility="collapsed")

            # With the column now twice as wide, we can return to a clean 4-column row!
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
            
            with btn_col1:
                submit_task = st.form_submit_button("Add Task", key="btn_add", use_container_width=True)

            with btn_col2:
                move_task_click = st.form_submit_button("Move Task", key="btn_move", use_container_width=True)
                if move_task_click:
                    st.session_state.show_move_dropdowns = True
                    st.session_state.show_delete_dropdown = False
                    st.session_state.force_expand_list = True

            with btn_col3:
                delete_task_click = st.form_submit_button("Delete Task", key="btn_delete_task", use_container_width=True)
                if delete_task_click:
                    st.session_state.show_delete_dropdown = True
                    st.session_state.show_move_dropdowns = False
                    st.session_state.force_expand_list = True

            with btn_col4:
                black_btn_label = "Yes, All" if st.session_state.confirm_delete_list else "Delete List"
                delete_list_click = st.form_submit_button(black_btn_label, key="btn_delete_list", use_container_width=True)
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
                        save_tasks_to_browser()
                        st.rerun()

            # --- PROCESS FORM SUBMISSION ---
            if submit_task:
                if task_text.strip() != "":
                    if len(st.session_state.tasks) < LIMIT:
                        new_task = {
                            "name": task_text.strip(),
                            "prereq": prereq_text.strip() if prereq_text.strip() != "" else None
                        }
                        st.session_state.tasks.append(new_task)
                        save_tasks_to_browser()
                        st.session_state.confirm_delete_list = False
                        st.rerun()
                    else:
                        st.sidebar.error(f"Limit reached! You cannot add more than {LIMIT} tasks.")
                else:
                    st.sidebar.warning("Task name cannot be blank!")

        # --- MOVE TASK DROPDOWNS ---
        if st.session_state.show_move_dropdowns and len(st.session_state.tasks) > 1:
            st.markdown("---")
            st.html(f"{STYLE_WRAPPER}<b>Rearrange Task Order:</b></div>")
            
            move_col1, move_col2, move_col3 = st.columns([1.5, 1.5, 1])
            task_numbers = [str(i) for i in range(1, len(st.session_state.tasks) + 1)]
            
            with move_col1:
                st.html(f"{STYLE_WRAPPER}Move task number:</div>")
                from_num = st.selectbox(label="From Position", options=["Choose..."] + task_numbers, key="move_from_drop", label_visibility="collapsed")
                
            with move_col2:
                st.html(f"{STYLE_WRAPPER}To new position:</div>")
                to_num = st.selectbox(label="To Position", options=["Choose..."] + task_numbers, key="move_to_drop", label_visibility="collapsed")
            
            with move_col3:
                st.html("<div style='margin-top: 24px;'></div>") 
                if st.button("Confirm Move", key="btn_confirm_move", use_container_width=True):
                    if from_num != "Choose..." and to_num != "Choose...":
                        if from_num != to_num:
                            from_idx = int(from_num) - 1
                            to_idx = int(to_num) - 1
                            
                            moved_task = st.session_state.tasks.pop(from_idx)
                            st.session_state.tasks.insert(to_idx, moved_task)
                            
                            save_tasks_to_browser()
                            st.session_state.show_move_dropdowns = False
                            st.rerun()
                    else:
                        st.sidebar.warning("Please select both positions first!")
                        
        elif st.session_state.show_move_dropdowns and len(st.session_state.tasks) <= 1:
            st.sidebar.warning("You need at least 2 tasks in your list to rearrange them!")
            st.session_state.show_move_dropdowns = False

        # --- DELETE SINGLE TASK DROPDOWN ---
        if st.session_state.show_delete_dropdown and len(st.session_state.tasks) > 0:
            st.markdown("---")
            st.html(f"{STYLE_WRAPPER}Select task number to remove permanently:</div>")
            
            del_col1, del_col2 = st.columns([3, 1])
            task_numbers = [str(i) for i in range(1, len(st.session_state.tasks) + 1)]
            
            with del_col1:
                selected_num = st.selectbox(label="Select Task Dropdown", options=["None"] + task_numbers, key="delete_task_drop", label_visibility="collapsed")
            
            with del_col2:
                if st.button("Confirm Delete", key="btn_confirm_delete", use_container_width=True):
                    if selected_num != "None":
                        del_idx = int(selected_num) - 1
                        del st.session_state.tasks[del_idx]
                        save_tasks_to_browser()
                        st.session_state.show_delete_dropdown = False
                        st.rerun()
                    else:
                        st.sidebar.warning("Please select a task number to delete!")
        
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
                save_tasks_to_browser()
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
            save_tasks_to_browser()
            st.rerun()
            