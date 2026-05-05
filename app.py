import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# =========================
# CLEAN WHITE BASE
# =========================
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #ffffff !important;
}
.block-container {
    padding-top: 4rem !important;
    padding-left: 3rem;
    padding-right: 3rem;
}
.headline { font-size: 28px; font-weight: 700; }
.sub { color: #6b7280; margin-bottom: 15px; }
.kpi { border-top: 3px solid #2563eb; padding-top: 8px; }
.kpi-title { font-size: 12px; color: #6b7280; }
.kpi-value { font-size: 22px; font-weight: 600; }
.exhibit { border: 1px solid #e5e7eb; padding: 12px; border-radius: 6px; }
.exhibit-title { font-weight: 600; margin-bottom: 6px; }
.takeaway { margin-top: 6px; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load():
    leads = pd.read_csv("dataset/leads_unclean_25000.csv")
    funnel = pd.read_csv("dataset/funnel_unclean_25000.csv")
    cost = pd.read_csv("dataset/marketing_cost_unclean.csv")

    leads = leads.drop_duplicates()
    leads["Lead_Source"] = leads["Lead_Source"].str.title()
    leads = leads.dropna(subset=["Lead_Source"])
    leads["Date"] = pd.to_datetime(leads["Date"], errors="coerce")
    leads = leads.dropna(subset=["Date"])

    def clean(c):
        return c.str.lower().map({"yes":"Yes","no":"No"})

    funnel["Enrolled"] = clean(funnel["Enrolled"]).fillna("No")

    cost["Monthly_Cost"] = pd.to_numeric(
        cost["Monthly_Cost"].astype(str)
        .str.replace(",", "")
        .str.replace("INR",""),
        errors="coerce"
    )

    df = leads.merge(funnel, on="Lead_ID")
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    return df, cost

df, cost = load()

# =========================
# METRICS
# =========================
total_leads = len(df)
enrolled = (df["Enrolled"]=="Yes").sum()
conversion = enrolled/total_leads*100
cpe = cost["Monthly_Cost"].sum()/enrolled

# =========================
# CHANNEL STATS
# =========================
lead_counts = df.groupby("Lead_Source")["Lead_ID"].count().reset_index()
enr = df[df["Enrolled"]=="Yes"].groupby("Lead_Source")["Lead_ID"].count().reset_index()

channel = lead_counts.merge(enr, on="Lead_Source")
channel.columns = ["Channel","Leads","Enrollments"]

channel = channel.merge(cost, on="Channel")
channel["Conversion Rate"] = channel["Enrollments"]/channel["Leads"]*100
channel["Cost per Enrollment"] = channel["Monthly_Cost"]/channel["Enrollments"]

best = channel.sort_values("Cost per Enrollment").iloc[0]
worst = channel.sort_values("Cost per Enrollment", ascending=False).iloc[0]

# =========================
# HEADLINE
# =========================
st.markdown(f"""
<div class="headline">
Referral is most efficient (₹{best['Cost per Enrollment']:.0f}); Instagram is ~{(worst['Cost per Enrollment']/best['Cost per Enrollment']):.1f}× more expensive.
</div>
<div class="sub">
{total_leads:,} leads | {enrolled:,} enrollments | {conversion:.1f}% CVR | ₹{cpe:.0f} CPE
</div>
""", unsafe_allow_html=True)

# =========================
# KPI STRIP
# =========================
cols = st.columns(4)
for i, (t, v) in enumerate([
    ("Total Leads", total_leads),
    ("Enrollments", enrolled),
    ("Conversion Rate", f"{conversion:.1f}%"),
    ("Cost / Enrollment", f"₹{cpe:.0f}")
]):
    cols[i].markdown(f"""
    <div class="kpi">
        <div class="kpi-title">{t}</div>
        <div class="kpi-value">{v}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =========================
# EXHIBIT 1: ROI (FIXED COLORS)
# =========================
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="exhibit">', unsafe_allow_html=True)
    st.markdown("Channel Efficiency vs Cost")

    fig = px.scatter(
        channel,
        x="Cost per Enrollment",
        y="Conversion Rate",
        color="Channel",  # FIXED
        size="Leads",
        text="Channel"
    )

    fig.update_traces(textposition="top center")

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
        height=350
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Insight:** Referral best ROI; Instagram inefficient.")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# EXHIBIT 2: FUNNEL
# =========================
with col2:
    st.markdown('<div class="exhibit">', unsafe_allow_html=True)

    funnel_data = pd.DataFrame({
        "Stage":["Leads","Enrollment"],
        "Count":[total_leads,enrolled]
    })

    fig2 = px.funnel(funnel_data, x="Count", y="Stage")
    fig2.update_layout(height=350)

    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Insight:** Major drop happens early.")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# NEW VISUAL 1: CHANNEL RANKING
# =========================
st.markdown("### Channel Comparison")

table = channel.sort_values("Cost per Enrollment")

st.dataframe(
    table[["Channel","Leads","Enrollments","Conversion Rate","Cost per Enrollment"]],
    use_container_width=True
)

# =========================
# NEW VISUAL 2: COURSE DEMAND
# =========================
st.markdown("### Course Demand by Channel")

course = df.groupby(["Lead_Source","Course_Interest"])["Lead_ID"].count().reset_index()

fig3 = px.bar(
    course,
    x="Lead_Source",
    y="Lead_ID",
    color="Course_Interest",
    barmode="stack"
)

fig3.update_layout(height=400)

st.plotly_chart(fig3, use_container_width=True)
