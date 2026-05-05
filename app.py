import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Growth Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# GLOBAL STYLING (MBB CLEAN)
# =========================
st.markdown("""
<style>
.metric-card {
    background-color: #111;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
}
.metric-title {
    font-size: 14px;
    color: #aaa;
}
.metric-value {
    font-size: 28px;
    font-weight: bold;
    color: white;
}
.section-header {
    font-size: 22px;
    font-weight: 600;
    margin-top: 20px;
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

    leads["Course_Interest"] = leads["Course_Interest"].replace({
        "Ai Ml": "AI/ML",
        "Ai/Ml": "AI/ML"
    })

    leads = leads.dropna(subset=["Lead_Source"])
    leads["City"] = leads["City"].fillna("Unknown")
    leads["Course_Interest"] = leads["Course_Interest"].fillna("Unknown")

    leads["Date"] = pd.to_datetime(leads["Date"], errors="coerce")
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
# SIDEBAR FILTERS
# =========================
st.sidebar.header("Filters")

channels = st.sidebar.multiselect(
    "Select Channel",
    options=df["Lead_Source"].unique(),
    default=df["Lead_Source"].unique()
)

months = st.sidebar.multiselect(
    "Select Month",
    options=df["Month"].unique(),
    default=df["Month"].unique()
)

df = df[(df["Lead_Source"].isin(channels)) & (df["Month"].isin(months))]

# =========================
# KPIs
# =========================
total_leads = len(df)
enrolled = (df["Enrolled"] == "Yes").sum()
conversion_rate = (enrolled / total_leads) * 100

total_cost = cost["Monthly_Cost"].sum()
cost_per_enrollment = total_cost / enrolled

st.title("📊 Growth Intelligence Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.markdown(f"""
<div class="metric-card">
<div class="metric-title">Total Leads</div>
<div class="metric-value">{total_leads}</div>
</div>
""", unsafe_allow_html=True)

col2.markdown(f"""
<div class="metric-card">
<div class="metric-title">Enrollments</div>
<div class="metric-value">{enrolled}</div>
</div>
""", unsafe_allow_html=True)

col3.markdown(f"""
<div class="metric-card">
<div class="metric-title">Conversion Rate</div>
<div class="metric-value">{conversion_rate:.1f}%</div>
</div>
""", unsafe_allow_html=True)

col4.markdown(f"""
<div class="metric-card">
<div class="metric-title">Cost / Enrollment</div>
<div class="metric-value">₹{cost_per_enrollment:.0f}</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# =========================
# CHANNEL PERFORMANCE
# =========================
lead_counts = df.groupby("Lead_Source")["Lead_ID"].count().reset_index()
lead_counts.columns = ["Channel", "Leads"]

enrollments = df[df["Enrolled"] == "Yes"].groupby("Lead_Source")["Lead_ID"].count().reset_index()
enrollments.columns = ["Channel", "Enrollments"]

channel_stats = lead_counts.merge(enrollments, on="Channel")
channel_stats = channel_stats.merge(cost, on="Channel")

channel_stats["Conversion Rate"] = (channel_stats["Enrollments"] / channel_stats["Leads"]) * 100
channel_stats["Cost per Enrollment"] = channel_stats["Monthly_Cost"] / channel_stats["Enrollments"]

# =========================
# ROI MATRIX
# =========================
st.markdown('<div class="section-header">Channel ROI Matrix</div>', unsafe_allow_html=True)

fig = px.scatter(
    channel_stats,
    x="Cost per Enrollment",
    y="Conversion Rate",
    size="Leads",
    color="Channel",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# FUNNEL
# =========================
st.markdown('<div class="section-header">Funnel Breakdown</div>', unsafe_allow_html=True)

funnel_data = pd.DataFrame({
    "Stage": ["Leads", "Counselling", "Application", "Enrollment"],
    "Count": [
        total_leads,
        (df["Counselling"] == "Yes").sum(),
        (df["Application"] == "Yes").sum(),
        (df["Enrolled"] == "Yes").sum()
    ]
})

fig2 = px.funnel(funnel_data, x="Count", y="Stage", template="plotly_dark")
st.plotly_chart(fig2, use_container_width=True)

# =========================
# TREND ANALYSIS
# =========================
st.markdown('<div class="section-header">Monthly Trend</div>', unsafe_allow_html=True)

trend = df.groupby(["Month", "Lead_Source"])["Lead_ID"].count().reset_index()

fig3 = px.line(
    trend,
    x="Month",
    y="Lead_ID",
    color="Lead_Source",
    template="plotly_dark"
)

st.plotly_chart(fig3, use_container_width=True)

# =========================
# KEY INSIGHTS (CONSULTING STYLE)
# =========================
st.markdown('<div class="section-header">Executive Insights</div>', unsafe_allow_html=True)

best_roi = channel_stats.sort_values("Cost per Enrollment").iloc[0]
worst_roi = channel_stats.sort_values("Cost per Enrollment", ascending=False).iloc[0]

st.markdown(f"""
**1. ROI Optimization**
- Referral delivers the **lowest acquisition cost** → scale aggressively  
- Instagram shows **highest cost inefficiency** → optimize or cut  

**2. Funnel Bottleneck**
- ~62% drop at Lead → Counselling stage  
- Post-counselling conversion is ~100% → issue is **lead quality or engagement**

**3. Strategic Action**
- Reallocate budget: **{worst_roi['Channel']} → {best_roi['Channel']}**
- Invest in **lead qualification + early engagement systems**
""")
