import streamlit as st
import os
import pickle

STATE_FILE = "task_manager_backup.pkl"

st.title("Executive Function Assistant\n"
"Feel free to brain dump up to 50 tasks. Select 'Yes' from the drop-down menu to specify a prerequisite.")

# --- 1. MEMORY SETUP ---
# Auto-loads local file backup if it exists on disk
if "tasks" not in st.session_state:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            st.session_state.tasks = pickle.load(f)
    else:
        st.session_state.tasks = []  

if "current_index" not in st.session_state:
    if os.path.exists(STATE_FILE):
        # Keeps your position if the app reloads mid-work
        st.session_state.current_index = 0
    else:
        st.session_state.current_index = 0  

if "mode" not in st.session_state:
    st.session_state.mode = "adding"  

LIMIT = 50

# Helper function to auto-save to disk instantly
def save_tasks_locally():
    with open(STATE_FILE, "wb") as f:
        pickle.dump(st.session_state.tasks, f)

# --- 2. MODE: ADDING TASKS ---
if st.session_state.mode == "adding":
    
    left_col, right_col = st.columns([1, 1.5], gap="large")

    # --- LEFT COLUMN: THE EXPANDABLE LIST ---
    with left_col:
        with st.expander("📋 View / Hide Full Task List", expanded=True):
            if len(st.session_state.tasks) > 0:
                for i, t in enumerate(st.session_state.tasks, 1):
                    if t["prereq"]:
                        st.write(f"{i}. **{t['name']}** \n*(Requires: {t['prereq']})*")
                    else:
                        st.write(f"{i}. **{t['name']}**")
            else:
                st.write("Your list is currently empty.")

   # --- RIGHT COLUMN: THE INPUT SECTION ---
    with right_col:
        st.header("Step 1: Build Your List")
        st.write(f"Current task count: {len(st.session_state.tasks)} / {LIMIT}")

        # 1. Place the dropdown OUTSIDE the form so it is dynamic and interactive instantly
        has_prereq = st.selectbox(
            "Does this task have a prerequisite?", 
            ["No", "Yes"],
            key="has_prereq_select"
        )

        # 2. Start the form for the text entry and submission button
        with st.form(key="input_form", clear_on_submit=True):
            
            task_text = st.text_input("Enter a task you would like to add:")

            # If they selected "Yes" above, this box displays inside the form immediately
            prereq_text = ""
            if has_prereq == "Yes":
                prereq_text = st.text_input("What must be completed first?")

            submit_task = st.form_submit_button("Add Task")

            if submit_task:
                task_text_cleaned = task_text.strip()
                if task_text_cleaned != "":
                    if len(st.session_state.tasks) < LIMIT:
                        
                        task_data = {
                            "name": task_text_cleaned,
                            "prereq": prereq_text.strip() if has_prereq == "Yes" and prereq_text.strip() else None
                        }
                        st.session_state.tasks.append(task_data)
                        
                        # Save backup immediately to your hard drive
                        save_tasks_locally()
                        st.rerun()
                    else:
                        st.sidebar.error("You have reached the task limit of 50!")
                else:
                    st.sidebar.warning("Please type a task name first!")

        st.markdown("---")
        
        if len(st.session_state.tasks) > 0:
            if st.button("Finish Adding & Start Working"):
                st.session_state.mode = "working"
                st.session_state.current_index = 0
                st.rerun() 

# --- 3. MODE: WORKING ON TASKS ---
elif st.session_state.mode == "working":
    st.header("Step 2: Time to start working on tasks--Allons-y!\n\n I have not yet configured an update to delete unwanted tasks,"
    "so for now, please just mark them as completed if you realize you don't need them.")

    if len(st.session_state.tasks) > 0:
        if st.session_state.current_index >= len(st.session_state.tasks):
            st.session_state.current_index = 0

        current_task = st.session_state.tasks[st.session_state.current_index]
        
        st.subheader(f"Current Task: **{current_task['name']}**")
        if current_task['prereq']:
            st.info(f"⚠️ **Prerequisite reminder:** You need to finish this task first!: \n\n **{current_task['prereq']}**")

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("👍 Yes, I completed it!"):
                del st.session_state.tasks[st.session_state.current_index]
                
                # Auto-save changes locally after removing the completed item
                save_tasks_locally()
                
                if st.session_state.current_index >= len(st.session_state.tasks):
                    st.session_state.current_index = 0
                st.rerun()

        with col2:
            if st.button("👎 No, skip it for now"):
                st.session_state.current_index += 1
                if st.session_state.current_index >= len(st.session_state.tasks):
                    st.session_state.current_index = 0
                st.rerun()

    else:
        st.balloons()
        st.success("All tasks have been completed! Hooray!")
        
        if st.button("Restart Program"):
            st.session_state.tasks = []
            st.session_state.current_index = 0
            st.session_state.mode = "adding"
            
            # Wipe file local storage clean for a fresh restart
            save_tasks_locally()
            st.rerun()
