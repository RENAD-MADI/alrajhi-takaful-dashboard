import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Display Title and Description
st.title("🏠Home Page")
st.markdown("Welcome to the Admin Dashboard 🛡️")

# Introduction
st.write(
"""
This dashboard allows you to view and analyze bills data.
You can navigate through different sections using the sidebar on the left.

- **1. 📃Bills Viewer**: View the full data of the bills and  Analyze billing data and generate reports.
- **2. 📝Tasks Divider**: Divide tasks among users Equal Division or Specify Tasks per User.
- **3. 🧑‍💻User Management**: Add or delete users.

Select a section from the sidebar to get started!
"""
        )