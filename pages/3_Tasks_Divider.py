import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Establishing a Google Sheets connection for Users
users_conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch existing users data
existing_users = users_conn.read(worksheet="Users", usecols=list(range(2)), ttl=5)
existing_users = existing_users.dropna(how="all")

st.title("📝 Tasks Divider")

# Function to divide tasks among users equally
def divide_tasks_equally(df, users):
    # Spread rows as evenly as possible: sizes differ by at most one task.
    base, extra = divmod(len(df), len(users))

    divided_tasks = {}
    start_idx = 0
    for i, user in enumerate(users):
        end_idx = start_idx + base + (1 if i < extra else 0)
        divided_tasks[user] = df.iloc[start_idx:end_idx].copy()
        divided_tasks[user].insert(0, "Username", user)  # Add user name in first column
        start_idx = end_idx

    return divided_tasks

# Function to divide tasks among users based on specified tasks per user
def divide_tasks_specified(df, users, tasks_per_user_dict):
    divided_tasks = {}

    for user in users:
        # Divide tasks for each user
        num_tasks = min(tasks_per_user_dict.get(user, 0), len(df))
        divided_tasks[user] = df.sample(n=num_tasks, replace=False).copy()
        divided_tasks[user].insert(0, "Username", user)  # Add user name in first column
        df = df.drop(divided_tasks[user].index)
    
    return divided_tasks



# File uploader for Excel file
st.write("Upload the Excel file containing tasks:")
excel_file = st.file_uploader("Upload Excel", type=["xlsx", "xls"])

# Multiselect for choosing users
if not existing_users.empty:
    users = st.multiselect("Select Users:", existing_users["Username"].tolist(), default=existing_users["Username"].tolist())

    if excel_file is not None and users:
        # Checkbox for choosing task division method
        division_method = st.radio("Task Division Method:", ["Equal Division", "Specify Tasks per User"])

        if division_method == "Equal Division":
            # Divide tasks equally among users
            df = pd.read_excel(excel_file)
            divided_tasks = divide_tasks_equally(df, users)
        elif division_method == "Specify Tasks per User":
            # Dictionary to store tasks per user
            tasks_per_user_dict = {}
            for user in users:
                tasks_per_user_dict[user] = st.slider(f"Tasks for {user}:", min_value=1, max_value=100, value=5)

            # Divide tasks based on specified tasks per user
            df = pd.read_excel(excel_file)
            divided_tasks = divide_tasks_specified(df, users, tasks_per_user_dict)

        # Button to initiate the task division process
        if st.button("Divide Tasks"):
            # Export tasks to Google Sheets
            for user, tasks in divided_tasks.items():
                users_conn.update(worksheet=user, data=tasks)
            st.success("Tasks successfully Divided!")
else:
    st.warning("No users found in the 'Users' sheet. Please add users first.")
    