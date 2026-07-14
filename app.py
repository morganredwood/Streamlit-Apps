import streamlit as st
import json
import random
import streamlit.components.v1 as components
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
# 🌐 BROWSER-BASED HIGH-CAPACITY STORAGE BRIDGE (WIPE-PROOF)
# ==============================================================================
# 1. Initialize our session states safely
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "storage_initialized" not in st.session_state:
    st.session_state.storage_initialized = False
if "sync_trigger" not in st.session_state:
    st.session_state.sync_trigger = False

def save_tasks_to_browser():
    """Triggers the JavaScript side to save the current task state to browser storage."""
    # Crucial safety check: Never write to storage if we haven't successfully loaded yet!
    if st.session_state.storage_initialized:
        st.session_state.sync_trigger = True

# 2. Inject the background bridge
# This script reads from localStorage ONCE on startup. If it finds data, it sends it back.
# If it finds nothing, it declares initialization complete so we can start writing.
browser_data = components.html(
    f"""
    <script>
    const STORAGE_KEY = "executive_function_tasks";
    
    // Send data from browser back to Streamlit
    function sendToStreamlit(val) {{
        window.parent.postMessage({{
            type: "streamlit:setComponentValue",
            value: val
        }}, "*");
    }}

    // Check if we have an active save command from Python
    const shouldSave = {json.dumps(st.session_state.sync_trigger)};
    const initialized = {json.dumps(st.session_state.storage_initialized)};

    if (shouldSave && initialized) {{
        // Save Python's current state to the browser
        localStorage.setItem(STORAGE_KEY, JSON.stringify({json.dumps(st.session_state.tasks)}));
    }}

    // Read the current local storage state to feed back into Python
    try {{
        const data = localStorage.getItem(STORAGE_KEY);
        if (data) {{
            sendToStreamlit({{ "status": "loaded", "data": JSON.parse(data) }});
        }} else {{
            sendToStreamlit({{ "status": "empty", "data": [] }});
        }}
    }} catch (e) {{
        sendToStreamlit({{ "status": "error", "data": [] }});
    }}
    </script>
    """,
    height=0,
)

# 3. Process the bridge payload safely
if browser_data is not None and not st.session_state.storage_initialized:
    # Only load the data if the bridge successfully returned our startup payload
    payload = browser_data
    if isinstance(payload, dict) and "status" in payload:
        if payload["status"] in ["loaded", "empty"]:
            st.session_state.tasks = payload["data"]
            st.session_state.storage_initialized = True
            st.rerun()  # Rerun once to make sure the UI displays the loaded tasks immediately

# Reset the write trigger flag safely for the next interaction
st.session_state.sync_trigger = False
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

# Safe high limit supported by native browser local storage
LIMIT = 500

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

            # Clean 4-column row layout for button alignment
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

        # --- MOVE TASK SECTION ---
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
                        
                        save_tasks_to_browser()
                        st.session_state.show_move_dropdowns = False
                        st.rerun()
                        
        elif st.session_state.show_move_dropdowns and len(st.session_state.tasks) <= 1:
            st.sidebar.warning("You need at least 2 tasks in your list to rearrange them!")
            st.session_state.show_move_dropdowns = False

        # --- DELETE SINGLE TASK SECTION ---
        if st.session_state.show_delete_dropdown and len(st.session_state.tasks) > 0:
            st.markdown("---")
            st.html(f"{STYLE_WRAPPER}Select task number to remove permanently:</div>")
            
            del_col1, del_col2 = st.columns([3, 1])
            max_tasks = len(st.session_state.tasks)
            
            with del_col1:
                selected_num = st.number_input(label="Select Task Number", min_value=1, max_value=max_tasks, step=1, key="delete_task_num", label_visibility="collapsed")
            
            with del_col2:
                st.html("<div style='margin-top: 5px;'></div>") 
                if st.button("Confirm Delete", key="btn_confirm_delete", use_container_width=True):
                    del_idx = int(selected_num) - 1
                    del st.session_state.tasks[del_idx]
                    save_tasks_to_browser()
                    st.session_state.show_delete_dropdown = False
                    st.rerun()
        
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
