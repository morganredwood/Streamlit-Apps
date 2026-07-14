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
        # Check if global design limits are set, if not, fallback safely
        if 'LIMIT' not in locals():
            LIMIT = 50 
        if 'TEXT_COLOR' not in locals():
            TEXT_COLOR = "#333333"

        st.html(f"<h2 style='text-align: center; margin-bottom: 20px; color: {TEXT_COLOR}; font-family: {'Georgia'};'>Build Your List</h2>", unsafe_allow_html=True)
        st.html(f"{STYLE_WRAPPER}Current task count: {len(st.session_state.tasks)} / {LIMIT}</div><br>", unsafe_allow_html=True)

        with st.form(key="input_form", clear_on_submit=True):
            st.html(f"<div style='color: {'purple'}; font-family: {'Georgia'};'>Enter a task you would like to add:</div>", unsafe_allow_html=True)
            task_text = st.text_input(label="Task Input", label_visibility="collapsed")
            
            st.html(f"<div style='color: {'gray'}; font-family: {'Georgia'};'>What must be completed first? (Optional)</div>", unsafe_allow_html=True)
            prereq_text = st.text_input(label="Prerequisite Input", label_visibility="collapsed")

            # Updated into a 4-column row with keys assigned for perfect color targeting
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
            
            with btn_col1:
                submit_task = st.form_submit_button("Add Task", key="add_btn")

            with btn_col2:
                move_task_click = st.form_submit_button("Move Task", key="move_btn")
                if move_task_click:
                    st.session_state.show_move_dropdowns = True
                    st.session_state.show_delete_dropdown = False
                    st.session_state.force_expand_list = True

            with btn_col3:
                delete_task_click = st.form_submit_button("Delete Task", key="del_btn")
                if delete_task_click:
                    st.session_state.show_delete_dropdown = True
                    st.session_state.show_move_dropdowns = False
                    st.session_state.force_expand_list = True

            with btn_col4:
                black_btn_label = "Yes, All" if st.session_state.confirm_delete_list else "Delete List"
                delete_list_click = st.form_submit_button(black_btn_label, key="del_list_btn")
                if delete_list_click:
                    if not st.session_state.confirm_delete_list:
                        st.session_state.confirm_delete_list = True
                        st.rerun()
                    else:
                        st.session_state.tasks = []
                        st.session_state.working_index = 0  # Aligned to match your workspace state
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
            """, unsafe_allow_html=True)
            if st.button("Go Back", key="go_back_btn"):
                st.session_state.confirm_delete_list = False
                st.session_state.show_delete_dropdown = False
                st.session_state.show_move_dropdowns = False
                st.rerun()
            st.html("<script>document.getElementById('root').querySelector('button:has(div:contains(\"Go Back\"))').classList.add('giant-goback-btn');</script>", unsafe_allow_html=True)

        # --- MOVE TASK DROPDOWNS ---
        if st.session_state.show_move_dropdowns and len(st.session_state.tasks) > 1:
            st.markdown("---")
            st.html(f"{STYLE_WRAPPER}<b>Rearrange Task Order:</b></div>", unsafe_allow_html=True)
            
            move_col1, move_col2 = st.columns(2)
            task_numbers = [str(i) for i in range(1, len(st.session_state.tasks) + 1)]
            
            with move_col1:
                st.html(f"{STYLE_WRAPPER}Move task number:</div>", unsafe_allow_html=True)
                from_num = st.selectbox(label="From Position", options=["Choose..."] + task_numbers, key="move_from_drop", label_visibility="collapsed")
                
            with move_col2:
                st.html(f"{STYLE_WRAPPER}To new position:</div>", unsafe_allow_html=True)
                to_num = st.selectbox(label="To Position", options=["Choose..."] + task_numbers, key="move_to_drop", label_visibility="collapsed")
            
            if from_num != "Choose..." and to_num != "Choose...":
                if from_num != to_num:
                    from_idx = int(from_num) - 1
                    to_idx = int(to_num) - 1
                    
                    moved_task = st.session_state.tasks.pop(from_idx)
                    st.session_state.tasks.insert(to_idx, moved_task)
                    
                    save_tasks_to_file()
                    st.session_state.show_move_dropdowns = False
                    st.rerun()
        elif st.session_state.show_move_dropdowns and len(st.session_state.tasks) <= 1:
            st.sidebar.warning("You need at least 2 tasks in your list to rearrange them!")
            st.session_state.show_move_dropdowns = False

        if st.session_state.show_delete_dropdown and len(st.session_state.tasks) > 0:
            st.html(f"{STYLE_WRAPPER}Select task number to remove permanently:</div>", unsafe_allow_html=True)
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
            st.html("<div style='display: flex; justify-content: center; margin-top: 25px;'>", unsafe_allow_html=True)
            if st.button("Start Working", key="start_start_engine_big"): # Updated key to trigger green button style matrix
                st.session_state.mode = "working"
                st.session_state.working_index = 0  # Aligned to match your active workspace state
                st.session_state.affirmation = None
                st.rerun()
            st.html("</div>", unsafe_allow_html=True)

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
