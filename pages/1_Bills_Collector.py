import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import datetime

# Establishing a Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Function to get default values for text inputs
def get_default_value(task, column_name):
    """
    Get the default value for a given column in a task.
    If the task is None, return an empty string.
    If the value is numeric and not NaN, convert it to an integer.
    """
    value = task[column_name] if task is not None else ""
    if pd.isna(value):
        return ""  # empty cells used to show up as "nan" in the form
    if isinstance(value, (int, float)):
        return int(value)
    return value

# Function to convert date to string format
def format_date(date):
    """Convert a date to string format (YYYY-MM-DD)."""
    return date.strftime("%Y-%m-%d") if date is not None else None

# Function to clear success message
def clear_message(message, duration=5):
    """Clear a message after a specified duration."""
    time.sleep(duration)
    message.empty()

# Fetching list of users from "Users" worksheet
users_data = conn.read(worksheet="Users", usecols=["Username"], ttl=5)
users_list = users_data["Username"].dropna().tolist()  # Filter out NaN values

# Select user from dropdown
selected_user = st.selectbox("Select User", users_list, key='user_select')

# Automatically select the first task in the sheet
existing_data = conn.read(worksheet=selected_user, ttl=5)
existing_data = existing_data.dropna(how="all")
first_task = existing_data.iloc[0] if not existing_data.empty else None

# Display user data
st.write(existing_data)

with st.form(key="bill_form", clear_on_submit=True):  # Setting clear_on_submit to True
    # Input fields for policy number, mobile, money, number of calls, result, date, and additional notes
    policy_number = st.text_input(label="Policy Number*", value=get_default_value(first_task, "PolicyNumber"))
    mobile = st.text_input(label="Mobile*", value=str(get_default_value(first_task, "Mobile")))
    money = st.text_input(label="Money*", value=str(get_default_value(first_task, "Money")))
    collected_money = st.text_input(label="Collected Money", value=str(get_default_value(first_task, "CollectedMoney")))
    num_calls_default = 1 if first_task is None or pd.isna(first_task.get("NumCalls")) else int(first_task.get("NumCalls"))
    num_calls = st.slider("Number of Calls*", 1, 10, num_calls_default)
    result_options = ["Paid", "Not Paid", "Pay Later", "No Answer", "Cancellation", "Partial withdrawal", "Modificaion"]
    result_default = None if first_task is None else first_task.get("Result")
    # Unknown or empty values in the sheet fall back to the first option instead of crashing.
    result_default_index = result_options.index(result_default) if result_default in result_options else 0
    result = st.selectbox("Result", result_options, index=result_default_index)
    date_default = datetime.date.today() if first_task is None or pd.isna(first_task.get("Date")) else pd.to_datetime(first_task["Date"]).date()
    date = st.date_input(label="Date", value=date_default)
    additional_notes_default = get_default_value(first_task, "AdditionalNotes")
    additional_notes = st.text_area(label="Additional Notes", value=additional_notes_default)

    st.markdown("**required*")
    submit_button = st.form_submit_button(label="Submit Bill Details")

    if submit_button:
        # Check if mandatory fields are filled
        amounts = pd.to_numeric(pd.Series([money, collected_money or 0]), errors="coerce")
        if not policy_number or not mobile or not money:
            st.warning("Ensure all mandatory fields are filled.")
        elif amounts.isna().any():
            st.warning("Money and Collected Money must be numbers.")
        else:
            # Remaining amount still owed on this bill
            rest = float(amounts[0] - amounts[1])

            # Create a DataFrame with bill details
            bill_data = pd.DataFrame([
                {
                    "Username": selected_user,
                    "PolicyNumber": policy_number,
                    "Mobile": mobile,
                    "Money": money,
                    "CollectedMoney": collected_money,
                    "Rest": rest,
                    "NumCalls": num_calls,
                    "Result": result,
                    "Date": format_date(date),
                    "AdditionalNotes": additional_notes,
                }
            ])

            # Access the existing "Done" worksheet
            done_data = conn.read(worksheet="Done", ttl=5)
            done_data = done_data.dropna(how="all")
            
            # Append new data to existing data
            updated_df = pd.concat([done_data, bill_data], axis=0, ignore_index=True, join="inner")
            
            # Delete the row from the original worksheet if it exists
            if existing_data is not None and not existing_data.empty:
                original_row_index = existing_data[existing_data["PolicyNumber"] == policy_number].index
                if len(original_row_index) > 0:
                    existing_data.drop(index=original_row_index[0], inplace=True)
                    conn.update(worksheet=selected_user, data=existing_data)
            
            # Update the "Done" worksheet
            conn.update(worksheet="Done", data=updated_df)
            success_message = st.success("Bill details successfully submitted and row deleted!")

            # Clear the success message after 5 seconds
            clear_message(success_message)
            
            # Trigger a rerun to update the displayed data
            st.rerun()