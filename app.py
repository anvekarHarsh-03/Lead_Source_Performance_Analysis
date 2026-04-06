import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Lead Analytics Dashboard", layout="wide")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    leads = pd.read_csv("dataset/leads_unclean_25000.csv")
    funnel = pd.read_csv("dataset/funnel_unclean_25000.csv")
    cost = pd.read_csv("dataset/marketing_cost_unclean.csv")

    # =========================
    # CLEANING (Same as your project)
    # =========================
    leads = leads.drop_duplicates()

    leads["City"] = leads["City"].str.strip().str.title()
    leads["Course_Interest"] = leads["Course_Interest"].str.strip().str.title()
    leads["Lead_Source"] = leads["Lead_Source"].str.strip().str.title()

    leads["Course_Interest"] = leads["Course_Interest"].replace({
        "Ai Ml": "AI/ML",
        "Ai/Ml": "AI/ML"
    })

    leads = leads.dropna(subset=["Lead_Source"])
    leads["City"] = leads["City"].fillna("Unknown")
    leads["Course_Interest"] = leads["Course_Interest"].fillna("Unknown")

    leads["Date"] = pd.to_datetime(leads["Date"], errors="coerce", dayfirst=True)
    leads = leads.dropna(subset=["Date"])

    # Funnel cleaning
    def clean_yes_no(col):
        return col.str.strip().str.lower().replace({
            "yes": "Yes", "y": "Yes",
            "no": "No", "n": "No"
        })

    funnel["Counselling"] = clean_yes_no(funnel["Counselling"])
    funnel["Application"] = clean_yes_no(funnel["Application"])
    funnel["Enrolled"] = clean_yes_no(funnel["Enrolled"])
    funnel = funnel.fillna("No")

    # Cost cleaning
    cost["Channel"] = cost["Channel"].str.strip().str.title()
    cost = cost.dropna()

    cost["Monthly_Cost"] = cost["Monthly_Cost"].astype(str)
    cost["Monthly_Cost"] = cost["Monthly_Cost"].str.replace(",", "")
    cost["Monthly_Cost"] = cost["Monthly_Cost"].str.replace("INR", "")
    cost["Monthly_Cost"] = cost["Monthly_Cost"].str.replace("Thirty Thousand", "30000")
    cost["Monthly_Cost"] = pd.to_numeric(cost["Monthly_Cost"], errors="coerce")

    # Merge
    df = leads.merge(funnel, on="Lead_ID")

    return df, cost

df, cost = load_data()

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.title("Filters")

selected_channel = st.sidebar.multiselect(
    "Select Channel",
    options=df["Lead_Source"].unique(),
    default=df["Lead_Source"].unique()
)

selected_city = st.sidebar.multiselect(
    "Select City",
    options=df["City"].unique(),
    default=df["City"].unique()
)

df_filtered = df[
    (df["Lead_Source"].isin(selected_channel)) &
    (df["City"].isin(selected_city))
]

# =========================
# KPIs
# =========================
total_leads = df_filtered.shape[0]
counselling = df_filtered[df_filtered["Counselling"] == "Yes"].shape[0]
applications = df_filtered[df_filtered["Application"] == "Yes"].shape[0]
enrolled = df_filtered[df_filtered["Enrolled"] == "Yes"].shape[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Leads", total_leads)
col2.metric("Counselling", counselling)
col3.metric("Applications", applications)
col4.metric("Enrollments", enrolled)

# =========================
# CHANNEL PERFORMANCE
# =========================
st.subheader("Channel Performance")

lead_counts = df_filtered.groupby("Lead_Source")["Lead_ID"].count().reset_index()
lead_counts.columns = ["Channel", "Leads"]

enrollments = df_filtered[df_filtered["Enrolled"] == "Yes"] \
    .groupby("Lead_Source")["Lead_ID"].count().reset_index()
enrollments.columns = ["Channel", "Enrollments"]

channel_stats = lead_counts.merge(enrollments, on="Channel")
channel_stats = channel_stats.merge(cost, on="Channel")

channel_stats["Conversion Rate"] = (
    channel_stats["Enrollments"] / channel_stats["Leads"] * 100
)

channel_stats["Cost per Enrollment"] = (
    channel_stats["Monthly_Cost"] / channel_stats["Enrollments"]
)

fig = px.bar(channel_stats, x="Channel", y="Leads", title="Leads by Channel")
st.plotly_chart(fig, use_container_width=True)

fig2 = px.bar(channel_stats, x="Channel", y="Conversion Rate",
              title="Conversion Rate (%)")
st.plotly_chart(fig2, use_container_width=True)

fig3 = px.bar(channel_stats, x="Channel", y="Cost per Enrollment",
              title="Cost per Enrollment")
st.plotly_chart(fig3, use_container_width=True)

# =========================
# FUNNEL
# =========================
st.subheader("Funnel Analysis")

funnel_data = pd.DataFrame({
    "Stage": ["Leads", "Counselling", "Application", "Enrollment"],
    "Count": [total_leads, counselling, applications, enrolled]
})

fig4 = px.funnel(funnel_data, x="Count", y="Stage")
st.plotly_chart(fig4, use_container_width=True)

# =========================
# CITY ANALYSIS
# =========================
st.subheader("City-wise Leads")

city_data = df_filtered.groupby("City")["Lead_ID"].count().reset_index()
fig5 = px.bar(city_data, x="City", y="Lead_ID", title="Leads by City")
st.plotly_chart(fig5, use_container_width=True)

# =========================
# COURSE DEMAND
# =========================
st.subheader("Course Demand")

course_data = df_filtered.groupby(["Lead_Source", "Course_Interest"]) \
    ["Lead_ID"].count().reset_index()

fig6 = px.sunburst(course_data,
                  path=["Lead_Source", "Course_Interest"],
                  values="Lead_ID",
                  title="Course Demand by Channel")
st.plotly_chart(fig6, use_container_width=True)

# =========================
# MONTHLY TREND
# =========================
st.subheader("Monthly Trend")

df_filtered["month"] = df_filtered["Date"].dt.to_period("M").astype(str)

monthly = df_filtered.groupby(["month", "Lead_Source"])["Lead_ID"] \
    .count().reset_index()

fig7 = px.line(monthly, x="month", y="Lead_ID", color="Lead_Source",
               title="Monthly Lead Trend")
st.plotly_chart(fig7, use_container_width=True)
