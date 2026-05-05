import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(layout="wide")

# =========================
# FORCE LIGHT + FIX HEADER OVERLAP
# =========================
st.markdown("""
<style>

/* FULL WHITE CANVAS */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #ffffff !important;
}

/* FIX TOP SPACING (CRITICAL) */
.block-container {
    padding-top: 4rem !important;
    padding-left: 3rem;
    padding-right: 3rem;
}

/* HEADER */
[data-testid="stHeader"] {
    background: #ffffff !important;
    height: 60px;
}

/* TYPOGRAPHY */
.headline {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
    line-height: 1.4;
    margin-bottom: 8px;
}

.sub {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 15px;
}

/* KPI STRIP */
.kpi {
    border-top: 3px solid #2563eb;
    padding-top: 8px;
}

.kpi-title {
    font-size: 12px;
    color: #6b7280;
}

.kpi-value {
    font-size: 22px;
    font-weight: 600;
    color: #111827;
}

/* EXHIBIT BLOCK */
.exhibit {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 12px;
}

.exhibit-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 6px;
}

.takeaway {
    font-size: 13px;
    margin-top: 6px;
}

/* DIVIDER */
hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 14px 0;
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
# METRICS
# =========================
total_leads = len(df)
enrolled = (df["Enrolled"] == "Yes").sum()
conversion_rate = (enrolled / total_leads) * 100
total_cost = cost["Monthly_Cost"].sum()
cpe = total_cost / enrolled

# =========================
# CHANNEL STATS
# =========================
lead_counts = df.groupby("Lead_Source")["Lead_ID"].count().reset_index()
lead_counts.columns = ["Channel", "Leads"]

enr = df[df["Enrolled"] == "Yes"].groupby("Lead_Source")["Lead_ID"].count().reset_index()
enr.columns = ["Channel", "Enrollments"]

channel = lead_counts.merge(enr, on="Channel").merge(cost, on="Channel")
channel["Conversion Rate"] = channel["Enrollments"] / channel["Leads"] * 100
channel["Cost per Enrollment"] = channel["Monthly_Cost"] / channel["Enrollments"]

best = channel.sort_values("Cost per Enrollment").iloc[0]
worst = channel.sort_values("Cost per Enrollment", ascending=False).iloc[0]

# =========================
# HEADLINE
# =========================
st.markdown(f"""
<div class="headline">
Referral delivers the lowest acquisition cost (₹{best['Cost per Enrollment']:.0f}); 
Instagram is ~{(worst['Cost per Enrollment']/best['Cost per Enrollment']):.1f}× more expensive — reallocate budget.
</div>

<div class="sub">
Context: {total_leads:,} leads | {enrolled:,} enrollments | {conversion_rate:.1f}% CVR | ₹{cpe:.0f} blended CPE
</div>
""", unsafe_allow_html=True)

# =========================
# KPI STRIP
# =========================
c1, c2, c3, c4 = st.columns(4)

def kpi(title, value):
    return f"""
    <div class="kpi">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """

c1.markdown(kpi("Total Leads", f"{total_leads:,}"), unsafe_allow_html=True)
c2.markdown(kpi("Enrollments", f"{enrolled:,}"), unsafe_allow_html=True)
c3.markdown(kpi("Conversion Rate", f"{conversion_rate:.1f}%"), unsafe_allow_html=True)
c4.markdown(kpi("Cost / Enrollment", f"₹{cpe:.0f}"), unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# =========================
# EXHIBIT 1: ROI
# =========================
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="exhibit">', unsafe_allow_html=True)
    st.markdown('<div class="exhibit-title">Exhibit 1 — Channel efficiency vs cost</div>', unsafe_allow_html=True)

    fig = px.scatter(
        channel,
        x="Cost per Enrollment",
        y="Conversion Rate",
        size="Leads",
        text="Channel"
    )

    fig.update_traces(marker=dict(color="#2563eb"), textposition="top center")

    fig.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
        height=320
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="takeaway">
    <b>Takeaway:</b> Referral is most efficient; Instagram is highest cost with no conversion advantage.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# EXHIBIT 2: FUNNEL
# =========================
with col2:
    st.markdown('<div class="exhibit">', unsafe_allow_html=True)
    st.markdown('<div class="exhibit-title">Exhibit 2 — Conversion funnel</div>', unsafe_allow_html=True)

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
        font=dict(color="black"),
        height=320
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    <div class="takeaway">
    <b>Takeaway:</b> Major drop occurs before counselling — improve early engagement.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# EXHIBIT 3: TREND
# =========================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="exhibit">', unsafe_allow_html=True)
st.markdown('<div class="exhibit-title">Exhibit 3 — Monthly trend</div>', unsafe_allow_html=True)

trend = df.groupby("Month")["Lead_ID"].count().reset_index()

fig3 = px.line(trend, x="Month", y="Lead_ID", markers=True)
fig3.update_traces(line=dict(color="#2563eb"))

fig3.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="black"),
    height=300
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("""
<div class="takeaway">
<b>Takeaway:</b> No consistent upward trend — focus on channel mix, not just volume.
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
