import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(layout="wide")

# =========================
# BOOTSTRAP-LIKE CSS
# =========================
st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

.sidebar .sidebar-content {
    background-color: #111827;
}

.card {
    background-color: white;
    padding: 18px;
    border-radius: 10px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
}

.kpi-card {
    background: linear-gradient(135deg, #4f46e5, #6366f1);
    color: white;
    padding: 20px;
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

.section-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA (same as yours)
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

    def clean(col):
        return col.str.lower().map({"yes":"Yes","no":"No"})

    funnel["Enrolled"] = clean(funnel["Enrolled"])
    funnel = funnel.fillna("No")

    cost["Monthly_Cost"] = pd.to_numeric(
        cost["Monthly_Cost"].astype(str)
        .str.replace(",", "")
        .str.replace("INR", ""),
        errors="coerce"
    )

    df = leads.merge(funnel, on="Lead_ID")
    return df, cost

df, cost = load_data()

# =========================
# SIDEBAR (LIKE IMAGE)
# =========================
st.sidebar.title("📊 Dashboard")
st.sidebar.markdown("---")

selected = st.sidebar.radio(
    "Navigation",
    ["Overview", "Channel Analysis", "Funnel"]
)

# =========================
# KPIs
# =========================
total_leads = len(df)
enrolled = (df["Enrolled"] == "Yes").sum()
conversion = enrolled / total_leads * 100
cpe = cost["Monthly_Cost"].sum() / enrolled

# =========================
# KPI ROW
# =========================
col1, col2, col3, col4 = st.columns(4)

def kpi(title, value):
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """

col1.markdown(kpi("Total Leads", total_leads), unsafe_allow_html=True)
col2.markdown(kpi("Enrollments", enrolled), unsafe_allow_html=True)
col3.markdown(kpi("Conversion Rate", f"{conversion:.1f}%"), unsafe_allow_html=True)
col4.markdown(kpi("Cost / Enrollment", f"₹{cpe:.0f}"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================
# CHANNEL STATS
# =========================
lead_counts = df.groupby("Lead_Source")["Lead_ID"].count().reset_index()
enrollments = df[df["Enrolled"]=="Yes"].groupby("Lead_Source")["Lead_ID"].count().reset_index()

channel_stats = lead_counts.merge(enrollments, on="Lead_Source")
channel_stats.columns = ["Channel", "Leads", "Enrollments"]

# =========================
# GRID LAYOUT (LIKE IMAGE)
# =========================
col1, col2 = st.columns(2)

# ROI SCATTER
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ROI Matrix</div>', unsafe_allow_html=True)

    fig = px.scatter(
        channel_stats,
        x="Leads",
        y="Enrollments",
        size="Leads",
        color="Channel"
    )

    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# BAR CHART
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Leads by Channel</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="section-title">Funnel</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="section-title">Trend</div>', unsafe_allow_html=True)

    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    trend = df.groupby("Month")["Lead_ID"].count().reset_index()

    fig4 = px.line(trend, x="Month", y="Lead_ID")
    fig4.update_layout(height=300)

    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
