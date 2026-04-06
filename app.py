import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Lead Source Performance Analysis")

# =========================
# LOAD DATA
# =========================
leads = pd.read_csv("dataset/leads_unclean_25000.csv")
funnel = pd.read_csv("dataset/funnel_unclean_25000.csv")
cost = pd.read_csv("dataset/marketing_cost_unclean.csv")



# =========================
# CLEAN LEADS DATA
# =========================
leads = leads.drop_duplicates()

leads["City"] = leads["City"].str.strip().str.title()
leads["Course_Interest"] = leads["Course_Interest"].str.strip().str.title()

leads["Course_Interest"] = leads["Course_Interest"].replace({
    "Ai Ml": "AI/ML",
    "Ai/Ml": "AI/ML"
})

leads["Lead_Source"] = leads["Lead_Source"].str.strip().str.title()

leads = leads.dropna(subset=["Lead_Source"])
leads["City"] = leads["City"].fillna("Unknown")
leads["Course_Interest"] = leads["Course_Interest"].fillna("Unknown")

leads["Date"] = pd.to_datetime(
    leads["Date"],
    errors="coerce",
    format="mixed"
)

#leads["Date"] = pd.to_datetime(leads["Date"], errors="coerce", dayfirst=True)
leads = leads.dropna(subset=["Date"])

# =========================
# CLEAN FUNNEL DATA
# =========================
def clean_yes_no(col):
    return col.str.strip().str.lower().replace({
        "yes": "Yes",
        "y": "Yes",
        "no": "No",
        "n": "No"
    })

funnel["Counselling"] = clean_yes_no(funnel["Counselling"])
funnel["Application"] = clean_yes_no(funnel["Application"])
funnel["Enrolled"] = clean_yes_no(funnel["Enrolled"])

funnel = funnel.fillna("No")

# =========================
# CLEAN COST DATA
# =========================
cost["Channel"] = cost["Channel"].str.strip().str.title()
cost = cost.dropna()

cost["Monthly_Cost"] = cost["Monthly_Cost"].astype(str)
cost["Monthly_Cost"] = cost["Monthly_Cost"].str.replace(",", "")
cost["Monthly_Cost"] = cost["Monthly_Cost"].str.replace("INR", "")
cost["Monthly_Cost"] = cost["Monthly_Cost"].str.replace("Thirty Thousand", "30000")
cost["Monthly_Cost"] = cost["Monthly_Cost"].str.strip()

cost["Monthly_Cost"] = pd.to_numeric(cost["Monthly_Cost"], errors="coerce")

# =========================
# MERGE
# =========================
df = leads.merge(funnel, on="Lead_ID")

st.subheader("Merged Data Shape")
st.write(df.shape)

# =========================
# CHANNEL PERFORMANCE
# =========================
lead_counts = df.groupby("Lead_Source")["Lead_ID"].count().sort_values(ascending=False)
lead_counts = pd.DataFrame(lead_counts).reset_index()
lead_counts = lead_counts.rename(columns={"Lead_Source": "Channel", "Lead_ID": "lead_counts"})

st.subheader("Lead Counts by Channel")
st.dataframe(lead_counts)

enrollments = df[df["Enrolled"] == "Yes"].groupby("Lead_Source")["Lead_ID"].count()
enrollments = pd.DataFrame(enrollments).reset_index()
enrollments = enrollments.rename(columns={"Lead_Source": "Channel", "Lead_ID": "Enrollments"})

st.subheader("Enrollments by Channel")
st.dataframe(enrollments)

channel_stats = lead_counts.merge(enrollments, on="Channel")
channel_stats["Conversion_rate"] = (channel_stats["Enrollments"] / channel_stats["lead_counts"]) * 100
channel_stats["Conversion_rate"] = channel_stats["Conversion_rate"].round(2)

channel_stats = channel_stats.merge(cost, on="Channel")

channel_stats["cost_per_enrollment"] = channel_stats["Monthly_Cost"] / channel_stats["Enrollments"]

st.subheader("Channel Stats")
st.dataframe(channel_stats)

# =========================
# FUNNEL ANALYSIS
# =========================
total_leads = df.shape[0]
counselling = df[df["Counselling"] == "Yes"].shape[0]
application = df[df["Application"] == "Yes"].shape[0]
enrolled = df[df["Enrolled"] == "Yes"].shape[0]

st.subheader("Funnel Counts")
st.write("Leads:", total_leads)
st.write("Counselling:", counselling)
st.write("Application:", application)
st.write("Enrolled:", enrolled)

st.subheader("Conversion Rates")
st.write("Lead → Counselling:", round((counselling / total_leads) * 100, 2), "%")
st.write("Counselling → Application:", round((application / counselling) * 100, 2), "%")
st.write("Application → Enrollment:", round((enrolled / application) * 100, 2), "%")

# =========================
# CHANNEL FUNNEL
# =========================
funnel_channel = df.groupby("Lead_Source").agg({
    "Counselling": lambda x: (x == "Yes").sum(),
    "Application": lambda x: (x == "Yes").sum(),
    "Enrolled": lambda x: (x == "Yes").sum(),
    "Lead_ID": "count"
}).reset_index()

funnel_channel.columns = ["Channel", "Counselling", "Application", "Enrolled", "Leads"]

st.subheader("Channel-wise Funnel")
st.dataframe(funnel_channel)

# =========================
# CITY CHANNEL
# =========================
city_channel = df.groupby(["City", "Lead_Source"])["Lead_ID"].count().reset_index()
city_channel.columns = ["City", "Channel", "Leads"]

st.subheader("City-wise Channel Performance")
st.dataframe(city_channel.head())

# =========================
# COURSE DEMAND
# =========================
course_channel = df.groupby(["Lead_Source", "Course_Interest"])["Lead_ID"].count().reset_index()
course_channel = course_channel.sort_values(by="Lead_ID", ascending=False)

st.subheader("Course Demand by Channel")
st.dataframe(course_channel)

# =========================
# MONTHLY TREND
# =========================
df["month"] = df["Date"].dt.to_period("M")

monthly_trend = df.groupby(["month", "Lead_Source"])["Lead_ID"].count().reset_index()

st.subheader("Monthly Trend")
st.dataframe(monthly_trend.head())

# =========================
# VISUALS (Same as notebook)
# =========================
st.subheader("Leads per Channel")
fig1, ax1 = plt.subplots()
funnel_channel.plot(kind="bar", x="Channel", y="Leads", ax=ax1)
st.pyplot(fig1)

st.subheader("Funnel Drop-off")
funnel_values = [total_leads, counselling, application, enrolled]

fig2, ax2 = plt.subplots()
ax2.plot(["Leads", "Counselling", "Application", "Enrollment"], funnel_values, marker='o')
st.pyplot(fig2)
