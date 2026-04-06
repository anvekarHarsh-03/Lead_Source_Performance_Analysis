import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 Lead Source Performance Dashboard")

# =========================
# LOAD + CLEAN (FIXED DATE)
# =========================
@st.cache_data
def load_data():
    leads = pd.read_csv("dataset/leads_unclean_25000.csv")
    funnel = pd.read_csv("dataset/funnel_unclean_25000.csv")
    cost = pd.read_csv("dataset/marketing_cost_unclean.csv")

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

    # ✅ FIXED DATE
    leads["Date"] = pd.to_datetime(leads["Date"], errors="coerce", format="mixed")
    leads = leads.dropna(subset=["Date"])

    def clean_yes_no(col):
        return col.str.strip().str.lower().replace({
            "yes": "Yes", "y": "Yes",
            "no": "No", "n": "No"
        })

    funnel["Counselling"] = clean_yes_no(funnel["Counselling"])
    funnel["Application"] = clean_yes_no(funnel["Application"])
    funnel["Enrolled"] = clean_yes_no(funnel["Enrolled"])
    funnel = funnel.fillna("No")

    cost["Channel"] = cost["Channel"].str.strip().str.title()
    cost = cost.dropna()

    cost["Monthly_Cost"] = cost["Monthly_Cost"].astype(str)
    cost["Monthly_Cost"] = cost["Monthly_Cost"].str.replace(",", "")
    cost["Monthly_Cost"] = cost["Monthly_Cost"].str.replace("INR", "")
    cost["Monthly_Cost"] = cost["Monthly_Cost"].str.replace("Thirty Thousand", "30000")
    cost["Monthly_Cost"] = pd.to_numeric(cost["Monthly_Cost"], errors="coerce")

    df = leads.merge(funnel, on="Lead_ID")

    return df, cost

df, cost = load_data()

# =========================
# KPIs
# =========================
total_leads = df.shape[0]
enrolled = df[df["Enrolled"] == "Yes"].shape[0]
conversion_rate = (enrolled / total_leads) * 100

# cost per enrollment (blended)
total_cost = cost["Monthly_Cost"].sum()
cost_per_enrollment = total_cost / enrolled

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Leads", total_leads)
col2.metric("Enrollments", enrolled)
col3.metric("Conversion Rate", f"{conversion_rate:.2f}%")
col4.metric("Cost / Enrollment", f"₹{cost_per_enrollment:.0f}")

st.divider()

# =========================
# CHANNEL PERFORMANCE
# =========================
lead_counts = df.groupby("Lead_Source")["Lead_ID"].count().reset_index()
lead_counts.columns = ["Channel", "Leads"]

enrollments = df[df["Enrolled"] == "Yes"] \
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

# =========================
# ROI CHART
# =========================
st.subheader("📈 Channel ROI Analysis")

fig = px.scatter(
    channel_stats,
    x="Cost per Enrollment",
    y="Conversion Rate",
    size="Leads",
    color="Channel",
    hover_name="Channel",
    title="Efficiency vs Effectiveness"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# FUNNEL
# =========================
st.subheader("🔻 Funnel Drop-off")

funnel_data = pd.DataFrame({
    "Stage": ["Leads", "Counselling", "Application", "Enrollment"],
    "Count": [
        total_leads,
        (df["Counselling"] == "Yes").sum(),
        (df["Application"] == "Yes").sum(),
        (df["Enrolled"] == "Yes").sum()
    ]
})

fig2 = px.funnel(funnel_data, x="Count", y="Stage")
st.plotly_chart(fig2, use_container_width=True)

# =========================
# AUTO INSIGHTS (MBB STYLE)
# =========================
st.subheader("💡 Key Insights")

best_roi = channel_stats.sort_values("Cost per Enrollment").iloc[0]
worst_roi = channel_stats.sort_values("Cost per Enrollment", ascending=False).iloc[0]

best_conv = channel_stats.sort_values("Conversion Rate", ascending=False).iloc[0]

st.markdown(f"""
- **Best ROI Channel:** {best_roi['Channel']} (₹{best_roi['Cost per Enrollment']:.0f} per enrollment)
- **Worst ROI Channel:** {worst_roi['Channel']} (₹{worst_roi['Cost per Enrollment']:.0f})
- **Highest Conversion Channel:** {best_conv['Channel']} ({best_conv['Conversion Rate']:.2f}%)

### Strategic Takeaway:
- Reallocate budget from **{worst_roi['Channel']} → {best_roi['Channel']}**
- Improve **top-of-funnel conversion (Leads → Counselling)** — biggest drop-off
""")
