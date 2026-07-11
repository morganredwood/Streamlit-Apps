import streamlit as st
import json
import random
import os

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
    st.title("Executive Function Assistant")

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

if "affirmation" not in st.session_state:
    st.session_state.affirmation = None

LIMIT = 100

AFFIRMATIONS = [
    "✨ Fantastic job getting that done!",
    "🎉 Way to cross that off your list!",
    "⭐ You are capable and worthy of completing your tasks on time.",
    "⭐ You are confident in your abilities and trust yourself to get things done!",
    "🎉 You are determined to succeed and make progress!",
    "🎉 You are managing your time efficiently!",
    "🎉 Great job being proactive and taking initiative to complete your work!",
    "🎉 You are committed to taking action and making progress!",
    "🎉 You are determined to overcome procrastination and be productive!",
    "🏆 You are focused and staying on track to complete your tasks!",
    "🏆 You are disciplined and making the most of every moment!",
    "🏆 You are capable of making the necessary changes to be more productive!",
    "🏆 You are committed to taking control of your time and using it wisely!",
    "⚡ You are constantly seeking ways to improve your skills!",
    "⚡ You are focused on achieving excellence in your work!",
    "⚡ You are calm and confident amidst challenges!",
    "⚡ You set clear and achievable goals!",
    "⚡ You find creative solutions to complex challenges!",
    "⚡ You are capable of whatever you set your mind to!",
    "⚡ Your goals are clear, achievable, and motivating!",
    "⚡ Your skills and knowledge are expanding continually!",
    "🌈 You are a catalyst for positive progress!",
    "🌈 You honor your unique skills, interests, and talents!",
    "🌈 You work with integrity and intention!",
    "🌈 Be like a postage stamp: stick to one thing until you get there. -- Josh Billings",
    "🌈 You can do two things at once, but you can't focus effectively on two things at once. -- Gary Keller",
    "🌈 Should you find yourself in a chronically leaking boat, energy devoted to changing vessels is likely to be more productive than energy devoted to patching leaks. -- Warren Buffett",
    "🌈 If I had six hours to chop down a tree, I would spend the first four hours sharpening the axe. -- Abraham Lincoln",
    "🌈 Productivity is never an accident. It's always the result of a commitment to excellence, intelligent planning, and focused effort. -- Paul J. Meyer",
    "🎯 The best time to start was last year. Failing that, today will do. -- Chris Guillebeau",
    "🎯 The best thing about the future is that it comes one day at a time. -- Abraham Lincoln",
    "🎯 He who every morning plans the transactions of that day and follows that plan carries a thread that will guide him through the labyrinth of the most busy life. -- Victor Hugo",
    "🎯 The secret of getting ahead is getting started. The secret of getting started is breaking your complex overwhelming tasks into small manageable tasks, and starting on the first one. -- Mark Twain",
    "🎯 Sometimes our stop-doing list needs to be bigger than our to-do list. -- Patti Digh",
    "🎯 Before you eat the elephant, make sure you know what parts you want to eat. -- Todd Stocker",
    "🎯 Rename your to-do list to your opportunities list. Each day is a treasure chest filled with limitless opportunities; take joy in checking many off your list. -- Steve Maraboli",
    "🎯 Subtracting from your list of priorities is as important as adding to it. -- Frank Sonnenberg",
    "🎯 No matter how expert you may be, well-designed checklists can improve outcomes. -- Steven Levitt",
    "🎯 I long to accomplish a great and noble task, but it is my chief duty to accomplish small tasks as if they were great and noble. -- Helen Keller",
    "🎯 No matter how great the talent or effort, some things just take time. -- Warren Buffett",    
    "⭐ You're setting yourself up for success by being focused and determined!",
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
                        st.write(f"{i}. **{t['name']}** \n*(Requires: {t['prereq']})*")
                    else:
                        st.write(f"{i}. **{t['name']}**")
            else:
                st.write("Your list is currently empty.")

        if st.session_state.confirm_delete_list:
            st.sidebar.error("Are you sure you want to delete the WHOLE list? This can't be undone.")

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

            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                submit_task = st.form_submit_button("Add Task")

            with btn_col2:
                delete_task_click = st.form_submit_button("Delete Task")
                if delete_task_click:
                    st.session_state.show_delete_dropdown = True
                    st.session_state.force_expand_list = True

            with btn_col3:
                black_btn_label = "Yes, Everything" if st.session_state.confirm_delete_list else "Delete List"
                delete_list_click = st.form_submit_button(black_btn_label)
                if delete_list_click:
                    if not st.session_state.confirm_delete_list:
                        st.session_state.confirm_delete_list = True
                        st.rerun()
                    else:
                        st.session_state.tasks = []
                        st.session_state.current_index = 0
                        st.session_state.confirm_delete_list = False
                        st.session_state.show_delete_dropdown = False
                        save_tasks_to_file()
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
                        save_tasks_to_file()
                        st.session_state.show_delete_dropdown = False
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
                st.rerun()
            st.html("<script>document.getElementById('root').querySelector('button:has(div:contains(\"Go Back\"))').classList.add('giant-goback-btn');</script>")

        if st.session_state.show_delete_dropdown and len(st.session_state.tasks) > 0:
            task_numbers = [str(i) for i in range(1, len(st.session_state.tasks) + 1)]
            selected_num = st.selectbox("Select task number to remove permanently:", ["None"] + task_numbers)
            
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
        
        st.html(f"<h1 style='text-align: center; margin-bottom: 20px;'>{current_task['name']}</h1>")
        
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
            st.html(f"<div style='text-align: center; font-size: 28px; font-weight: 400; color: inherit;'>{st.session_state.affirmation}</div>")

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
