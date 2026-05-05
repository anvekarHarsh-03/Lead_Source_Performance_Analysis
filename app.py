import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# =========================
# ADVANCED UI CSS (REPLICA)
# =========================
st.markdown("""
<style>

/* GLOBAL */
.main {
    background-color: #f4f6fb;
    padding: 0;
}

/* REMOVE DEFAULT PADDING */
.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #111827 !important;
    color: white;
}

.sidebar-title {
    font-size: 18px;
    font-weight: 600;
    padding: 10px 0;
}

/* HEADER */
.topbar {
    background-color: white;
    padding: 15px 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
}

/* KPI CARDS */
.kpi {
    background: linear-gradient(135deg, #5b5cf6, #7c3aed);
    color: white;
    padding: 18px;
    border-radius: 10px;
}

.kpi-title {
    font-size: 13px;
    opacity: 0.8;
}

.kpi-value {
    font-size: 26px;
    font-weight: bold;
}

/* CARDS */
.card {
    background-color: white;
    padding: 18px;
    border-radius: 10px;
    box-shadow: 0px 3px 8px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

.card-title {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# DATA LOAD
# =========================
@st.cache_data
def load_data():
    leads = pd.read_csv("dataset/leads_unclean_25000.csv")
    funnel = pd.read_csv("dataset/funnel_unclean_25000.csv")
    cost = pd.read_csv("dataset/marketing_cost_unclean.csv")

    leads = leads.drop_duplicates()
    leads["Lead_Source"] = leads["Lead_Source"].str.title()
    leads = leads.dropna(subset=["Lead_Source"])

    leads["Date"] = pd.to_datetime(leads["Date"], errors="coerce")
    leads = leads.dropna(subset=["Date"])

    funnel["Enrolled"] = funnel["Enrolled"].str.lower().map({
        "yes":"Yes","no":"No"
    })
    funnel = funnel.fillna("No")

    cost["Monthly_Cost"] = pd.to_numeric(
        cost["Monthly_Cost"].astype(str)
        .str.replace(",", "")
        .str.replace("INR", ""),
        errors="coerce"
    )

    df = leads.merge(funnel, on="Lead_ID")
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    return df, cost

df, cost = load_data()

# =========================
# SIDEBAR NAV
# =========================
st.sidebar.markdown('<div class="sidebar-title">📊 Dashboard</div>', unsafe_allow_html=True)
menu = st.sidebar.radio("", ["Overview", "Channels", "Funnel"])

# =========================
# HEADER BAR
# =========================
st.markdown("""
<div class="topbar">
<b>Home</b> &nbsp; / &nbsp; Dashboard
</div>
""", unsafe_allow_html=True)

# =========================
# KPIs
# =========================
total_leads = len(df)
enrolled = (df["Enrolled"] == "Yes").sum()
conversion = enrolled / total_leads * 100
cpe = cost["Monthly_Cost"].sum() / enrolled

c1, c2, c3, c4 = st.columns(4)

def kpi(title, value):
    return f"""
    <div class="kpi">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """

c1.markdown(kpi("Total Leads", total_leads), unsafe_allow_html=True)
c2.markdown(kpi("Enrollments", enrolled), unsafe_allow_html=True)
c3.markdown(kpi("Conversion Rate", f"{conversion:.1f}%"), unsafe_allow_html=True)
c4.markdown(kpi("Cost / Enrollment", f"₹{cpe:.0f}"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================
# CHANNEL STATS
# =========================
lead_counts = df.groupby("Lead_Source")["Lead_ID"].count().reset_index()
enrollments = df[df["Enrolled"]=="Yes"].groupby("Lead_Source")["Lead_ID"].count().reset_index()

channel_stats = lead_counts.merge(enrollments, on="Lead_Source")
channel_stats.columns = ["Channel", "Leads", "Enrollments"]

# =========================
# GRID LAYOUT
# =========================
col1, col2 = st.columns(2)

# ROI
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Channel ROI</div>', unsafe_allow_html=True)

    fig = px.scatter(channel_stats, x="Leads", y="Enrollments", color="Channel")
    fig.update_layout(height=300)

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# BAR
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Leads by Channel</div>', unsafe_allow_html=True)

    fig2 = px.bar(channel_stats, x="Channel", y="Leads")
    fig2.update_layout(height=300)

    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# SECOND ROW
# =========================
col3, col4 = st.columns(2)

# FUNNEL
with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Funnel</div>', unsafe_allow_html=True)

    funnel_data = pd.DataFrame({
        "Stage": ["Leads","Enrollment"],
        "Count": [total_leads, enrolled]
    })

    fig3 = px.funnel(funnel_data, x="Count", y="Stage")
    fig3.update_layout(height=300)

    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# TREND
with col4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Monthly Trend</div>', unsafe_allow_html=True)

    trend = df.groupby("Month")["Lead_ID"].count().reset_index()

    fig4 = px.line(trend, x="Month", y="Lead_ID")
    fig4.update_layout(height=300)

    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
