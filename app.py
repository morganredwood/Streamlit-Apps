import streamlit as st
import json
import random
import os
from supabase import create_client, Client

# 🚀 Unlocks full monitor width
st.set_page_config(layout="wide")

# ==============================================================================
# 🌐 SUPABASE CLOUD DATABASE CONFIGURATION
# ==============================================================================
# Pulls keys safely from Streamlit Cloud Secrets (or local .streamlit/secrets.toml)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception as e:
    SUPABASE_URL = ""
    SUPABASE_KEY = ""

LIMIT = 500  # Hard locked cap capacity

@st.cache_resource
def init_supabase() -> Client:
    """Initializes and caches the Supabase database connection."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"⚠️ Supabase Error Detail: {e}")

def load_from_cloud(user_key: str):
    """Fetches tasks and list name for a specific user passcode from Supabase."""
    if not user_key.strip():
        return
    try:
        response = supabase.table("tasks_db").select("*").eq("user_key", user_key.strip()).execute()
        if response.data:
            row = response.data[0]
            st.session_state.tasks = row.get("tasks_data", [])
            st.session_state.list_name = row.get("list_name", None)
        else:
            # If user key doesn't exist yet, start fresh for them
            st.session_state.tasks = []
            st.session_state.list_name = None
    except Exception as e:
        st.sidebar.error(f"Error loading cloud data: {e}")

def save_to_cloud():
    """Saves current tasks and list name to Supabase under the active user_key."""
    user_key = st.session_state.get("user_passcode", "").strip()
    if not user_key:
        return
    try:
        payload = {
            "user_key": user_key,
            "list_name": st.session_state.list_name,
            "tasks_data": st.session_state.tasks
        }
        # Upsert creates the row if new, or updates it if user_key exists
        supabase.table("tasks_db").upsert(payload).execute()
    except Exception as e:
        st.sidebar.error(f"Failed to auto-save to cloud: {e}")

# ==============================================================================
# 🗂️ GLOBAL STATE INITIALIZATIONS
# ==============================================================================
if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "list_name" not in st.session_state:
    st.session_state.list_name = None

# Store passcode in session state
if "user_passcode" not in st.session_state:
    st.session_state.user_passcode = ""

passcode_input = st.sidebar.text_input

if passcode_input:
    st.session_state.user_passcode = passcode_input

if "uploader_id" not in st.session_state:
    st.session_state.uploader_id = 0

if "import_success" not in st.session_state:
    st.session_state.import_success = False

if "current_index" not in st.session_state:
    st.session_state.current_index = 0  

if "mode" not in st.session_state:
    st.session_state.mode = "adding"  

if "form_version" not in st.session_state:
    st.session_state.form_version = 0

# Panel visibility toggles
if "show_delete_dropdown" not in st.session_state:
    st.session_state.show_delete_dropdown = False

if "show_move_dropdowns" not in st.session_state:
    st.session_state.show_move_dropdowns = False

if "show_edit_dropdown" not in st.session_state:
    st.session_state.show_edit_dropdown = False

# Editing state tracker
if "editing_index" not in st.session_state:
    st.session_state.editing_index = None

if "edit_task_name" not in st.session_state:
    st.session_state.edit_task_name = ""

if "edit_prereq_name" not in st.session_state:
    st.session_state.edit_prereq_name = ""

if "confirm_delete_list" not in st.session_state:
    st.session_state.confirm_delete_list = False

if "affirmation" not in st.session_state:
    st.session_state.affirmation = None

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

def reset_transient_panels():
    """Helper function to close all temporary action dropdowns/prompts."""
    st.session_state.show_edit_dropdown = False
    st.session_state.show_move_dropdowns = False
    st.session_state.show_delete_dropdown = False
    st.session_state.confirm_delete_list = False

# ==============================================================================
# 🎨 CENTRAL STYLE CONFIGURATION
# ==============================================================================
TEXT_COLOR = "black"  
FONT_FAMILY = "Georgia"

STYLE_WRAPPER = f"<div style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>"

COLOR_ADD_TASK = "green"
COLOR_EDIT_TASK = "darkorange"
COLOR_MOVE_TASK = "blue"
COLOR_DELETE_TASK = "red"
COLOR_DELETE_LIST = "black"

st.html(f"""
    <style>
    div[class*="st-key-btn_"] button {{
        width: 100% !important;
        padding-left: 4px !important;
        padding-right: 4px !important;
    }}
    
    div[class*="st-key-btn_"] button p {{
        white-space: normal !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        hyphens: none !important;
        text-align: center !important;
    }}

    @media (max-width: 992px) {{
        div[data-testid="column"]:has(div[class*="st-key-btn_"]) {{
            min-width: 110px !important;
            flex: 1 1 30% !important;
            margin-bottom: 8px !important;
        }}
    }}

    div[class*="st-key-btn_add"] button p {{ color: {COLOR_ADD_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_edit"] button p {{ color: {COLOR_EDIT_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_move"] button p {{ color: {COLOR_MOVE_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_delete_task"] button p {{ color: {COLOR_DELETE_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_delete_list"] button p {{ color: {COLOR_DELETE_LIST} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_confirm_edit"] button p {{ color: {COLOR_EDIT_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_confirm_move"] button p {{ color: {COLOR_MOVE_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_confirm_delete"] button p {{ color: {COLOR_DELETE_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    </style>
""")

# ==============================================================================
# 💾 SIDEBAR: CLOUD PASSCODE LOGIN & UTILITIES
# ==============================================================================
with st.sidebar:
    st.html(f"<h3 style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>☁️ Cloud Sync Login</h3>")
    
    # 🔑 USER PASSCODE FIELD
    passcode_input = st.text_input(
        label="Enter a unique key to load and auto-sync your tasks across sessions:",
        value=st.session_state.user_passcode,
        placeholder="e.g. kid1 or family",
        key="passcode_field"
    )

    if passcode_input != st.session_state.user_passcode:
        st.session_state.user_passcode = passcode_input
        st.session_state.uploader_id = passcode_input

        if passcode_input.strip():
            load_from_cloud(passcode_input)
            st.rerun()

    if st.session_state.user_passcode:
        st.sidebar.success(f"🟢 Synced as: **{st.session_state.user_passcode}**")
    
    st.markdown("---")
    st.html(f"<h3 style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>💾 Workspace Backup</h3>")
    
    # --- UTILITY 1: EXPORT LIST ---
    if len(st.session_state.tasks) > 0:
        current_list_name = st.session_state.get("list_name", None)
        default_name = current_list_name if current_list_name else "executive_tasks_backup"
        
        st.html(f"<div style='color: gray; font-size: 14px; font-family: {FONT_FAMILY}; margin-bottom: 2px;'>Export File Name:</div>")
        custom_name = st.text_input(
            label="Export File Name",
            value="",
            placeholder=default_name,
            key="export_file_name_input",
            label_visibility="collapsed"
        )
        
        clean_name = custom_name.strip()
        if clean_name.lower().endswith(".json"):
            clean_name = clean_name[:-5]
        if not clean_name:
            clean_name = default_name
            
        final_export_filename = f"{clean_name}.json"

        json_string = json.dumps(st.session_state.tasks, indent=2)
        st.download_button(
            label="📤 Export List",
            data=json_string,
            file_name=final_export_filename,
            mime="application/json",
            use_container_width=True,
            key="btn_export_sidebar"
        )
    else:
        st.button("📤 Export List (Empty)", disabled=True, use_container_width=True, key="btn_export_disabled")

    # --- UTILITY 2: DUAL IMPORT INTERFACE ---
    uploaded_file = st.file_uploader(
        label="📥 Select Saved List (.json)",
        type=["json"],
        key=f"file_uploader_{st.session_state.uploader_id}",
        label_visibility="visible"
    )

    if uploaded_file is not None:
        col_replace, col_combine = st.columns(2)
        
        with col_replace:
            replace_clicked = st.button("Upload: Replace", use_container_width=True)
            
        with col_combine:
            combine_clicked = st.button("Upload: Combine", use_container_width=True)
            
        try:
            imported_data = json.load(uploaded_file)
            
            if isinstance(imported_data, list):
                num_imported = len(imported_data)
                current_count = len(st.session_state.tasks)
                
                if replace_clicked:
                    if num_imported <= LIMIT:
                        st.session_state.tasks = imported_data
                        st.session_state.current_index = 0
                        st.session_state.mode = "adding"
                        st.session_state.import_success = True
                        st.session_state.uploader_id += 1
                        st.session_state.editing_index = None
                        st.session_state.edit_task_name = ""
                        st.session_state.edit_prereq_name = ""
                        st.session_state.form_version += 1
                        reset_transient_panels()
                        
                        base_name, _ = os.path.splitext(uploaded_file.name)
                        st.session_state.list_name = base_name
                        
                        save_to_cloud()
                        st.rerun()
                    else:
                        st.error(f"❌ Import failed: File exceeds limit of {LIMIT} tasks.")
                
                elif combine_clicked:
                    if current_count == 0:
                        st.sidebar.warning("⚠️ Your task list is currently empty. Enter a task first to combine.")
                    elif (current_count + num_imported) > LIMIT:
                        st.sidebar.error("❌ Unable to import: combined count exceeds limit.")
                    else:
                        st.session_state.tasks.extend(imported_data)
                        st.session_state.import_success = True
                        st.session_state.uploader_id += 1
                        reset_transient_panels()
                        save_to_cloud()
                        st.rerun()
            else:
                st.error("❌ Invalid format: Unrecognized JSON structure.")
        except Exception:
            st.error("❌ Failed to read file.")

    if st.session_state.import_success:
        st.success("✅ List restored successfully!")
        st.session_state.import_success = False

# ==============================================================================
# 🧩 MAIN VIEW LOGIC
# ==============================================================================

# --- MODE: ADDING / EDITING TASKS ---
if st.session_state.mode == "adding":
    st.html(f"<h1 style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>Executive Function Assistant</h1>")
    
    if not st.session_state.user_passcode.strip():
        st.info("👈 Don't forget your Passcode!")

    left_col, right_col = st.columns([1.5, 1.2], gap="large")

    with left_col:
        if st.session_state.list_name:
            header_html = f"<h3 style='margin-bottom: 5px; color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>📋 Current Task List: <span style='color: purple; font-weight: normal;'>{st.session_state.list_name}</span></h3>"
        else:
            header_html = f"<h3 style='margin-bottom: 5px; color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>📋 Current Task List: <span style='color: gray; font-weight: normal;'><i>(The file name you export will appear here.)</i></span></h3>"
        st.html(header_html)
        
        with st.container(height=450, border=True):
            if len(st.session_state.tasks) > 0:
                for i, t in enumerate(st.session_state.tasks, 1):
                    is_editing_this = (st.session_state.editing_index == (i - 1))
                    prefix = "✏️ " if is_editing_this else ""
                    
                    if t["prereq"]:
                        st.html(f"{STYLE_WRAPPER}{i}. {prefix}<b>{t['name']}</b> <br><i>({t['prereq']})</i></div><hr style='margin: 8px 0;'>")
                    else:
                        st.html(f"{STYLE_WRAPPER}{i}. {prefix}<b>{t['name']}</b></div><hr style='margin: 8px 0;'>")
            else:
                st.html(f"{STYLE_WRAPPER}Your list is currently empty.</div>")

        if st.session_state.confirm_delete_list:
            st.sidebar.error("Are you sure you want to delete the WHOLE list? This can't be undone.")

    with right_col:
        st.html(f"<h2 style='text-align: center; margin-bottom: 20px; color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>Build Your List</h2>")
        
        st.html(f"{STYLE_WRAPPER}Current task count: {len(st.session_state.tasks)} / {LIMIT}</div><br>")

        if st.session_state.editing_index is not None:
            active_task_num = st.session_state.editing_index + 1
            form_title = f"Editing Task #{active_task_num}:"
            add_button_label = "Save Changes"
        else:
            form_title = "Enter a task you would like to add:"
            add_button_label = "Add Task"

        ver_key = f"v{st.session_state.form_version}_e{st.session_state.editing_index}"

        with st.form(key=f"input_form_{ver_key}", clear_on_submit=True):
            new_task = st.text_input("Enter a task you would like to add:")
            submitted = st.form_submit_button("Add Task")
            if submitted:
                task_text = new_task.strip()
                if task_text:
                    if len(st.session_state.tasks) < 500:
                        st.session_state.tasks.append(task_text)
                        if st.session_state.user_passcode:
                            save_to_cloud(st.session_state.user_passcode)
                        st.rerun()
                    else:
                        st.error("Task limit reached (500 maximum).")
    
        with st.form(key=f"input_form_{ver_key}", clear_on_submit=False):
            st.html(f"<div style='color: green; font-family: {FONT_FAMILY};'>{form_title}</div>")
            task_text = st.text_input(
                label="Task Input",
                value=st.session_state.edit_task_name,
                key=f"task_in_{ver_key}",
                label_visibility="collapsed"
            )                   
    
            st.html(f"<div style='color: gray; font-family: {FONT_FAMILY};'>Enter a note you would like to add to your task. (Optional)</div>")
            prereq_text = st.text_input(
                label="Prerequisite Input",
                value=st.session_state.edit_prereq_name,
                key=f"prereq_in_{ver_key}",
                label_visibility="collapsed"
            )

            # --- 3x2 ACTION GRID ---
            row1_col1, row1_col2, row1_col3 = st.columns(3)
            with row1_col1:
                submit_task = st.form_submit_button(add_button_label, key="btn_add", use_container_width=True)

            with row1_col2:
                edit_task_click = st.form_submit_button("Edit Task", key="btn_edit", use_container_width=True)

            with row1_col3:
                move_task_click = st.form_submit_button("Move Task", key="btn_move", use_container_width=True)

            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                delete_task_click = st.form_submit_button("Delete Task", key="btn_delete_task", use_container_width=True)

            with row2_col2:
                black_btn_label = "Yes, All" if st.session_state.confirm_delete_list else "Delete List"
                delete_list_click = st.form_submit_button(black_btn_label, key="btn_delete_list", use_container_width=True)

            # --- PROCESS FORM SUBMISSIONS ---
            if submit_task:
                reset_transient_panels()
                
                if task_text.strip() != "":
                    new_task_obj = {
                        "name": task_text.strip(),
                        "prereq": prereq_text.strip() if prereq_text.strip() != "" else None
                    }
                    
                    if st.session_state.editing_index is not None:
                        idx = st.session_state.editing_index
                        if idx < len(st.session_state.tasks):
                            st.session_state.tasks[idx] = new_task_obj
                        
                        st.session_state.editing_index = None
                        st.session_state.edit_task_name = ""
                        st.session_state.edit_prereq_name = ""
                        st.session_state.form_version += 1
                        save_to_cloud()
                        st.rerun()
                    else:
                        if len(st.session_state.tasks) < LIMIT:
                            st.session_state.tasks.append(new_task_obj)
                            st.session_state.affirmation = None
                            st.session_state.edit_task_name = ""
                            st.session_state.edit_prereq_name = ""
                            st.session_state.form_version += 1
                            save_to_cloud()
                            st.rerun()
                        else:
                            st.sidebar.error(f"Limit reached! You cannot add more than {LIMIT} tasks.")
                else:
                    st.sidebar.warning("Task name cannot be blank!")

            elif edit_task_click:
                st.session_state.show_edit_dropdown = True
                st.session_state.show_move_dropdowns = False
                st.session_state.show_delete_dropdown = False
                st.session_state.confirm_delete_list = False
                st.rerun()

            elif move_task_click:
                st.session_state.show_move_dropdowns = True
                st.session_state.show_edit_dropdown = False
                st.session_state.show_delete_dropdown = False
                st.session_state.confirm_delete_list = False
                st.rerun()

            elif delete_task_click:
                st.session_state.show_delete_dropdown = True
                st.session_state.show_edit_dropdown = False
                st.session_state.show_move_dropdowns = False
                st.session_state.confirm_delete_list = False
                st.rerun()

            elif delete_list_click:
                if not st.session_state.confirm_delete_list:
                    st.session_state.confirm_delete_list = True
                    st.session_state.show_edit_dropdown = False
                    st.session_state.show_move_dropdowns = False
                    st.session_state.show_delete_dropdown = False
                    st.rerun()
                else:
                    st.session_state.tasks = []
                    st.session_state.current_index = 0
                    st.session_state.list_name = None
                    reset_transient_panels()
                    st.session_state.editing_index = None
                    st.session_state.edit_task_name = ""
                    st.session_state.edit_prereq_name = ""
                    st.session_state.form_version += 1
                    save_to_cloud()
                    st.rerun()

        # --- EDIT TASK PANEL ---
        if st.session_state.show_edit_dropdown and len(st.session_state.tasks) > 0:
            st.markdown("---")
            st.html(f"{STYLE_WRAPPER}<b>Select task number to load into editor:</b></div>")
            
            edit_col1, edit_col2 = st.columns([3, 1])
            max_tasks = len(st.session_state.tasks)
            
            with edit_col1:
                selected_edit_num = st.number_input(label="Select Task to Edit", min_value=1, max_value=max_tasks, step=1, key="edit_task_num", label_visibility="collapsed")
            
            with edit_col2:
                st.html("<div style='margin-top: 2px;'></div>") 
                if st.button("Load Task", key="btn_confirm_edit", use_container_width=True):
                    edit_idx = int(selected_edit_num) - 1
                    target_task = st.session_state.tasks[edit_idx]
                    
                    st.session_state.editing_index = edit_idx
                    st.session_state.edit_task_name = target_task["name"]
                    st.session_state.edit_prereq_name = target_task["prereq"] if target_task["prereq"] else ""
                    st.session_state.show_edit_dropdown = False
                    st.session_state.form_version += 1
                    st.rerun()

        # --- MOVE TASK PANEL ---
        if st.session_state.show_move_dropdowns and len(st.session_state.tasks) > 1:
            st.markdown("---")
            st.html(f"{STYLE_WRAPPER}<b>Rearrange Task Order:</b></div>")
            
            move_col1, move_col2, move_col3 = st.columns([1.5, 1.5, 1])
            max_tasks = len(st.session_state.tasks)
            
            with move_col1:
                st.html(f"{STYLE_WRAPPER}Move task number:</div>")
                from_num = st.number_input(label="From Position", min_value=1, max_value=max_tasks, step=1, key="move_from_num", label_visibility="collapsed")
                
            with move_col2:
                st.html(f"{STYLE_WRAPPER}To new position:</div>")
                to_num = st.number_input(label="To Position", min_value=1, max_value=max_tasks, step=1, key="move_to_num", label_visibility="collapsed")
            
            with move_col3:
                st.html("<div style='margin-top: 24px;'></div>") 
                if st.button("Confirm Move", key="btn_confirm_move", use_container_width=True):
                    if from_num != to_num:
                        from_idx = int(from_num) - 1
                        to_idx = int(to_num) - 1
                        
                        moved_task = st.session_state.tasks.pop(from_idx)
                        st.session_state.tasks.insert(to_idx, moved_task)
                        
                        if st.session_state.editing_index == from_idx:
                            st.session_state.editing_index = to_idx
                        
                        save_to_cloud()
                        st.session_state.show_move_dropdowns = False
                        st.rerun()
                        
        elif st.session_state.show_move_dropdowns and len(st.session_state.tasks) <= 1:
            st.sidebar.warning("You need at least 2 tasks in your list to rearrange them!")
            st.session_state.show_move_dropdowns = False

        # --- DELETE TASK PANEL ---
        if st.session_state.show_delete_dropdown and len(st.session_state.tasks) > 0:
            st.markdown("---")
            st.html(f"{STYLE_WRAPPER}Select task number to remove permanently:</div>")
            
            del_col1, del_col2 = st.columns([3, 1])
            max_tasks = len(st.session_state.tasks)
            
            with del_col1:
                selected_num = st.number_input(label="Select Task Number", min_value=1, max_value=max_tasks, step=1, key="delete_task_num", label_visibility="collapsed")
            
            with del_col2:
                st.html("<div style='margin-top: 2px;'></div>") 
                if st.button("Confirm Delete", key="btn_confirm_delete", use_container_width=True):
                    del_idx = int(selected_num) - 1
                    del st.session_state.tasks[del_idx]
                    
                    if st.session_state.editing_index == del_idx:
                        st.session_state.editing_index = None
                        st.session_state.edit_task_name = ""
                        st.session_state.edit_prereq_name = ""
                        st.session_state.form_version += 1
                    elif st.session_state.editing_index is not None and st.session_state.editing_index > del_idx:
                        st.session_state.editing_index -= 1
                        
                    save_to_cloud()
                    st.session_state.show_delete_dropdown = False
                    st.rerun()
        
        if len(st.session_state.tasks) > 0:
            st.html("<div style='display: flex; justify-content: center; margin-top: 25px;'>")
            if st.button("Start Working", key="start_working_big"):
                st.session_state.mode = "working"
                st.session_state.current_index = 0
                st.session_state.affirmation = None
                reset_transient_panels()
                st.rerun()
            st.html("</div>")

# --- MODE: WORKING ON TASKS ---
elif st.session_state.mode == "working":
    st.write("")
    st.write("")

    if len(st.session_state.tasks) > 0:
        if st.session_state.current_index >= len(st.session_state.tasks):
            st.session_state.current_index = 0

        current_task = st.session_state.tasks[st.session_state.current_index]
        
        st.html(f"<h1 style='text-align: center; margin-bottom: 20px; color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>{current_task['name']}</h1>")
        
        if current_task['prereq']:
            st.warning(f"⚠️ **Worth Noting:** \n\n  {current_task['prereq']}")
        
        st.write("")
        st.write("")

        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👍 Yes, I completed it!", use_container_width=True):
                del st.session_state.tasks[st.session_state.current_index]
                save_to_cloud()
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
            st.session_state.list_name = None
            reset_transient_panels()
            st.session_state.editing_index = None
            st.session_state.edit_task_name = ""
            st.session_state.edit_prereq_name = ""
            st.session_state.form_version += 1
            save_to_cloud()
            st.rerun()
