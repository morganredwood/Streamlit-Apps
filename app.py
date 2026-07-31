import streamlit as st
import random
from supabase import create_client, Client

# ==============================================================================
# 🌐 SUPABASE CLOUD DATABASE CONFIGURATION
# ==============================================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception as e:
    SUPABASE_URL = ""
    SUPABASE_KEY = ""

@st.cache_resource
def init_supabase() -> Client:
    """Initializes and caches the Supabase database connection."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in st.secrets.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize database connection safely
supabase = None
try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"⚠️ Supabase Connection Warning: {e}")

# ==============================================================================
# 🗄️ SUPABASE HELPER FUNCTIONS (LOAD & SAVE)
# ==============================================================================
def load_tasks_from_supabase(passcode: str):
    """Loads tasks matching the user's passcode from Supabase."""
    if not supabase or not passcode:
        return
    try:
        response = supabase.table("tasks_db").select("task_data").eq("passcode", passcode).execute()
        if response.data:
            st.session_state.tasks = response.data[0].get("task_data", [])
        else:
            # New passcode; start with an empty list
            st.session_state.tasks = []
    except Exception as e:
        st.error(f"Error loading tasks from cloud: {e}")

def save_tasks_to_supabase(passcode: str):
    """Saves/upserts the current task list to Supabase for the active passcode."""
    if not supabase or not passcode:
        return
    try:
        data = {
            "passcode": passcode,
            "task_data": st.session_state.tasks
        }
        supabase.table("tasks_db").upsert(data, on_conflict="passcode").execute()
    except Exception as e:
        st.error(f"Error saving tasks to cloud: {e}")

# ==============================================================================
# 🗂️ GLOBAL STATE INITIALIZATIONS
# ==============================================================================
if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "list_name" not in st.session_state:
    st.session_state.list_name = None

if "user_passcode" not in st.session_state:
    st.session_state.user_passcode = ""

if "uploader_id" not in st.session_state:
    st.session_state.uploader_id = ""

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
# 🔐 SIDEBAR PASSCODE PERSISTENCE & CLOUD SYNC
# ==============================================================================
passcode_input = st.sidebar.text_input(
    "Enter Passcode / User ID", 
    value=st.session_state.user_passcode,
    key="user_passcode_widget",
    help="Enter a unique key to load and auto-sync your tasks across sessions."
)

# Detect when the passcode changes or is submitted
if passcode_input != st.session_state.user_passcode:
    st.session_state.user_passcode = passcode_input
    st.session_state.uploader_id = passcode_input
    
    if passcode_input.strip():
        load_tasks_from_supabase(passcode_input.strip())
        st.rerun()

if st.session_state.user_passcode:
    st.sidebar.success(f"🟢 Synced as: **{st.session_state.user_passcode}**")
else:
    st.sidebar.info("💡 Enter a passcode above to save tasks to the cloud.")

# ==============================================================================
# 🎨 CENTRAL STYLE CONFIGURATION & PAGE LAYOUT
# ==============================================================================
st.title("Executive Function Assistant")

# Display notification banner if an affirmation is active
if st.session_state.affirmation:
    st.success(st.session_state.affirmation)

# Main container for the task list display
st.subheader("📋 Current Task List")

if len(st.session_state.tasks) == 0:
    st.write("Your list is currently empty.")
else:
    for idx, task_item in enumerate(st.session_state.tasks):
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(f"**{idx + 1}. {task_item}**")
        if col2.button("Done", key=f"done_{idx}"):
            st.session_state.tasks.pop(idx)
            st.session_state.affirmation = random.choice(AFFIRMATIONS)
            save_tasks_to_supabase(st.session_state.user_passcode)
            st.rerun()

st.write("---")

# ==============================================================================
# ✍️ TASK ENTRY FORM (PERSISTENT FOCUS & ENTER-KEY SUPPORT)
# ==============================================================================
with st.form(key=f"add_task_form_{st.session_state.form_version}", clear_on_submit=True):
    new_task = st.text_input("Enter a task you need to complete:")
    submitted = st.form_submit_button("Add Task")

    if submitted:
        task_text = new_task.strip()
        if task_text:
            if len(st.session_state.tasks) < 500:
                st.session_state.tasks.append(task_text)
                st.session_state.affirmation = None  # Clear old affirmation on new entry
                save_tasks_to_supabase(st.session_state.user_passcode)
                st.rerun()
            else:
                st.error("Task limit reached (500 maximum).")
                