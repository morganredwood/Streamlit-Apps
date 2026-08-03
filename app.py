import streamlit as st
import json
import os
import random
from supabase import create_client, Client

# ==========================================
# CONFIG & CONSTANTS
# ==========================================
st.set_page_config(page_title="Executive Function Assistant", page_icon="🧠", layout="centered")

LIMIT = 1000

# ==========================================
# SUPABASE SETUP
# ==========================================
# Retrieve Supabase credentials from Streamlit secrets
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to initialize Supabase client: {e}")

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "user_key" not in st.session_state:
    st.session_state.user_key = ""
if "user_pin" not in st.session_state:
    st.session_state.user_pin = ""
if "list_name" not in st.session_state:
    st.session_state.list_name = "Main List"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "mode" not in st.session_state:
    st.session_state.mode = "adding"

if "editing_index" not in st.session_state:
    st.session_state.editing_index = None
if "edit_task_name" not in st.session_state:
    st.session_state.edit_task_name = ""
if "edit_prereq_name" not in st.session_state:
    st.session_state.edit_prereq_name = ""

if "form_version" not in st.session_state:
    st.session_state.form_version = 0
if "uploader_id" not in st.session_state:
    st.session_state.uploader_id = 0
if "import_success" not in st.session_state:
    st.session_state.import_success = False

if "show_bulk_delete" not in st.session_state:
    st.session_state.show_bulk_delete = False
if "show_edit_list_name" not in st.session_state:
    st.session_state.show_edit_list_name = False
if "show_new_list_input" not in st.session_state:
    st.session_state.show_new_list_input = False

if "shuffle_working" not in st.session_state:
    st.session_state.shuffle_working = False
if "working_indices" not in st.session_state:
    st.session_state.working_indices = []

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def reset_transient_panels():
    st.session_state.show_bulk_delete = False
    st.session_state.show_edit_list_name = False
    st.session_state.show_new_list_input = False

def get_available_lists(user_key):
    """Fetch all list names registered under the given user_key from Supabase."""
    if not supabase or not user_key:
        return ["Main List"]
    try:
        response = supabase.table("tasks_db").select("list_name").eq("user_key", user_key).execute()
        if response.data:
            lists = sorted(list(set(row["list_name"] for row in response.data if row.get("list_name"))))
            return lists if lists else ["Main List"]
    except Exception as e:
        st.sidebar.error(f"Error fetching cloud lists: {e}")
    return ["Main List"]

def fetch_cloud_data():
    """Load tasks and PIN from Supabase for current user_key and list_name."""
    if not supabase or not st.session_state.authenticated:
        return False
    try:
        response = supabase.table("tasks_db").select("*").eq("user_key", st.session_state.user_key).eq("list_name", st.session_state.list_name).execute()
        if response.data:
            record = response.data[0]
            # Verify PIN matches stored PIN for existing list
            stored_pin = str(record.get("pin", ""))
            if stored_pin and stored_pin != str(st.session_state.user_pin):
                st.sidebar.error("Incorrect PIN for this list!")
                return False
            
            loaded_tasks = record.get("tasks_data", [])
            st.session_state.tasks = loaded_tasks if isinstance(loaded_tasks, list) else []
            return True
        else:
            # If list row doesn't exist yet, start empty
            st.session_state.tasks = []
            return True
    except Exception as e:
        st.sidebar.error(f"Supabase Load Error: {e}")
        return False

def save_to_cloud():
    """Save current session tasks to Supabase for active user_key and list_name."""
    if not supabase or not st.session_state.authenticated:
        return False
    try:
        payload = {
            "user_key": st.session_state.user_key,
            "list_name": st.session_state.list_name,
            "pin": str(st.session_state.user_pin),
            "tasks_data": st.session_state.tasks
        }
        # Upsert requires unique constraint on (user_key, list_name)
        response = supabase.table("tasks_db").upsert(payload, on_conflict="user_key, list_name").execute()
        st.sidebar.success(f"Saved to cloud list: '{st.session_state.list_name}'!")
        return True
    except Exception as e:
        st.sidebar.error(f"Supabase Error: {e}")
        return False

def init_working_sequence():
    """Initialize working index order based on shuffle state."""
    indices = list(range(len(st.session_state.tasks)))
    if st.session_state.shuffle_working:
        random.shuffle(indices)
    st.session_state.working_indices = indices

# ==========================================
# SIDEBAR: AUTH & CLOUD LIST MANAGMENT
# ==========================================
with st.sidebar:
    st.header("☁️ Cloud Sync Login")
    
    passcode_input = st.text_input(
        "Enter Passcode:", 
        value=st.session_state.user_key, 
        type="default"
    )
    pin_input = st.text_input(
        "Enter 4-Digit PIN:", 
        value=st.session_state.user_pin, 
        type="password", 
        max_chars=4
    )
    
    if st.button("🔒 Sync / Authenticate"):
        if passcode_input.strip() and pin_input.strip():
            st.session_state.user_key = passcode_input.strip()
            st.session_state.user_pin = pin_input.strip()
            st.session_state.authenticated = True
            
            # Fetch available lists for this authentication key
            avail = get_available_lists(st.session_state.user_key)
            if st.session_state.list_name not in avail:
                st.session_state.list_name = avail[0]
            
            fetch_cloud_data()
            st.rerun()
        else:
            st.error("Please enter both Passcode and PIN.")

    if st.session_state.authenticated:
        st.markdown("---")
        st.subheader("📋 Cloud List Selector")
        
        avail_lists = get_available_lists(st.session_state.user_key)
        current_active = st.session_state.list_name
        
        # Keep dropdown selectbox state in sync
        if "cloud_list_selector" not in st.session_state or st.session_state.cloud_list_selector not in avail_lists:
            st.session_state.cloud_list_selector = current_active if current_active in avail_lists else avail_lists[0]

        selected_cloud_list = st.selectbox(
            "Select Active Cloud List:",
            options=avail_lists,
            index=avail_lists.index(st.session_state.cloud_list_selector) if st.session_state.cloud_list_selector in avail_lists else 0,
            key="cloud_list_selector"
        )

        # Switch lists if selectbox selection changes
        if selected_cloud_list != st.session_state.list_name:
            st.session_state.list_name = selected_cloud_list
            fetch_cloud_data()
            st.session_state.current_index = 0
            st.rerun()

        # Action Buttons for List Management
        col_list1, col_list2 = st.columns(2)
        with col_list1:
            if st.button("➕ New List"):
                st.session_state.show_new_list_input = not st.session_state.show_new_list_input
                st.session_state.show_edit_list_name = False
        with col_list2:
            if st.button("✏️ Rename"):
                st.session_state.show_edit_list_name = not st.session_state.show_edit_list_name
                st.session_state.show_new_list_input = False

        # Input to Create New Cloud List
        if st.session_state.show_new_list_input:
            new_name = st.text_input("New List Name:", key="new_list_name_input")
            if st.button("Confirm Create List"):
                cleaned_name = new_name.strip()
                if cleaned_name:
                    st.session_state.list_name = cleaned_name
                    st.session_state.tasks = []
                    st.session_state.cloud_list_selector = cleaned_name
                    st.session_state.show_new_list_input = False
                    save_to_cloud()
                    st.rerun()

        # Input to Rename Active Cloud List
        if st.session_state.show_edit_list_name:
            renamed = st.text_input("Rename Current List:", value=st.session_state.list_name, key="rename_list_input")
            if st.button("Confirm Rename"):
                cleaned_rename = renamed.strip()
                if cleaned_rename and cleaned_rename != st.session_state.list_name:
                    # Delete old record in DB if exists and write new list name
                    if supabase:
                        try:
                            supabase.table("tasks_db").delete().eq("user_key", st.session_state.user_key).eq("list_name", st.session_state.list_name).execute()
                        except Exception as e:
                            st.error(f"Error cleaning up old list name: {e}")
                    st.session_state.list_name = cleaned_rename
                    st.session_state.cloud_list_selector = cleaned_rename
                    st.session_state.show_edit_list_name = False
                    save_to_cloud()
                    st.rerun()

        st.markdown("---")
        # ==========================================
        # WORKSPACE BACKUP (IMPORT / EXPORT)
        # ==========================================
        st.subheader("💾 Workspace Backup")
        
        # Export Button
        export_json = json.dumps(st.session_state.tasks, indent=2)
        st.download_button(
            label="📤 Export Active List (.json)",
            data=export_json,
            file_name=f"{st.session_state.list_name}.json",
            mime="application/json",
            disabled=len(st.session_state.tasks) == 0
        )
        
        # JSON Import File Uploader
        uploaded_file = st.file_uploader(
            "📥 Select Saved List (.json)", 
            type=["json"], 
            key=f"uploader_{st.session_state.uploader_id}"
        )
        
        if uploaded_file is not None:
            try:
                imported_data = json.load(uploaded_file)
                if isinstance(imported_data, list):
                    num_imported = len(imported_data)
                    
                    if num_imported > LIMIT:
                        st.error(f"Cannot import: File contains {num_imported} tasks (Limit is {LIMIT}).")
                    else:
                        col_imp1, col_imp2 = st.columns(2)
                        replace_clicked = col_imp1.button("Upload: Replace")
                        combine_clicked = col_imp2.button("Upload: Combine")

                        if replace_clicked:
                            st.session_state.tasks = imported_data
                            st.session_state.current_index = 0
                            st.session_state.mode = "adding"
                            st.session_state.uploader_id += 1
                            reset_transient_panels()
                            
                            # Update list name from filename automatically
                            base_name, _ = os.path.splitext(uploaded_file.name)
                            st.session_state.list_name = base_name
                            st.session_state.cloud_list_selector = base_name

                            # Sync to cloud; rerun only on successful save
                            if save_to_cloud():
                                st.rerun()

                        if combine_clicked:
                            combined = st.session_state.tasks + imported_data
                            if len(combined) > LIMIT:
                                st.error(f"Combining would exceed the {LIMIT} task limit!")
                            else:
                                st.session_state.tasks = combined
                                st.session_state.uploader_id += 1
                                reset_transient_panels()
                                
                                if save_to_cloud():
                                    st.rerun()
                else:
                    st.error("Invalid JSON format. File must contain a list of task objects.")
            except Exception as e:
                st.error(f"Error reading JSON file: {e}")

# ==========================================
# MAIN CONTENT AREA
# ==========================================
st.title("🧠 Executive Function Assistant")
st.subheader(f"Active List: **{st.session_state.list_name}**")

# Mode Selection Tabs / Toggles
mode_col1, mode_col2, mode_col3 = st.columns(3)
with mode_col1:
    if st.button("➕ Add / Manage Tasks", use_container_width=True):
        st.session_state.mode = "adding"
        reset_transient_panels()
        st.rerun()

with mode_col2:
    if st.button("⚡ Working Mode", use_container_width=True):
        st.session_state.mode = "working"
        init_working_sequence()
        reset_transient_panels()
        st.rerun()

with mode_col3:
    if st.button("🧹 Clear / Manage List", use_container_width=True):
        st.session_state.show_bulk_delete = not st.session_state.show_bulk_delete
        st.rerun()

st.markdown("---")

# ==========================================
# MODE 1: ADDING / EDITING / MANAGE TASKS
# ==========================================
if st.session_state.mode == "adding":
    st.header("Task Entry & Management")
    
    # Task Addition Form
    with st.form(key=f"add_task_form_{st.session_state.form_version}"):
        task_input = st.text_input("Task Name:")
        prereq_input = st.text_input("Prerequisite Task (Optional):")
        submit_add = st.form_submit_button("Add Task")

        if submit_add:
            if not task_input.strip():
                st.warning("Please enter a task name.")
            elif len(st.session_state.tasks) >= LIMIT:
                st.error(f"Task limit of {LIMIT} reached!")
            else:
                new_task = {
                    "name": task_input.strip(),
                    "prereq": prereq_input.strip() if prereq_input.strip() else None,
                    "completed": False
                }
                st.session_state.tasks.append(new_task)
                st.session_state.form_version += 1
                save_to_cloud()
                st.rerun()

    # Bulk Delete Panel
    if st.session_state.show_bulk_delete:
        st.warning("⚠️ Clear List Actions")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("Delete ALL Tasks", type="primary"):
                st.session_state.tasks = []
                st.session_state.current_index = 0
                st.session_state.show_bulk_delete = False
                save_to_cloud()
                st.rerun()
        with col_del2:
            if st.button("Cancel"):
                st.session_state.show_bulk_delete = False
                st.rerun()

    # Task List Display & In-line Editing
    st.subheader(f"Current Tasks ({len(st.session_state.tasks)} / {LIMIT})")
    
    if not st.session_state.tasks:
        st.info("No tasks in this list yet.")
    else:
        for idx, task in enumerate(st.session_state.tasks):
            col_t1, col_t2, col_t3 = st.columns([5, 1, 1])
            
            with col_t1:
                prereq_str = f" *(Prereq: {task['prereq']})*" if task.get("prereq") else ""
                status_str = "✅ " if task.get("completed") else "🔲 "
                st.markdown(f"{status_str} **{idx + 1}. {task['name']}**{prereq_str}")

            with col_t2:
                if st.button("Edit", key=f"edit_btn_{idx}"):
                    st.session_state.editing_index = idx
                    st.session_state.edit_task_name = task["name"]
                    st.session_state.edit_prereq_name = task.get("prereq") or ""
                    st.rerun()

            with col_t3:
                if st.button("❌", key=f"del_btn_{idx}"):
                    st.session_state.tasks.pop(idx)
                    save_to_cloud()
                    st.rerun()

            # Display Inline Edit Sub-form
            if st.session_state.editing_index == idx:
                with st.form(key=f"edit_form_{idx}"):
                    new_name = st.text_input("Task Name:", value=st.session_state.edit_task_name)
                    new_prereq = st.text_input("Prerequisite:", value=st.session_state.edit_prereq_name)
                    save_edit = st.form_submit_button("Save Changes")

                    if save_edit:
                        if new_name.strip():
                            st.session_state.tasks[idx]["name"] = new_name.strip()
                            st.session_state.tasks[idx]["prereq"] = new_prereq.strip() if new_prereq.strip() else None
                            st.session_state.editing_index = None
                            save_to_cloud()
                            st.rerun()

# ==========================================
# MODE 2: WORKING MODE
# ==========================================
elif st.session_state.mode == "working":
    st.header("⚡ Focus / Working Mode")

    # Toggle for Randomizing Task Order
    shuffle_toggle = st.toggle("🔀 Randomize Working Order", value=st.session_state.shuffle_working)
    if shuffle_toggle != st.session_state.shuffle_working:
        st.session_state.shuffle_working = shuffle_toggle
        init_working_sequence()
        st.rerun()

    if not st.session_state.tasks:
        st.info("No tasks available to work on.")
    else:
        # Check active indices range
        if not st.session_state.working_indices or len(st.session_state.working_indices) != len(st.session_state.tasks):
            init_working_sequence()

        idx = st.session_state.current_index
        if 0 <= idx < len(st.session_state.working_indices):
            actual_task_idx = st.session_state.working_indices[idx]
            current_task = st.session_state.tasks[actual_task_idx]

            st.markdown(f"### Current Step ({idx + 1} of {len(st.session_state.tasks)})")
            
            # Highlight Card
            st.info(f"### 🎯 Task: **{current_task['name']}**")
            if current_task.get("prereq"):
                st.warning(f"⚠️ **Prerequisite First:** {current_task['prereq']}")

            # Completion Checkbox
            completed = st.checkbox("Mark as Completed", value=current_task.get("completed", False))
            if completed != current_task.get("completed", False):
                st.session_state.tasks[actual_task_idx]["completed"] = completed
                save_to_cloud()

            # Navigation Controls
            col_nav1, col_nav2 = st.columns(2)
            with col_nav1:
                if st.button("⬅️ Previous Task", disabled=(idx == 0)):
                    st.session_state.current_index -= 1
                    st.rerun()
            with col_nav2:
                if st.button("Next Task ➡️", disabled=(idx >= len(st.session_state.tasks) - 1)):
                    st.session_state.current_index += 1
                    st.rerun()
                    