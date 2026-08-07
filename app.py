import json
import os
import random
import streamlit as st
from supabase import Client, create_client

# 🚀 Unlocks full monitor width
st.set_page_config(
    layout="wide", page_title="Executive Function Assistant", page_icon="🧠"
)

# ==============================================================================
# 🌐 SUPABASE CLOUD DATABASE CONFIGURATION
# ==============================================================================
try:
  SUPABASE_URL = st.secrets["SUPABASE_URL"]
  SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
  SUPABASE_URL = ""
  SUPABASE_KEY = ""

LIMIT = 1000


@st.cache_resource
def init_supabase() -> Client:
  """Initializes and caches the Supabase database connection."""
  return create_client(SUPABASE_URL, SUPABASE_KEY)


try:
  supabase = init_supabase()
except Exception as e:
  st.error(f"⚠️ Supabase Error Detail: {e}")


def get_available_lists(user_key: str):
  """Fetch all list names registered under the given user_key from Supabase."""
  if not supabase or not user_key.strip():
    return []
  try:
    response = (
        supabase.table("tasks_db")
        .select("list_name")
        .eq("user_key", user_key.strip())
        .execute()
    )
    if response.data:
      lists = sorted(
          list(
              set(row["list_name"] for row in response.data if row.get("list_name"))
          )
      )
      return lists
  except Exception as e:
    st.sidebar.error(f"Error fetching cloud lists: {e}")
  return []


def fetch_list_tasks_only(user_key: str, target_list: str):
  """Fetch tasks from a cloud list without switching active session state directly."""
  if not supabase or not user_key.strip() or not target_list:
    return []
  try:
    response = (
        supabase.table("tasks_db")
        .select("tasks_data")
        .eq("user_key", user_key.strip())
        .eq("list_name", target_list)
        .execute()
    )
    if response.data:
      return response.data[0].get("tasks_data", [])
  except Exception as e:
    st.sidebar.error(f"Error fetching tasks for '{target_list}': {e}")
  return []


def rename_cloud_list(user_key: str, old_name: str, new_name: str):
  """Renames an existing list row directly in Supabase."""
  if not supabase or not user_key.strip() or not old_name or not new_name:
    return False
  try:
    supabase.table("tasks_db").update({"list_name": new_name}).eq(
        "user_key", user_key.strip()
    ).eq("list_name", old_name).execute()
    return True
  except Exception as e:
    st.sidebar.error(f"Error renaming list in Supabase: {e}")
    return False


def delete_cloud_list_row(user_key: str, target_list: str):
  """Completely purges a list row from Supabase so it no longer shows in the cloud dropdown."""
  if not supabase or not user_key.strip() or not target_list:
    return False
  try:
    supabase.table("tasks_db").delete().eq("user_key", user_key.strip()).eq(
        "list_name", target_list
    ).execute()
    return True
  except Exception as e:
    st.sidebar.error(f"Error deleting cloud list: {e}")
    return False


def load_from_cloud(user_key: str, pin: str, target_list: str = None):
  """Fetches tasks if user_key and pin match."""
  clean_key = user_key.strip()
  clean_pin = pin.strip()

  if not clean_key or not clean_pin:
    return False

  try:
    query = supabase.table("tasks_db").select("*").eq("user_key", clean_key)
    if target_list:
      query = query.eq("list_name", target_list)

    response = query.execute()
    if response.data:
      row = response.data[0]
      existing_pin = str(row.get("pin", "")).strip()

      if existing_pin == clean_pin:
        st.session_state.tasks = row.get("tasks_data", [])
        st.session_state.list_name = row.get("list_name", "Main List")
        st.session_state.auth_error = None
        st.session_state.db_status = (
            f"🟢 Connected to: '{st.session_state.list_name}'"
        )
        return True
      else:
        st.session_state.auth_error = "❌ Incorrect PIN for this passcode!"
        st.session_state.db_status = None
        st.session_state.tasks = []
        return False
    else:
      if target_list:
        st.session_state.list_name = target_list
      st.session_state.tasks = []
      st.session_state.auth_error = None
      st.session_state.db_status = "🟢 Ready! (Will save to cloud on action)"
      return True
  except Exception as e:
    st.session_state.auth_error = f"Error loading cloud data: {e}"
    return False


def save_to_cloud():
  """Saves current state to Supabase using persistent session state."""
  user_key = st.session_state.get("user_passcode", "").strip()
  pin = st.session_state.get("user_pin", "").strip()

  if not user_key or not pin:
    st.session_state.db_status = "⚠️ Save Skipped: Passcode or PIN missing!"
    return False

  current_name = st.session_state.get("list_name") or "Main List"

  try:
    payload = {
        "user_key": user_key,
        "pin": pin,
        "list_name": current_name,
        "tasks_data": st.session_state.tasks,
    }
    supabase.table("tasks_db").upsert(
        payload, on_conflict="user_key, list_name"
    ).execute()
    st.session_state.db_status = f"✅ Saved cloud list: '{current_name}'!"
    return True
  except Exception as e:
    st.session_state.db_status = f"❌ Supabase Error: {e}"
    st.sidebar.error(f"Save failed: {e}")
    return False


# ==============================================================================
# 🗂️ GLOBAL STATE INITIALIZATIONS
# ==============================================================================
if "tasks" not in st.session_state:
  st.session_state.tasks = []

if "list_name" not in st.session_state:
  st.session_state.list_name = None

if "user_passcode" not in st.session_state:
  st.session_state.user_passcode = ""

if "user_pin" not in st.session_state:
  st.session_state.user_pin = ""

if "auth_error" not in st.session_state:
  st.session_state.auth_error = None

if "db_status" not in st.session_state:
  st.session_state.db_status = None

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

if "show_delete_dropdown" not in st.session_state:
  st.session_state.show_delete_dropdown = False

if "show_move_dropdowns" not in st.session_state:
  st.session_state.show_move_dropdowns = False

if "show_edit_dropdown" not in st.session_state:
  st.session_state.show_edit_dropdown = False

if "show_new_list_input" not in st.session_state:
  st.session_state.show_new_list_input = False

if "show_template_actions" not in st.session_state:
  st.session_state.show_template_actions = False

if "show_manage_list" not in st.session_state:
  st.session_state.show_manage_list = False

if "editing_index" not in st.session_state:
  st.session_state.editing_index = None

if "edit_task_name" not in st.session_state:
  st.session_state.edit_task_name = ""

if "edit_prereq_name" not in st.session_state:
  st.session_state.edit_prereq_name = ""

if "affirmation" not in st.session_state:
  st.session_state.affirmation = None

if "randomize_mode" not in st.session_state:
  st.session_state.randomize_mode = False

if "ref_sublist_name" not in st.session_state:
  st.session_state.ref_sublist_name = None

AFFIRMATIONS = [
    "✨ Fantastic job getting that done!",
    "🎉 Way to cross that off your list!",
    "🚀 Outstanding momentum! Keep it going!",
    "⭐ Brilliant effort on this task!",
    "🎯 Crushing your goals one step at a time!",
    "🏆 Victory! Another item successfully completed!",
    "🌈 Spectacular execution!",
    "⚡ Pure efficiency! You're doing amazing!",
]


def reset_transient_panels():
  """Helper function to close all temporary action dropdowns/prompts."""
  st.session_state.show_edit_dropdown = False
  st.session_state.show_move_dropdowns = False
  st.session_state.show_delete_dropdown = False
  st.session_state.show_new_list_input = False
  st.session_state.show_template_actions = False
  st.session_state.show_manage_list = False


# ==============================================================================
# 🎨 CENTRAL STYLE CONFIGURATION
# ==============================================================================
TEXT_COLOR = "black"
FONT_FAMILY = "Georgia"

STYLE_WRAPPER = (
    f"<div style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>"
)

COLOR_ADD_TASK = "green"
COLOR_EDIT_TASK = "darkorange"
COLOR_MOVE_TASK = "blue"
COLOR_DELETE_TASK = "red"
COLOR_START_WORK = "purple"

st.html(f"""
    <style>
    /* Force buttons to fill container smoothly and remove native Streamlit padding */
    div[class*="st-key-btn_"] button {{
        width: 100% !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
    }}
    
    /* Strict no-wrap and keep-all for button text */
    div[class*="st-key-btn_"] button p {{
        white-space: nowrap !important;
        word-break: keep-all !important;
        overflow-wrap: normal !important;
        hyphens: none !important;
        text-align: center !important;
        font-size: 14px !important;
    }}

    /* Clean tablet layout adjustments */
    @media (min-width: 576px) and (max-width: 992px) {{
        div[data-testid="column"]:has(div[class*="st-key-btn_"]) {{
            min-width: 0px !important;
            flex: 1 1 auto !important;
            margin-bottom: 4px !important;
        }}
        div[class*="st-key-btn_"] button p {{
            font-size: 11px !important;
        }}
    }}

    div[class*="st-key-btn_add"] button p {{ color: {COLOR_ADD_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_edit"] button p {{ color: {COLOR_EDIT_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_move"] button p {{ color: {COLOR_MOVE_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_delete_task"] button p {{ color: {COLOR_DELETE_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_start_work"] button p {{ color: {COLOR_START_WORK} !important; font-family: {FONT_FAMILY} !important; font-weight: bold !important; }}
    div[class*="st-key-btn_confirm_edit"] button p {{ color: {COLOR_EDIT_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_confirm_move"] button p {{ color: {COLOR_MOVE_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    div[class*="st-key-btn_confirm_delete"] button p {{ color: {COLOR_DELETE_TASK} !important; font-family: {FONT_FAMILY} !important; }}
    </style>
""")

# ==============================================================================
# 💾 SIDEBAR: CLOUD PASSCODE LOGIN & UTILITIES
# ==============================================================================
with st.sidebar:
  st.html(
      f"<h3 style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>☁️ Cloud"
      " Sync Login</h3>"
  )

  passcode_input = st.text_input(
      label="Enter Passcode:",
      key="user_passcode",
      placeholder="e.g. executive-tasks",
  )

  pin_input = st.text_input(
      label="Enter 4-Digit PIN:",
      key="user_pin",
      type="password",
      max_chars=4,
      placeholder="e.g. 1234",
  )

  if st.button("🔐 Sync / Authenticate", use_container_width=True):
    if passcode_input.strip() and pin_input.strip():
      load_from_cloud(passcode_input, pin_input)
      st.rerun()

  if st.session_state.auth_error:
    st.error(st.session_state.auth_error)
  elif st.session_state.user_passcode and st.session_state.user_pin:
    st.success(f"🟢 Authenticated: **{st.session_state.user_passcode}**")
    if st.session_state.db_status:
      st.info(st.session_state.db_status)

  # --- MULTI-LIST & TEMPLATE ENGINE ---
  if (
      st.session_state.user_passcode.strip()
      and st.session_state.user_pin.strip()
      and not st.session_state.auth_error
  ):
    st.markdown("---")
    st.html(
        f"<h3 style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>📋 Cloud"
        " List Selector</h3>"
    )

    avail_lists = get_available_lists(st.session_state.user_passcode)
    if not avail_lists:
      avail_lists = [
          st.session_state.list_name
          if st.session_state.list_name
          else "Main List"
      ]

    if (
        st.session_state.list_name
        and st.session_state.list_name not in avail_lists
    ):
      avail_lists.append(st.session_state.list_name)
      avail_lists = sorted(list(set(avail_lists)))

    current_active = (
        st.session_state.list_name
        if st.session_state.list_name in avail_lists
        else avail_lists[0]
    )

    selected_cloud_list = st.selectbox(
        "Select Active Cloud List:",
        options=avail_lists,
        index=avail_lists.index(current_active),
        key="cloud_list_selector",
    )

    if selected_cloud_list != st.session_state.list_name:
      st.session_state.list_name = selected_cloud_list
      load_from_cloud(
          st.session_state.user_passcode,
          st.session_state.user_pin,
          selected_cloud_list,
      )
      st.session_state.current_index = 0
      st.rerun()

    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
      if st.button("➕ New", use_container_width=True, key="btn_sb_new"):
        st.session_state.show_new_list_input = (
            not st.session_state.show_new_list_input
        )
        st.session_state.show_template_actions = False
        st.session_state.show_manage_list = False
    with col_l2:
      if st.button("🧩 Copy", use_container_width=True, key="btn_sb_copy"):
        st.session_state.show_template_actions = (
            not st.session_state.show_template_actions
        )
        st.session_state.show_new_list_input = False
        st.session_state.show_manage_list = False
    with col_l3:
      if st.button("⚙️ Edit", use_container_width=True, key="btn_sb_edit"):
        st.session_state.show_manage_list = (
            not st.session_state.show_manage_list
        )
        st.session_state.show_new_list_input = False
        st.session_state.show_template_actions = False

    if st.session_state.show_new_list_input:
      new_list_name = st.text_input(
          "New List Name:", key="new_list_name_sidebar"
      )
      if st.button("Create List", use_container_width=True):
        if new_list_name.strip():
          st.session_state.list_name = new_list_name.strip()
          st.session_state.tasks = []
          st.session_state.show_new_list_input = False
          save_to_cloud()
          if "cloud_list_selector" in st.session_state:
            del st.session_state["cloud_list_selector"]
          st.rerun()

    # --- TEMPLATE PULL PANEL ---
    if st.session_state.show_template_actions:
      st.markdown("---")
      st.html(
          f"<div style='font-size: 13px; color: {TEXT_COLOR}; font-family:"
          f" {FONT_FAMILY};'><b>Copy tasks from another cloud list into"
          f" '{st.session_state.list_name}':</b></div>"
      )

      source_template = st.selectbox(
          "Choose Template List:",
          options=[
              lst for lst in avail_lists if lst != st.session_state.list_name
          ]
          if len(avail_lists) > 1
          else avail_lists,
          key="template_source_selector",
      )

      col_t_combine, col_t_replace = st.columns(2)
      with col_t_combine:
        if st.button("📥 Combine", use_container_width=True):
          fetched_tasks = fetch_list_tasks_only(
              st.session_state.user_passcode, source_template
          )
          if fetched_tasks:
            st.session_state.tasks.extend(fetched_tasks)
            save_to_cloud()
            st.success(f"Combined '{source_template}' into active list!")
            st.session_state.show_template_actions = False
            st.rerun()
          else:
            st.warning("Selected template list is empty.")

      with col_t_replace:
        if st.button("🔄 Overwrite", use_container_width=True):
          fetched_tasks = fetch_list_tasks_only(
              st.session_state.user_passcode, source_template
          )
          if fetched_tasks:
            st.session_state.tasks = fetched_tasks
            save_to_cloud()
            st.success(f"Overwrote active list with '{source_template}'!")
            st.session_state.show_template_actions = False
            st.rerun()
          else:
            st.warning("Selected template list is empty.")

    # --- LIST MANAGEMENT PANEL (Rename & Purge) ---
    if st.session_state.show_manage_list:
      st.markdown("---")
      st.html(
          f"<div style='font-size: 13px; color: {TEXT_COLOR}; font-family:"
          f" {FONT_FAMILY};'><b>Manage Active List:"
          f" '{st.session_state.list_name}'</b></div>"
      )

      renamed_val = st.text_input(
          "Rename List To:",
          value=st.session_state.list_name,
          key="rename_input_val",
      )
      if st.button("✏️ Confirm Rename", use_container_width=True):
        if renamed_val.strip() and renamed_val.strip() != st.session_state.list_name:
          old_name = st.session_state.list_name
          new_name = renamed_val.strip()
          if rename_cloud_list(
              st.session_state.user_passcode, old_name, new_name
          ):
            st.session_state.list_name = new_name
            st.session_state.show_manage_list = False
            if "cloud_list_selector" in st.session_state:
              del st.session_state["cloud_list_selector"]
            st.rerun()

      st.markdown("---")
      if st.button("🗑️ Delete List from Cloud", use_container_width=True):
        target_to_del = st.session_state.list_name
        if delete_cloud_list_row(
            st.session_state.user_passcode, target_to_del
        ):
          st.session_state.tasks = []
          st.session_state.list_name = "Main List"
          st.session_state.show_manage_list = False
          if "cloud_list_selector" in st.session_state:
            del st.session_state["cloud_list_selector"]
          st.success(f"Deleted '{target_to_del}' from database.")
          st.rerun()

  st.markdown("---")
  st.html(
      f"<h3 style='color: {TEXT_COLOR}; font-family: {FONT_FAMILY};'>💾"
      " Workspace Backup</h3>"
  )

  if len(st.session_state.tasks) > 0:
    current_list_name = st.session_state.get("list_name", None)
    default_name = (
        current_list_name if current_list_name else "executive_tasks_backup"
    )

    st.html(
        f"<div style='color: gray; font-size: 14px; font-family:"
        f" {FONT_FAMILY}; margin-bottom: 2px;'>Export File Name:</div>"
    )
    custom_name = st.text_input(
        label="Export File Name",
        value="",
        placeholder=default_name,
        key="export_file_name_input",
        label_visibility="collapsed",
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
        key="btn_export_sidebar",
    )
  else:
    st.button(
        "📤 Export List (Empty)",
        disabled=True,
        use_container_width=True,
        key="btn_export_disabled",
    )

  uploaded_file = st.file_uploader(
      label="📥 Select Saved List (.json)",
      type=["json"],
      key=f"file_uploader_{st.session_state.uploader_id}",
      label_visibility="visible",
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
            base_name, _ = os.path.splitext(uploaded_file.name)
            st.session_state.list_name = base_name
            st.session_state.tasks = imported_data
            st.session_state.current_index = 0
            st.session_state.mode = "adding"
            st.session_state.uploader_id += 1
            st.session_state.editing_index = None
            st.session_state.edit_task_name = ""
            st.session_state.edit_prereq_name = ""
            st.session_state.form_version += 1
            reset_transient_panels()

            if save_to_cloud():
              st.session_state.import_success = True
              if "cloud_list_selector" in st.session_state:
                del st.session_state["cloud_list_selector"]
              st.rerun()
          else:
            st.error(
                f"❌ Import failed: File exceeds limit of {LIMIT} tasks."
            )

        elif combine_clicked:
          if current_count == 0:
            st.sidebar.warning(
                "⚠️ Your task list is currently empty. Enter a task first to"
                " combine."
            )
          elif (current_count + num_imported) > LIMIT:
            st.sidebar.error(
                "❌ Unable to import: combined count exceeds limit of"
                f" {LIMIT}."
            )
          else:
            st.session_state.tasks.extend(imported_data)
            st.session_state.uploader_id += 1
            reset_transient_panels()
            if save_to_cloud():
              st.session_state.import_success = True
              st.rerun()
      else:
        st.error("❌ Invalid format: Unrecognized JSON structure.")
    except Exception as e:
      st.error(f"❌ Failed to read file: {e}")

  if st.session_state.import_success:
    st.success("✅ List restored successfully!")
    st.session_state.import_success = False

# ==============================================================================
# 🧩 MAIN VIEW LOGIC
# ==============================================================================

# --- MODE: ADDING / EDITING TASKS ---
if st.session_state.mode == "adding":
  st.html(
      f"<h1 style='color: {TEXT_COLOR}; font-family:"
      f" {FONT_FAMILY};'>Executive Function Assistant</h1>"
  )

  if not (
      st.session_state.user_passcode.strip()
      and st.session_state.user_pin.strip()
  ):
    st.info(
        "👈 Save your progress by creating a Passcode and PIN, or retrieve past"
        " work with existing ones! "
    )

  left_col, right_col = st.columns([1.5, 1.2], gap="large")

  with left_col:
    if st.session_state.list_name:
      header_html = (
          f"<h3 style='margin-bottom: 5px; color: {TEXT_COLOR}; font-family:"
          f" {FONT_FAMILY};'>📋 Current Task List: <span style='color: purple;"
          f" font-weight: normal;'>{st.session_state.list_name}</span></h3>"
      )
    else:
      header_html = (
          f"<h3 style='margin-bottom: 5px; color: {TEXT_COLOR}; font-family:"
          f" {FONT_FAMILY};'>📋 Current Task List: <span style='color: gray;"
          " font-weight: normal;'><i></i></span></h3>"
      )
    st.html(header_html)

    with st.container(height=450, border=True):
      if len(st.session_state.tasks) > 0:
        for i, t in enumerate(st.session_state.tasks, 1):
          is_editing_this = st.session_state.editing_index == (i - 1)
          prefix = "✏️ " if is_editing_this else ""
          if t["prereq"]:
            st.html(
                f"{STYLE_WRAPPER}{i}. {prefix}<b>{t['name']}</b>"
                f" <br><i>({t['prereq']})</i></div><hr style='margin: 8px 0;'>"
            )
          else:
            st.html(
                f"{STYLE_WRAPPER}{i}. {prefix}<b>{t['name']}</b></div><hr"
                " style='margin: 8px 0;'>"
            )
      else:
        st.html(f"{STYLE_WRAPPER}Your list is currently empty.</div>")

  with right_col:
    st.html(
        f"<h2 style='text-align: center; margin-bottom: 20px; color:"
        f" {TEXT_COLOR}; font-family: {FONT_FAMILY};'>Build Your List</h2>"
    )

    st.html(
        f"{STYLE_WRAPPER}Current task count: {len(st.session_state.tasks)} /"
        f" {LIMIT}</div><br>"
    )

    if st.session_state.editing_index is not None:
      active_task_num = st.session_state.editing_index + 1
      form_title = f"Editing Task #{active_task_num}:"
      add_button_label = "Save Changes"
    else:
      form_title = "Enter a task you would like to add:"
      add_button_label = "Add Task"

    ver_key = (
        f"v{st.session_state.form_version}_e{st.session_state.editing_index}"
    )

    with st.form(key=f"input_form_{ver_key}", clear_on_submit=True):
      task_text = st.text_input(
          form_title, value=st.session_state.edit_task_name
      )

      st.html(
          f"<div style='color: gray; font-family: {FONT_FAMILY};'>Enter a note"
          " you would like to add to your task. (Optional)</div>"
      )
      prereq_text = st.text_input(
          label="Prerequisite Input",
          value=st.session_state.edit_prereq_name,
          key=f"prereq_in_{ver_key}",
          label_visibility="collapsed",
      )

      row1_col1, row1_col2, row1_col3 = st.columns(3)
      with row1_col1:
        submit_task = st.form_submit_button(
            add_button_label, key="btn_add", use_container_width=True
        )

      with row1_col2:
        edit_task_click = st.form_submit_button(
            "Edit Task", key="btn_edit", use_container_width=True
        )

      with row1_col3:
        move_task_click = st.form_submit_button(
            "Move Task", key="btn_move", use_container_width=True
        )

      row2_col1, row2_col2 = st.columns(2)
      with row2_col1:
        delete_task_click = st.form_submit_button(
            "Delete Task", key="btn_delete_task", use_container_width=True
        )

      with row2_col2:
        if len(st.session_state.tasks) > 0:
          start_working_click = st.form_submit_button(
              "Start Working", key="btn_start_work", use_container_width=True
          )
        else:
          start_working_click = False

      if submit_task:
        reset_transient_panels()

        if task_text.strip() != "":
          new_task_obj = {
              "name": task_text.strip(),
              "prereq": (
                  prereq_text.strip() if prereq_text.strip() != "" else None
              ),
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
              st.sidebar.error(
                  f"Limit reached! You cannot add more than {LIMIT} tasks."
              )
        else:
          st.sidebar.warning("Task name cannot be blank!")

      elif edit_task_click:
        st.session_state.show_edit_dropdown = True
        st.session_state.show_move_dropdowns = False
        st.session_state.show_delete_dropdown = False
        st.rerun()

      elif move_task_click:
        st.session_state.show_move_dropdowns = True
        st.session_state.show_edit_dropdown = False
        st.session_state.show_delete_dropdown = False
        st.rerun()

      elif delete_task_click:
        st.session_state.show_delete_dropdown = True
        st.session_state.show_edit_dropdown = False
        st.session_state.show_move_dropdowns = False
        st.rerun()

      elif start_working_click:
        st.session_state.mode = "working"
        st.session_state.current_index = 0
        st.session_state.affirmation = None
        reset_transient_panels()
        st.rerun()

    if st.session_state.show_edit_dropdown and len(st.session_state.tasks) > 0:
      st.markdown("---")
      st.html(
          f"{STYLE_WRAPPER}<b>Select task number to load into editor:</b></div>"
      )

      edit_col1, edit_col2 = st.columns([3, 1])
      max_tasks = len(st.session_state.tasks)

      with edit_col1:
        selected_edit_num = st.number_input(
            label="Select Task to Edit",
            min_value=1,
            max_value=max_tasks,
            step=1,
            key="edit_task_num",
            label_visibility="collapsed",
        )

      with edit_col2:
        st.html("<div style='margin-top: 2px;'></div>")
        if st.button(
            "Load Task", key="btn_confirm_edit", use_container_width=True
        ):
          edit_idx = int(selected_edit_num) - 1
          target_task = st.session_state.tasks[edit_idx]

          st.session_state.editing_index = edit_idx
          st.session_state.edit_task_name = target_task["name"]
          st.session_state.edit_prereq_name = (
              target_task["prereq"] if target_task["prereq"] else ""
          )
          st.session_state.show_edit_dropdown = False
          st.session_state.form_version += 1
          st.rerun()

    if (
        st.session_state.show_move_dropdowns
        and len(st.session_state.tasks) > 1
    ):
      st.markdown("---")
      st.html(f"{STYLE_WRAPPER}<b>Rearrange Task Order:</b></div>")

      move_col1, move_col2, move_col3 = st.columns([1.5, 1.5, 1])
      max_tasks = len(st.session_state.tasks)

      with move_col1:
        st.html(f"{STYLE_WRAPPER}Move task number:</div>")
        from_num = st.number_input(
            label="From Position",
            min_value=1,
            max_value=max_tasks,
            step=1,
            key="move_from_num",
            label_visibility="collapsed",
        )

      with move_col2:
        st.html(f"{STYLE_WRAPPER}To new position:</div>")
        to_num = st.number_input(
            label="To Position",
            min_value=1,
            max_value=max_tasks,
            step=1,
            key="move_to_num",
            label_visibility="collapsed",
        )

      with move_col3:
        st.html("<div style='margin-top: 24px;'></div>")
        if st.button(
            "Confirm Move", key="btn_confirm_move", use_container_width=True
        ):
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

    elif (
        st.session_state.show_move_dropdowns
        and len(st.session_state.tasks) <= 1
    ):
      st.sidebar.warning(
          "You need at least 2 tasks in your list to rearrange them!"
      )
      st.session_state.show_move_dropdowns = False

    if (
        st.session_state.show_delete_dropdown
        and len(st.session_state.tasks) > 0
    ):
      st.markdown("---")
      st.html(
          f"{STYLE_WRAPPER}Select task number to remove permanently:</div>"
      )

      del_col1, del_col2 = st.columns([3, 1])
      max_tasks = len(st.session_state.tasks)

      with del_col1:
        selected_num = st.number_input(
            label="Select Task Number",
            min_value=1,
            max_value=max_tasks,
            step=1,
            key="delete_task_num",
            label_visibility="collapsed",
        )

      with del_col2:
        st.html("<div style='margin-top: 2px;'></div>")
        if st.button(
            "Confirm Delete",
            key="btn_confirm_delete",
            use_container_width=True,
        ):
          del_idx = int(selected_num) - 1
          del st.session_state.tasks[del_idx]

          if st.session_state.editing_index == del_idx:
            st.session_state.editing_index = None
            st.session_state.edit_task_name = ""
            st.session_state.edit_prereq_name = ""
            st.session_state.form_version += 1
          elif (
              st.session_state.editing_index is not None
              and st.session_state.editing_index > del_idx
          ):
            st.session_state.editing_index -= 1

          save_to_cloud()
          st.session_state.show_delete_dropdown = False
          st.rerun()

# --- MODE: WORKING ON TASKS ---
elif st.session_state.mode == "working":
  st.write("")
  st.write("")

  if len(st.session_state.tasks) > 0:
    if st.session_state.current_index >= len(st.session_state.tasks):
      st.session_state.current_index = 0

    current_task = st.session_state.tasks[st.session_state.current_index]

    st.html(
        f"<h1 style='text-align: center; margin-bottom: 20px; color:"
        f" {TEXT_COLOR}; font-family:"
        f" {FONT_FAMILY};'>{current_task['name']}</h1>"
    )

    if current_task["prereq"]:
      st.warning(f"⚠️ **Worth Noting:** \n\n  {current_task['prereq']}")

    st.write("")

    st.session_state.randomize_mode = st.toggle(
        "🔀 Shuffle / Randomize Next Task",
        value=st.session_state.randomize_mode,
        key="toggle_randomize_mode",
    )

    st.write("")
    col1, col2, col3 = st.columns(3)

    with col1:
      if st.button("👍 Yes, I completed it!", use_container_width=True):
        del st.session_state.tasks[st.session_state.current_index]
        save_to_cloud()
        st.session_state.affirmation = random.choice(AFFIRMATIONS)

        remaining_count = len(st.session_state.tasks)
        if remaining_count > 0:
          if st.session_state.randomize_mode:
            st.session_state.current_index = random.randrange(remaining_count)
          else:
            if st.session_state.current_index >= remaining_count:
              st.session_state.current_index = 0
        st.rerun()

    with col2:
      if st.button("👎 No, skip it for now", use_container_width=True):
        st.session_state.affirmation = None
        remaining_count = len(st.session_state.tasks)

        if remaining_count > 1 and st.session_state.randomize_mode:
          available_indices = [
              i
              for i in range(remaining_count)
              if i != st.session_state.current_index
          ]
          st.session_state.current_index = random.choice(available_indices)
        else:
          st.session_state.current_index += 1
          if st.session_state.current_index >= remaining_count:
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
      st.html(
          f"<div style='text-align: center; font-size: 28px; font-weight: 400;"
          " color: orange; font-family: Comic Sans"
          f" MS;'>{st.session_state.affirmation}</div>"
      )

    # --- READ-ONLY SUB-LIST REFERENCE PANEL ---
    st.markdown("---")
    with st.expander("📖 View Reference Sub-List (Read-Only)", expanded=False):
      all_cloud_lists = (
          get_available_lists(st.session_state.user_passcode)
          if st.session_state.user_passcode
          else []
      )

      # Exclude current active working list to avoid self-reference
      sublist_options = [
          lst for lst in all_cloud_lists if lst != st.session_state.list_name
      ]

      if sublist_options:
        selected_sublist = st.selectbox(
            "Choose sub-list to inspect top item:",
            options=sublist_options,
            key="sublist_ref_selector",
        )

        if selected_sublist:
          ref_tasks = fetch_list_tasks_only(
              st.session_state.user_passcode, selected_sublist
          )
          if ref_tasks:
            top_ref_task = ref_tasks[0]  # First sequential task
            st.html(
                f"<div style='border: 1px solid #ddd; padding: 12px;"
                " border-radius: 6px; background-color: #f9f9f9;'>"
                f"<div style='font-size: 14px; color: purple;"
                f" font-weight: bold;'>📌 First Task in '{selected_sublist}':</div>"
                f"<div style='font-size: 18px; font-weight: bold; margin-top:"
                f" 4px;'>{top_ref_task['name']}</div>"
                "</div>"
            )
            if top_ref_task.get("prereq"):
              st.info(f"⚠️ **Worth Noting:** {top_ref_task['prereq']}")
          else:
            st.info(f"The sub-list '{selected_sublist}' is currently empty.")
      else:
        st.info("No other cloud lists available for reference view.")

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
      st.rerun()
      