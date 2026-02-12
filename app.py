# HR Analytics Dashboard – Base Code with Reference Data Preparation
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
st.caption("B2B HR Analytics | Cleaned, Optimised & Insight‑Driven")

# -----------------------------
# 2. LOAD & CLEAN DATA (PORTED FROM REFERENCE CODE)
# -----------------------------
@st.cache_data
def load_and_clean_data():
    raw_file = "/Users/Josiah/Downloads/hr-dashboard/SGJobData.csv"
    output_file = "cleaned_SGJobData_exploded.csv"

    if not os.path.exists(raw_file):
        st.error("SGJobData.csv not found")
        st.stop()

    # Use cached cleaned file if exists
    if os.path.exists(output_file):
        return pd.read_csv(output_file)

    df = pd.read_csv(raw_file)

    # --- Drop metadata & irrelevant columns ---
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

    # --- Drop rows without essential business fields ---
    df = df.dropna(subset=[
        "categories",
        "positionLevels",
        "salary_type",
        "title",
        "postedCompany_name"
    ])

    # --- Salary & experience sanity filters (SG context) ---
    df = df[(df["average_salary"] >= 500) & (df["average_salary"] <= 50000)]
    df = df[df["minimumYearsExperience"] <= 40]

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
        
        # Remove text inside brackets
        title = re.sub(r"\(.*?\)", "", title)
        
        # Remove urgency words
        title = re.sub(r"\bURGENT\b|\burgent\b|\bUrgent\b", "", title)
        
        # Remove 'allowances'
        title = re.sub(r"\ballowances?\b", "", title, flags=re.IGNORECASE)
        
        # Remove salary mentions like $3000, $4,500, $5k
        title = re.sub(r"\$\s?\d+(?:,\d+)*(?:\.\d+)?k?", "", title, flags=re.IGNORECASE)
        
        # Remove leftover extra spaces
        title = re.sub(r"\s{2,}", " ", title)
        
        return title.strip()

    df["job_title"] = df["title"].apply(clean_title)

    # --- Standardise column names for base dashboard ---
    df = df.rename(columns={
        "employmentTypes": "employment_type",
        "minimumYearsExperience": "experience_years",
        "salary_minimum": "salary_min",
        "salary_maximum": "salary_max",
        "status_jobStatus": "job_status"
    })

    # --- Numeric cleanup ---
    df["salary_min"] = pd.to_numeric(df.get("salary_min"), errors="coerce")
    df["salary_max"] = pd.to_numeric(df.get("salary_max"), errors="coerce")
    df["experience_years"] = pd.to_numeric(df.get("experience_years"), errors="coerce")

    # --- Average salary ---
    df["avg_salary"] = df["average_salary"]

    # Save cleaned dataset
    df.to_csv(output_file, index=False)
    return df


df = load_and_clean_data()

# -----------------------------
# 3. GLOBAL MARKET STATS (OVERVIEW)
# -----------------------------
market_stats = df.groupby('category_list').agg({
    'average_salary': 'median',
    'metadata_totalNumberJobApplication': 'sum',
    'numberOfVacancies': 'sum'
}).reset_index()

# -----------------------------
# 4. SIDEBAR FILTERS (BASE CODE RETAINED)
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

# Apply filters
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
# 5. MARKET OVERVIEW (BASE LOGIC)
# -----------------------------
st.subheader("📌 Market Overview")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Active Jobs", len(filtered_df))
c2.metric("Industries", filtered_df["category_list"].nunique())
c3.metric("Avg Salary", f"${int(filtered_df['avg_salary'].mean()):,}")
c4.metric("Median Salary", f"${int(filtered_df['avg_salary'].median()):,}")
c5.metric("Avg Experience", f"{filtered_df['experience_years'].mean():.1f} yrs")

# -----------------------------
# 6. JOB MARKET DEMAND (TOP 10)
# -----------------------------
st.subheader("📈 Job Market Demand (Top Industries)")

industry_demand = (
    filtered_df.groupby("category_list")
    .size()
    .reset_index(name="job_count")
    .sort_values("job_count", ascending=False)
    .head(10)
)

industry_chart = (
    alt.Chart(industry_demand)
    .mark_bar()
    .encode(
        x=alt.X("job_count:Q", title="Number of Jobs"),
        y=alt.Y("category_list:N", sort='-x', title="Industry")
    )
)

st.altair_chart(industry_chart, use_container_width=True)

# -----------------------------
# 7. SALARY vs EXPERIENCE (SAMPLED)
# -----------------------------
st.subheader("💰 Salary vs Experience")

sample_df = filtered_df.sample(
    n=min(3000, len(filtered_df)),
    random_state=42
)

scatter = (
    alt.Chart(sample_df)
    .mark_circle(size=60, opacity=0.6)
    .encode(
        x=alt.X("experience_years:Q", title="Years of Experience"),
        y=alt.Y("avg_salary:Q", title="Average Salary"),
        color=alt.Color("category_list:N", legend=None),
        tooltip=["job_title", "category_list", "avg_salary", "experience_years"]
    )
)

st.altair_chart(scatter, use_container_width=True)

# -----------------------------
# 8. JOB SEEKER RESULTS TABLE
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
st.caption("Base code preserved | Reference STEP 1 data preparation integrated")
