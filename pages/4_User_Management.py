import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time


option = st.sidebar.selectbox("Choose an Option", ["Add User", "Delete User"])


# Establishing a Google Sheets connection for Users
users_conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch existing users data
existing_users = users_conn.read(worksheet="Users", usecols=list(range(2)), ttl=5)
existing_users = existing_users.dropna(how="all")

# Display Title and Description
st.title("🧑‍💻User Management")

# Adding new Users

if option == "Add User":
    st.title("Add User")
    st.markdown("Add new users and passwords below.")

    with st.form(key="user_form", clear_on_submit=True):
        new_username = st.text_input(label="Username*")
        new_password = st.text_input(label="Password*", type="password", key="password")  # Masking the password
        confirm_password = st.text_input(label="Confirm Password*", type="password", key="confirm_password")

        st.markdown("**required*")
        submit_user_button = st.form_submit_button(label="Add User")

        if submit_user_button:
            if not new_username or not new_password or not confirm_password:
                st.warning("Ensure all mandatory fields are filled.")
            elif new_password != confirm_password:
                st.warning("Passwords do not match. Please re-enter.")
            else:
                user_data = pd.DataFrame([{"Username": new_username, "Password": new_password}])
                updated_users_df = pd.concat([existing_users, user_data], ignore_index=True)
                users_conn.update(worksheet="Users", data=updated_users_df)
                success_user_message = st.success("User successfully added!")

                # Clear the success message after 5 seconds
                time.sleep(5)
                success_user_message.empty()

# Delete users

elif option == "Delete User":
    st.title("Delete User")
    st.markdown("Delete one user or more.")
    selected_users_to_delete = st.multiselect("Select Users to Delete:", existing_users["Username"].tolist())

    if selected_users_to_delete:
        confirm_delete = st.checkbox("Confirm deletion")

        if st.button("Delete") and confirm_delete:
            # Remove selected users from existing users
            existing_users = existing_users[~existing_users["Username"].isin(selected_users_to_delete)]
            
            # Update the Google Sheets with the updated user list
            users_conn.update(worksheet="Users", data=existing_users)

            st.success("Users deleted successfully!")
