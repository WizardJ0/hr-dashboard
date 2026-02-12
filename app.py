# HR Analytics Dashboard – Fully Stable Version
# Run with: streamlit run app.py

import streamlit as st
import pandas as pd
import altair as alt
import json
import re
import os

# -----------------------------
# 1. PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="HR Market Intelligence Dashboard",
    layout="wide"
)

st.title("📊 HR Market Intelligence & Hiring Dashboard")
st.caption("Cleaned • Stable • Executive-Ready")

# -----------------------------
# 2. LOAD & CLEAN DATA
# -----------------------------
@st.cache_data
def load_and_clean_data():

    raw_file = "/Users/Josiah/Downloads/hr-dashboard/SGJobData.csv"

    if not os.path.exists(raw_file):
        st.error("SGJobData.csv not found")
        st.stop()

    df = pd.read_csv(raw_file)

    # --- Drop unnecessary metadata ---
    DROP_COLS = [
        "metadata_expiryDate",
        "metadata_isPostedOnBehalf",
        "metadata_jobPostId",
        "metadata_newPostingDate",
        "metadata_originalPostingDate",
        "metadata_repostCount",
        "metadata_totalNumberOfView",
        "status_id",
        "occupationId"
    ]
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns], errors="ignore")

    # --- Drop rows missing critical business fields ---
    df = df.dropna(subset=[
        "categories",
        "positionLevels",
        "salary_type",
        "title",
        "postedCompany_name"
    ])

    # --- Salary sanity filter ---
    df["average_salary"] = pd.to_numeric(df["average_salary"], errors="coerce")
    df = df[(df["average_salary"] >= 500) & (df["average_salary"] <= 50000)]

    # --- Extract & explode categories ---
    def extract_categories(cat_str):
        try:
            cats = json.loads(cat_str.replace("''", "'"))
            return [c["category"] for c in cats]
        except:
            return []

    df["category_list"] = df["categories"].apply(extract_categories)
    df = df.explode("category_list")

    # --- Clean job titles ---
    def clean_title(title):
        if pd.isna(title):
            return title
        
        title = re.sub(r"\(.*?\)", "", title)
        title = re.sub(r"\bURGENT\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\ballowances?\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\$\s?\d+(?:,\d+)*(?:\.\d+)?k?", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s{2,}", " ", title)
        return title.strip()

    df["job_title"] = df["title"].apply(clean_title)

    # --- Rename columns ---
    df = df.rename(columns={
        "employmentTypes": "employment_type",
        "minimumYearsExperience": "experience_years",
        "salary_minimum": "salary_min",
        "salary_maximum": "salary_max",
        "status_jobStatus": "job_status"
    })

    # --- Clean experience safely ---
    if "experience_years" in df.columns:
        df["experience_years"] = (
            df["experience_years"]
            .astype(str)
            .str.extract(r"(\d+)")
        )
        df["experience_years"] = pd.to_numeric(df["experience_years"], errors="coerce")

    # --- Convert numeric fields safely ---
    for col in [
        "salary_min",
        "salary_max",
        "metadata_totalNumberJobApplication",
        "numberOfVacancies"
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["avg_salary"] = df["average_salary"]

    return df


df = load_and_clean_data()

# -----------------------------
# 3. GLOBAL MARKET STATS
# -----------------------------
AGG_COLS = {"average_salary": "median"}

if "metadata_totalNumberJobApplication" in df.columns:
    AGG_COLS["metadata_totalNumberJobApplication"] = "sum"

if "numberOfVacancies" in df.columns:
    AGG_COLS["numberOfVacancies"] = "sum"

market_stats = (
    df.groupby("category_list")
    .agg(AGG_COLS)
    .reset_index()
)

if "metadata_totalNumberJobApplication" in market_stats.columns and \
   "numberOfVacancies" in market_stats.columns:

    market_stats["competition_index"] = (
        market_stats["metadata_totalNumberJobApplication"] /
        market_stats["numberOfVacancies"]
    )

# -----------------------------
# 4. SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("🔍 Job Filters")

industry_filter = st.sidebar.multiselect(
    "Industry",
    sorted(df["category_list"].dropna().unique())
)

employment_filter = st.sidebar.multiselect(
    "Employment Type",
    sorted(df["employment_type"].dropna().unique())
)

job_status_filter = st.sidebar.multiselect(
    "Job Status",
    sorted(df["job_status"].dropna().unique())
)

salary_range = st.sidebar.slider(
    "Average Salary Range",
    int(df["avg_salary"].min()),
    int(df["avg_salary"].max()),
    (
        int(df["avg_salary"].min()),
        int(df["avg_salary"].max())
    )
)

filtered_df = df.copy()

if industry_filter:
    filtered_df = filtered_df[filtered_df["category_list"].isin(industry_filter)]

if employment_filter:
    filtered_df = filtered_df[filtered_df["employment_type"].isin(employment_filter)]

if job_status_filter:
    filtered_df = filtered_df[filtered_df["job_status"].isin(job_status_filter)]

filtered_df = filtered_df[
    (filtered_df["avg_salary"] >= salary_range[0]) &
    (filtered_df["avg_salary"] <= salary_range[1])
]

# -----------------------------
# 5. MARKET OVERVIEW
# -----------------------------
st.subheader("📌 Market Overview")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Active Jobs", len(filtered_df))
c2.metric("Industries", filtered_df["category_list"].nunique())
c3.metric("Avg Salary", f"${int(filtered_df['avg_salary'].mean()):,}")
c4.metric("Median Salary", f"${int(filtered_df['avg_salary'].median()):,}")
c5.metric("Avg Experience", f"{filtered_df['experience_years'].mean():.1f} yrs")

# -----------------------------
# 6. TOP INDUSTRIES
# -----------------------------
st.subheader("📈 Top Industries by Job Demand")

industry_demand = (
    filtered_df.groupby("category_list")
    .size()
    .reset_index(name="job_count")
    .sort_values("job_count", ascending=False)
    .head(10)
)

st.altair_chart(
    alt.Chart(industry_demand)
    .mark_bar()
    .encode(
        x="job_count:Q",
        y=alt.Y("category_list:N", sort='-x')
    ),
    use_container_width=True
)




# -----------------------------
# 7. SALARY vs EXPERIENCE
# -----------------------------
st.subheader("💰 Salary vs Experience")

analysis_df = filtered_df[
    (filtered_df["experience_years"].notna()) &
    (filtered_df["avg_salary"].notna())
][["experience_years", "avg_salary"]]

# HARD LIMIT DATA SIZE (critical for 1.7M rows)
if len(analysis_df) > 5000:
    analysis_df = analysis_df.sample(5000, random_state=42)

if len(analysis_df) > 10:

    covariance = analysis_df["experience_years"].cov(analysis_df["avg_salary"])
    correlation = analysis_df["experience_years"].corr(analysis_df["avg_salary"])

    chart = (
        alt.Chart(analysis_df)
        .mark_circle(size=40, opacity=0.4)
        .encode(
            x=alt.X("experience_years:Q", title="Years of Experience"),
            y=alt.Y("avg_salary:Q", title="Average Salary"),
            tooltip=["experience_years", "avg_salary"]
        )
        .properties(height=450)
    )

    regression = chart.transform_regression(
        "experience_years",
        "avg_salary"
    ).mark_line(color="red")

    st.altair_chart(chart + regression, use_container_width=True)

    st.markdown(
        f"""
        **Covariance:** {covariance:,.2f}  
        **Correlation (Pearson r):** {correlation:.3f}
        """
    )

else:
    st.warning("Not enough data to compute correlation.")


# -----------------------------
# 8. JOB TABLE
# -----------------------------
st.subheader("🧑‍💼 Available Jobs")

DISPLAY_COLS = [
    "job_title",
    "category_list",
    "employment_type",
    "job_status",
    "experience_years",
    "avg_salary"
]

st.dataframe(
    filtered_df[DISPLAY_COLS].head(1000).reset_index(drop=True),
    use_container_width=True,
    height=420
)

# -----------------------------
# 9. FOOTER
# -----------------------------
st.caption("Stable Build: Correlation • Regression • Cleaned Experience • Executive Layout")
