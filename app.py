import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(layout="wide")

# =========================
# MBB CLEAN STYLING
# =========================
st.markdown("""
<style>

.main {
    background-color: #ffffff;
}

.block-container {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
}

/* KPI Cards */
.card {
    background-color: white;
    padding: 16px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
}

.kpi-title {
    font-size: 12px;
    color: #6b7280;
}

.kpi-value {
    font-size: 24px;
    font-weight: 600;
    color: #111827;
}

/* Section */
.section-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 10px;
}

/* Insight */
.insight {
    font-size: 15px;
    font-weight: 500;
    margin-top: 5px;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA
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

    leads = leads.dropna(subset=["Lead_Source"])
    leads["Date"] = pd.to_datetime(leads["Date"], errors="coerce")
    leads = leads.dropna(subset=["Date"])

    def clean(col):
        return col.str.strip().str.lower().replace({
            "yes": "Yes", "y": "Yes",
            "no": "No", "n": "No"
        })

    funnel["Counselling"] = clean(funnel["Counselling"])
    funnel["Application"] = clean(funnel["Application"])
    funnel["Enrolled"] = clean(funnel["Enrolled"])
    funnel = funnel.fillna("No")

    cost["Channel"] = cost["Channel"].str.strip().str.title()
    cost["Monthly_Cost"] = (
        cost["Monthly_Cost"]
        .astype(str)
        .str.replace(",", "")
        .str.replace("INR", "")
        .str.replace("Thirty Thousand", "30000")
    )
    cost["Monthly_Cost"] = pd.to_numeric(cost["Monthly_Cost"], errors="coerce")

    df = leads.merge(funnel, on="Lead_ID")
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    return df, cost

df, cost = load_data()

# =========================
# KPIs
# =========================
total_leads = len(df)
enrolled = (df["Enrolled"] == "Yes").sum()
conversion_rate = (enrolled / total_leads) * 100
total_cost = cost["Monthly_Cost"].sum()
cost_per_enrollment = total_cost / enrolled

# =========================
# CHANNEL STATS
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
# TOP HEADLINE (MOST IMPORTANT)
# =========================
best_roi = channel_stats.sort_values("Cost per Enrollment").iloc[0]
worst_roi = channel_stats.sort_values("Cost per Enrollment", ascending=False).iloc[0]

st.markdown(f"""
### 📌 Key Insight  
**{best_roi['Channel']} delivers the lowest cost per enrollment (₹{best_roi['Cost per Enrollment']:.0f}), while {worst_roi['Channel']} is the least efficient — immediate budget reallocation opportunity.**
""")

# =========================
# KPI ROW
# =========================
col1, col2, col3, col4 = st.columns(4)

def kpi(title, value):
    return f"""
    <div class="card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """

col1.markdown(kpi("Total Leads", total_leads), unsafe_allow_html=True)
col2.markdown(kpi("Enrollments", enrolled), unsafe_allow_html=True)
col3.markdown(kpi("Conversion Rate", f"{conversion_rate:.1f}%"), unsafe_allow_html=True)
col4.markdown(kpi("Cost / Enrollment", f"₹{cost_per_enrollment:.0f}"), unsafe_allow_html=True)

st.divider()

# =========================
# ROI ANALYSIS
# =========================
st.markdown('<div class="section-title">Channel Efficiency vs Cost (ROI)</div>', unsafe_allow_html=True)

fig = px.scatter(
    channel_stats,
    x="Cost per Enrollment",
    y="Conversion Rate",
    size="Leads",
    color="Channel"
)

fig.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="black"),
    xaxis=dict(showgrid=True, gridcolor="#e5e7eb"),
    yaxis=dict(showgrid=True, gridcolor="#e5e7eb")
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
<div class="insight">
Instagram drives volume but at significantly higher cost — inefficient scaling channel.
</div>
""", unsafe_allow_html=True)

# =========================
# FUNNEL
# =========================
st.markdown('<div class="section-title">Conversion Funnel — Primary Drop-off at Top</div>', unsafe_allow_html=True)

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

fig2.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="black")
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("""
<div class="insight">
~62% of leads drop before counselling — biggest leverage point is early-stage engagement.
</div>
""", unsafe_allow_html=True)

# =========================
# TREND
# =========================
st.markdown('<div class="section-title">Monthly Lead Trend</div>', unsafe_allow_html=True)

trend = df.groupby("Month")["Lead_ID"].count().reset_index()

fig3 = px.line(trend, x="Month", y="Lead_ID")

fig3.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="black"),
    xaxis=dict(showgrid=True, gridcolor="#e5e7eb"),
    yaxis=dict(showgrid=True, gridcolor="#e5e7eb")
)

st.plotly_chart(fig3, use_container_width=True)
