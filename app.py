import streamlit as st
import json
from streamlit_local_storage import LocalStorage

# --- PAGE CONFIGURATION & STYLING ---
st.set_page_config(page_title="Executive Function Assistant", layout="wide")

# Custom Typography Setup (Georgia Font & Spacing)
STYLE_WRAPPER = """
<div style="
    font-family: 'Georgia', serif; 
    line-height: 1.5; 
    font-size: 1.1rem;
">
"""

st.markdown("""
    <style>
    /* Global Georgia font application */
    html, body, [data-testid="stWidgetLabel"] p, .stSelectbox label {
        font-family: 'Georgia', serif !important;
    }
    
    /* Button Color Theme Matrix */
    div.stButton > button[key^="add_"] {
        background-color: #4A90E2 !important; /* Blue */
        color: white !important;
    }
    div.stButton > button[key^="move_"] {
        background-color: #F5A623 !important; /* Orange/Amber */
        color: white !important;
    }
    div.stButton > button[key^="del_"] {
        background-color: #D0021B !important; /* Crimson Red */
        color: white !important;
    }
    div.stButton > button[key^="start_"] {
        background-color: #417505 !important; /* Forest Green */
        color: white !important;
    }
    div.stButton > button[key^="clear_"] {
        background-color: #7ED321 !important; /* Light Green */
        color: white !important;
    }
    
    /* Hover effects for buttons */
    div.stButton > button:hover {
        opacity: 0.85 !important;
        transform: scale(1.01);
        transition: all 0.1s ease-in-out;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. PRIVACY-SECURE BROWSER LOCAL STORAGE SETUP ---
# Initializes the connection to the visitor's individual browser cache
local_storage = LocalStorage()

def load_tasks_from_file():
    """Reads tasks directly from the visitor's private browser memory."""
    try:
        saved_data = local_storage.getItem("my_private_tasks")
        if saved_data:
            return json.loads(saved_data)
    except Exception:
        pass
    return []

def save_tasks_to_file():
    """Saves tasks directly down to the visitor's private browser memory."""
    try:
        tasks_json = json.dumps(st.session_state.tasks)
        local_storage.setItem("my_private_tasks", tasks_json)
    except Exception:
        pass

# --- INITIALIZE SESSION STATE ---
if "tasks" not in st.session_state:
    # First boot attempt to read from the visitor's browser local storage
    st.session_state.tasks = load_tasks_from_file()

if "mode" not in st.session_state:
    st.session_state.mode = "adding"  # Options: "adding", "working"

if "working_index" not in st.session_state:
    st.session_state.working_index = 0

if "confirm_delete_list" not in st.session_state:
    st.session_state.confirm_delete_list = False

# --- APP HEADER ---
st.html(f"{STYLE_WRAPPER}<h1>✨ Executive Function Task Assistant</h1></div>")
st.write("---")

# --- 2. MODE: ADDING TASKS ---
if st.session_state.mode == "adding":
    
    # Establish a clean layout grid
    left_col, right_col = st.columns([1, 1.5], gap="large")

    with left_col:
        st.html(f"{STYLE_WRAPPER}<b>📋 Full Task List</b></div><br>")
        
        # Native, scroll-locked container window that retains its position 
        with st.container(height=400):
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
            if st.sidebar.button("Yes, Nuke the Entire List", key="del_confirm_nuke"):
                st.session_state.tasks = []
                save_tasks_to_file()
                st.session_state.confirm_delete_list = False
                st.rerun()
            if st.sidebar.button("Cancel", key="add_cancel_nuke"):
                st.session_state.confirm_delete_list = False
                st.rerun()

    with right_col:
        st.html(f"{STYLE_WRAPPER}<b>🛠️ Build Your List</b></div><br>")
        
        # Action A: Add Tasks Form
        with st.form("add_task_form", clear_on_submit=True):
            new_task = st.text_input("What is the next task step?")
            
            # Dynamically compute valid prerequisites from the current task names
            task_options = ["None"] + [t["name"] for t in st.session_state.tasks]
            prereq = st.selectbox("Does this task require another task to be completed first?", options=task_options)
            
            submit_add = st.form_submit_button("Add Task Step", key="add_task_submit")
            
            if submit_add and new_task.strip():
                chosen_prereq = None if prereq == "None" else prereq
                st.session_state.tasks.append({"name": new_task.strip(), "prereq": chosen_prereq})
                save_tasks_to_file()
                st.rerun()

        st.write("---")

        # Action B: Rearrange Task Order
        if len(st.session_state.tasks) > 1:
            with st.expander("🔄 Rearrange Task Order"):
                task_to_move = st.selectbox("Select task to move:", 
                                            options=range(1, len(st.session_state.tasks) + 1),
                                            format_func=lambda x: f"{x}. {st.session_state.tasks[x-1]['name']}")
                
                target_position = st.selectbox("Move to position:", 
                                               options=range(1, len(st.session_state.tasks) + 1),
                                               index=task_to_move-1)
                
                if st.button("Execute Move", key="move_execute"):
                    # Adjust index arrays natively
                    task = st.session_state.tasks.pop(task_to_move - 1)
                    st.session_state.tasks.insert(target_position - 1, task)
                    save_tasks_to_file()
                    st.rerun()

        # Action C: Delete Single Task
        if len(st.session_state.tasks) > 0:
            with st.expander("🗑️ Delete a Task Step"):
                task_to_delete = st.selectbox("Select task to delete:", 
                                              options=range(1, len(st.session_state.tasks) + 1),
                                              format_func=lambda x: f"{x}. {st.session_state.tasks[x-1]['name']}")
                if st.button("Delete Selected Task", key="del_single_task"):
                    st.session_state.tasks.pop(task_to_delete - 1)
                    save_tasks_to_file()
                    st.rerun()

        st.write("---")

        # Workflow Control Grid
        control_col1, control_col2 = st.columns(2)
        with control_col1:
            if st.button("🚀 Start Working", key="start_engine", use_container_width=True):
                if len(st.session_state.tasks) > 0:
                    st.session_state.mode = "working"
                    st.session_state.working_index = 0
                    st.rerun()
                else:
                    st.warning("Please add at least one task step before starting.")
                    
        with control_col2:
            if len(st.session_state.tasks) > 0:
                if st.button("🗑️ Delete Whole List", key="del_nuke_trigger", use_container_width=True):
                    st.session_state.confirm_delete_list = True
                    st.rerun()

# --- 3. MODE: WORKING ACTIVE CONTEXT ---
elif st.session_state.mode == "working":
    if st.session_state.working_index < len(st.session_state.tasks):
        current_task = st.session_state.tasks[st.session_state.working_index]
        
        # Safety Check: Is there an unfinished prerequisite?
        unfinished_prereq = None
        if current_task["prereq"]:
            # Scan all preceding items to check if the dependency has been checked off yet
            for idx, t in enumerate(st.session_state.tasks):
                if t["name"] == current_task["prereq"] and idx >= st.session_state.working_index:
                    unfinished_prereq = current_task["prereq"]
                    break

        # Display the single, hyper-focused working block
        st.html(f"""
        {STYLE_WRAPPER}
        <div style="background-color: #f9f9f9; padding: 25px; border-radius: 10px; border-left: 5px solid #417505;">
            <p style="font-size: 0.9rem; color: #666; margin: 0;">CURRENT ACTIVE TASK STEP ({st.session_state.working_index + 1} of {len(st.session_state.tasks)})</p>
            <h2 style="margin: 10px 0 5px 0; color: #111;">{current_task['name']}</h2>
        </div>
        </div>
        """)
        
        if unfinished_prereq:
            st.warning(f"⚠️ **Focus Blocked**: This task requires **'{unfinished_prereq}'** to be completed first, which is further down the list. Use the button below to skip this for now, or return to edit mode to reorder your steps.")

        st.write("")

        # Action Execution Grid
        work_col1, work_col2, work_col3 = st.columns(3)
        with work_col1:
            if st.button("✅ Mark Complete", key="start_complete", use_container_width=True):
                # Pop it completely out of existence
                st.session_state.tasks.pop(st.session_state.working_index)
                save_tasks_to_file()
                # Do not increment index because the next item naturally drops down into the current slot
                st.rerun()
                
        with work_col2:
            if st.button("⏭️ Skip Step for Now", key="add_skip", use_container_width=True):
                st.session_state.working_index += 1
                st.rerun()
                
        with work_col3:
            if st.button("🛠️ Return to Edit List", key="clear_return", use_container_width=True):
                st.session_state.mode = "adding"
                st.rerun()
                
    else:
        # End of the active session sequence loop
        st.balloons()
        st.html(f"{STYLE_WRAPPER}<h2>🎉 All caught up! Outstanding job!</h2></div>")
        st.write("You skipped or completed everything in your immediate working sequence.")
        
        if st.button("Back to Task Builder", key="clear_finish_return"):
            st.session_state.mode = "adding"
            st.session_state.working_index = 0
            st.rerun()
