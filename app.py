import streamlit as st
import pandas as pd
import plotly.express as px

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Lead Funnel Dashboard",
    layout="wide"
)

# ======================================================
# GLOBAL STYLING
# ======================================================
st.markdown("""
<style>

/* MAIN BACKGROUND */
html, body, [data-testid="stAppViewContainer"] {
    background-color: white !important;
    color: #111827 !important;
}

/* REMOVE DARK AREAS */
[data-testid="stHeader"] {
    background: white !important;
}

[data-testid="stSidebar"] {
    background: white !important;
}

/* CONTAINER */
.block-container {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
}

/* HEADINGS */
.main-title {
    font-size: 34px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 5px;
}

.sub-title {
    color: #6b7280;
    margin-bottom: 25px;
}

/* KPI BOX */
.kpi-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 18px;
}

.kpi-title {
    font-size: 13px;
    color: #6b7280;
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
}

/* SECTION BOX */
.chart-box {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 15px;
    margin-top: 10px;
}

</style>
""", unsafe_allow_html=True)

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data
def load_data():

    # LOAD CSV
    leads = pd.read_csv("dataset/leads_unclean_25000.csv")
    funnel = pd.read_csv("dataset/funnel_unclean_25000.csv")
    cost = pd.read_csv("dataset/marketing_cost_unclean.csv")

    # ==================================================
    # DEBUG COUNTS
    # ==================================================
    st.write("Original Leads:", len(leads))
    st.write("Original Funnel:", len(funnel))

    # ==================================================
    # CLEAN LEADS
    # ==================================================
    leads["Lead_Source"] = (
        leads["Lead_Source"]
        .astype(str)
        .str.title()
    )

    # DATE FIX
    leads["Date"] = pd.to_datetime(
        leads["Date"],
        errors="coerce",
        dayfirst=True
    )

    st.write("Invalid Dates:", leads["Date"].isna().sum())

    # ==================================================
    # CLEAN FUNNEL
    # ==================================================
    funnel = funnel.drop_duplicates(subset=["Lead_ID"])

    st.write("Funnel after dedupe:", len(funnel))

    # CLEAN ENROLLED COLUMN
    funnel["Enrolled"] = (
        funnel["Enrolled"]
        .astype(str)
        .str.lower()
        .map({
            "yes": "Yes",
            "no": "No"
        })
        .fillna("No")
    )

    # ==================================================
    # CLEAN COST
    # ==================================================
    cost["Monthly_Cost"] = pd.to_numeric(
        cost["Monthly_Cost"]
        .astype(str)
        .str.replace(",", "")
        .str.replace("INR", ""),
        errors="coerce"
    )

    # ==================================================
    # MERGE
    # ==================================================
    df = leads.merge(
        funnel,
        on="Lead_ID",
        how="left"
    )

    df["Enrolled"] = df["Enrolled"].fillna("No")

    st.write("Final Merged Rows:", len(df))

    # MONTH COLUMN
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    return df, cost

# LOAD
df, cost = load_data()

# ======================================================
# METRICS
# ======================================================
total_leads = len(df)

enrolled = (
    df["Enrolled"] == "Yes"
).sum()

conversion = (
    enrolled / total_leads * 100
)

cpe = (
    cost["Monthly_Cost"].sum() / enrolled
)

# ======================================================
# CHANNEL ANALYSIS
# ======================================================
lead_counts = (
    df.groupby("Lead_Source")["Lead_ID"]
    .count()
    .reset_index()
)

enrollment_counts = (
    df[df["Enrolled"] == "Yes"]
    .groupby("Lead_Source")["Lead_ID"]
    .count()
    .reset_index()
)

channel = lead_counts.merge(
    enrollment_counts,
    on="Lead_Source",
    how="left"
)

channel.columns = [
    "Channel",
    "Leads",
    "Enrollments"
]

channel["Enrollments"] = (
    channel["Enrollments"]
    .fillna(0)
)

# MERGE COST
channel = channel.merge(
    cost,
    on="Channel",
    how="left"
)

# KPIs
channel["Conversion Rate"] = (
    channel["Enrollments"] /
    channel["Leads"] * 100
)

channel["Cost per Enrollment"] = (
    channel["Monthly_Cost"] /
    channel["Enrollments"]
)

channel["Cost per Enrollment"] = (
    channel["Cost per Enrollment"]
    .replace([float("inf")], 0)
)

# BEST/WORST
best = channel.sort_values(
    "Cost per Enrollment"
).iloc[0]

worst = channel.sort_values(
    "Cost per Enrollment",
    ascending=False
).iloc[0]

# ======================================================
# HEADER
# ======================================================
st.markdown(f"""
<div class="main-title">
Marketing Funnel Performance Dashboard
</div>

<div class="sub-title">
Referral is the most efficient channel while Instagram has the highest acquisition cost.
</div>
""", unsafe_allow_html=True)

# ======================================================
# KPI ROW
# ======================================================
k1, k2, k3, k4 = st.columns(4)

metrics = [
    ("Total Leads", f"{total_leads:,}"),
    ("Enrollments", f"{enrolled:,}"),
    ("Conversion Rate", f"{conversion:.1f}%"),
    ("Cost / Enrollment", f"₹{cpe:.0f}")
]

for col, (title, value) in zip(
    [k1, k2, k3, k4],
    metrics
):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ======================================================
# CHARTS
# ======================================================
c1, c2 = st.columns(2)

# ------------------------------------------------------
# ROI SCATTER
# ------------------------------------------------------
with c1:

    st.markdown(
        '<div class="chart-box">',
        unsafe_allow_html=True
    )

    fig1 = px.scatter(
        channel,
        x="Cost per Enrollment",
        y="Conversion Rate",
        size="Leads",
        color="Channel",
        text="Channel",
        template="simple_white"
    )

    fig1.update_traces(
        textposition="top center"
    )

    fig1.update_layout(
        title="Channel ROI Analysis",
        height=500
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    st.markdown(
        "**Insight:** Referral delivers strongest ROI."
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

# ------------------------------------------------------
# FUNNEL
# ------------------------------------------------------
with c2:

    st.markdown(
        '<div class="chart-box">',
        unsafe_allow_html=True
    )

    funnel_data = pd.DataFrame({
        "Stage": [
            "Leads",
            "Enrollments"
        ],
        "Count": [
            total_leads,
            enrolled
        ]
    })

    fig2 = px.funnel(
        funnel_data,
        x="Count",
        y="Stage",
        template="simple_white"
    )

    fig2.update_layout(
        title="Lead Funnel",
        height=500
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    st.markdown(
        "**Insight:** Significant drop-off before enrollment."
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

# ======================================================
# MONTHLY TREND
# ======================================================
st.markdown("<br>", unsafe_allow_html=True)

monthly = (
    df.groupby("Month")["Lead_ID"]
    .count()
    .reset_index()
)

fig3 = px.line(
    monthly,
    x="Month",
    y="Lead_ID",
    markers=True,
    template="simple_white"
)

fig3.update_layout(
    title="Monthly Lead Trend",
    height=450
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

# ======================================================
# CHANNEL TABLE
# ======================================================
st.subheader("Channel Performance")

st.dataframe(
    channel.sort_values(
        "Cost per Enrollment"
    ),
    use_container_width=True
)
