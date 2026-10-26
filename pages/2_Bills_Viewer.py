import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# Establishing a Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)


def load_done_data():
    """Read the "Done" worksheet with proper date and number types."""
    data = conn.read(worksheet="Done", ttl=5).dropna(how="all")
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    for column in ["Money", "CollectedMoney", "Rest"]:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)
    return data


def show_result_charts(data, title_suffix=""):
    """Pie of result share, bar of result counts and bar of money per result."""
    st.subheader("Percentage of Each Result Type")
    result_percentage = data["Result"].value_counts(normalize=True) * 100
    fig = px.pie(values=result_percentage, names=result_percentage.index,
                 title=f"Percentage of Each Result Type{title_suffix}")
    st.plotly_chart(fig)

    st.subheader("Count of Result Types")
    st.bar_chart(data["Result"].value_counts())

    st.subheader("Total money by Result Type")
    st.bar_chart(data.groupby("Result")["Money"].sum())


all_done = load_done_data()

# Fetching list of users from "Users" worksheet
users_data = conn.read(worksheet="Users", usecols=["Username"], ttl=5)
users_list = users_data["Username"].dropna().tolist()

option = st.sidebar.selectbox("Choose an Option", ["Home", "Each User Individually", "Comparison", "Total for All"])

# Date range defaults to the oldest and latest dates in the "Done" sheet
st.sidebar.subheader("Analysis Period")
start_date = pd.to_datetime(st.sidebar.date_input("Start Date", value=all_done["Date"].min()))
end_date = pd.to_datetime(st.sidebar.date_input("End Date", value=all_done["Date"].max()))
done_data = all_done[(all_done["Date"] >= start_date) & (all_done["Date"] <= end_date)]

if option == "Home":
    st.title("📃 Bills Analysis")
    st.markdown("Welcome to the Billing Data Analysis dashboard! Please choose one of the following options to proceed:")
    st.write(
        """
    **1. 🧑‍💻Each User Individually** : Analyze billing data for each user separately.

    **2. 👥Comparison** : Compare billing data between different users.

    **3. 📈Total for All** : Analyze total billing data for all selected users.
    """
    )
    st.write("Choose the option from the sidebar to get started!")

elif option == "Each User Individually":
    st.title("🧑‍💻Each User Individually")
    selected_users = st.multiselect("Select Users", users_list, key="user_select")

    if not selected_users:
        st.warning("Please select at least one user.")
    for user in selected_users:
        st.subheader(f"Analysis for User: {user}")
        user_data = done_data[done_data["Username"] == user]
        if user_data.empty:
            st.warning(f"No data found for user {user}.")
        else:
            show_result_charts(user_data)

elif option == "Comparison":
    st.title("👥Comparison")
    selected_users = st.multiselect("Select Users for Comparison", users_list, key="comparison_select")

    if not selected_users:
        st.warning("Please select at least one user.")
    else:
        data = done_data[done_data["Username"].isin(selected_users)]
        for user in selected_users:
            if data[data["Username"] == user].empty:
                st.warning(f"No data found for user {user}.")

        st.subheader("Comparison of Numbers and Statistics")

        st.subheader("Percentage of Each Result Type")
        for user, user_data in data.groupby("Username"):
            share = user_data["Result"].value_counts(normalize=True) * 100
            st.plotly_chart(px.pie(values=share, names=share.index,
                                   title=f"Percentage of Each Result Type for {user}"))

        # One column per user; result types a user does not have count as zero.
        st.subheader("Count of Result Types")
        st.bar_chart(pd.crosstab(data["Result"], data["Username"]))

        st.subheader("Total money by Result Type")
        st.bar_chart(data.pivot_table(index="Result", columns="Username", values="Money",
                                      aggfunc="sum", fill_value=0))

elif option == "Total for All":
    st.title("📈Total for All")
    selected_users = st.multiselect("Select Users for Total Analysis", users_list, key="total_select")

    if not selected_users:
        st.warning("Please select at least one user.")
    else:
        # Analyse the selected users' rows together; the old version added up
        # per-user percentages, which could exceed 100% and drop missing result types.
        data = done_data[done_data["Username"].isin(selected_users)]
        if data.empty:
            st.warning("No data found for the selected users in this period.")
        else:
            st.subheader("Total Numbers and Statistics for Selected Users")
            show_result_charts(data)
