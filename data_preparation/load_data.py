import os
import pandas as pd

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def standardize_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
        .str.replace("/", "_", regex=False)
    )
    return df


def fix_primary_key(df):
    if "psuedocode" in df.columns:
        df = df.rename(columns={"psuedocode": "school_id"})
    if "pseudocode" in df.columns:
        df = df.rename(columns={"pseudocode": "school_id"})
    return df


def drop_fully_null_columns(df, dataset_name="dataset"):
    null_counts = df.isnull().sum()
    total_rows = len(df)
    fully_null_cols = null_counts[null_counts == total_rows].index.tolist()

    if fully_null_cols:
        print(f"\nDropping fully null columns from {dataset_name}:")
        for col in fully_null_cols:
            print(f" - {col}")
        df = df.drop(columns=fully_null_cols)

    return df


def safe_drop_grouping_columns(df):
    return df.drop(columns=["item_desc", "item_group", "item_id"], errors="ignore")


# =====================================================
# MASTER DATASET BUILDER (PER YEAR)
# =====================================================

def build_master_dataset(year):

    print("\n==============================")
    print(f"Processing Year: {year}")
    print("==============================")

    base_path = f"data/raw/{year}"

    profile_1 = pd.read_csv(os.path.join(base_path, "profile_1.csv"))
    profile_2 = pd.read_csv(os.path.join(base_path, "profile_2.csv"))
    facility = pd.read_csv(os.path.join(base_path, "facility.csv"))
    teacher = pd.read_csv(os.path.join(base_path, "teacher.csv"))
    enrolment_1 = pd.read_csv(os.path.join(base_path, "enrolment_1.csv"))
    enrolment_2 = pd.read_csv(os.path.join(base_path, "enrolment_2.csv"))

    datasets = [profile_1, profile_2, facility, teacher, enrolment_1, enrolment_2]
    datasets = [standardize_columns(df) for df in datasets]
    profile_1, profile_2, facility, teacher, enrolment_1, enrolment_2 = datasets

    profile_1 = fix_primary_key(profile_1)
    profile_2 = fix_primary_key(profile_2)
    facility = fix_primary_key(facility)
    teacher = fix_primary_key(teacher)
    enrolment_1 = fix_primary_key(enrolment_1)
    enrolment_2 = fix_primary_key(enrolment_2)

    # --- ENROLMENT 1 ---
    enrolment_1 = safe_drop_grouping_columns(enrolment_1)

    enrolment_1_agg = (
        enrolment_1.groupby("school_id")
        .sum(numeric_only=True)
        .reset_index()
    )

    boys_cols = [c for c in enrolment_1_agg.columns if c.endswith("_b")]
    girls_cols = [c for c in enrolment_1_agg.columns if c.endswith("_g")]

    enrolment_1_agg["total_boys"] = enrolment_1_agg[boys_cols].sum(axis=1)
    enrolment_1_agg["total_girls"] = enrolment_1_agg[girls_cols].sum(axis=1)
    enrolment_1_agg["total_enrolment"] = (
        enrolment_1_agg["total_boys"] + enrolment_1_agg["total_girls"]
    )

    # --- ENROLMENT 2 ---
    enrolment_2 = safe_drop_grouping_columns(enrolment_2)

    enrolment_2_agg = (
        enrolment_2.groupby("school_id")
        .sum(numeric_only=True)
        .reset_index()
    )

    boys_cols_2 = [c for c in enrolment_2_agg.columns if c.endswith("_b")]
    girls_cols_2 = [c for c in enrolment_2_agg.columns if c.endswith("_g")]

    enrolment_2_agg["total_boys_age"] = enrolment_2_agg[boys_cols_2].sum(axis=1)
    enrolment_2_agg["total_girls_age"] = enrolment_2_agg[girls_cols_2].sum(axis=1)
    enrolment_2_agg["total_enrolment_age"] = (
        enrolment_2_agg["total_boys_age"] + enrolment_2_agg["total_girls_age"]
    )

    # --- MERGE ---
    master_df = profile_1.merge(profile_2, on="school_id", how="left")
    master_df = master_df.merge(facility, on="school_id", how="left")
    master_df = master_df.merge(teacher, on="school_id", how="left")
    master_df = master_df.merge(enrolment_1_agg, on="school_id", how="left")
    master_df = master_df.merge(enrolment_2_agg, on="school_id", how="left")

    master_df = drop_fully_null_columns(master_df, f"master_{year}")

    os.makedirs("data/processed", exist_ok=True)
    master_df.to_csv(f"data/processed/master_{year}.csv", index=False)

    print(f"Master dataset for {year} saved.")
    print("Shape:", master_df.shape)


# =====================================================
# LONGITUDINAL BUILDER
# =====================================================

def build_longitudinal_dataset():

    print("\n==============================")
    print("Building Longitudinal Dataset")
    print("==============================")

    processed_path = "data/processed"

    master_files = sorted([
        f for f in os.listdir(processed_path)
        if f.startswith("master_") and f.endswith(".csv")
    ])

    all_years_data = []

    for file in master_files:
        year = file.replace("master_", "").replace(".csv", "")
        print(f"Loading {file}")

        df = pd.read_csv(os.path.join(processed_path, file), low_memory=False)
        df = df.assign(year=year)

        all_years_data.append(df)

    longitudinal_df = pd.concat(all_years_data, ignore_index=True).copy()

    print("Final Longitudinal Shape:", longitudinal_df.shape)

    longitudinal_df.to_csv(
        "data/processed/master_longitudinal.csv",
        index=False
    )

    print("Longitudinal dataset saved.")


# =====================================================
# CHURN ANALYSIS
# =====================================================

def analyze_school_churn():

    print("\n==============================")
    print("Analyzing School Churn")
    print("==============================")

    df = pd.read_csv(
        "data/processed/master_longitudinal.csv",
        low_memory=False
    )

    years = sorted(df["year"].unique())
    print("Years:", years)

    total_unique = df["school_id"].nunique()
    print("Total unique schools:", total_unique)

    print("\nSchools per year:")
    print(df.groupby("year")["school_id"].nunique())

    survival_df = (
        df.groupby("school_id")["year"]
        .nunique()
        .reset_index()
        .rename(columns={"year": "years_active"})
    )

    print("\nSurvival distribution:")
    print(survival_df["years_active"].value_counts().sort_index())


# =====================================================
# STABLE vs UNSTABLE COMPARISON
# =====================================================

def compare_stable_unstable():

    print("\n==============================")
    print("Stable vs Unstable Comparison")
    print("==============================")

    df = pd.read_csv(
        "data/processed/master_longitudinal.csv",
        low_memory=False
    )

    survival_df = (
        df.groupby("school_id")["year"]
        .nunique()
        .reset_index()
        .rename(columns={"year": "years_active"})
    )

    survival_df["stability"] = "mid"
    survival_df.loc[survival_df["years_active"] == 7, "stability"] = "stable"
    survival_df.loc[survival_df["years_active"] <= 3, "stability"] = "unstable"

    df = df.merge(
        survival_df[["school_id", "stability"]],
        on="school_id",
        how="left"
    )

    latest_year = df["year"].max()
    latest_df = df[df["year"] == latest_year]

    print("Latest year:", latest_year)

    print("\nAverage Total Enrolment:")
    print(latest_df.groupby("stability")["total_enrolment"].mean())

    if "rural_urban" in latest_df.columns:
        print("\nRural vs Urban:")
        print(pd.crosstab(
            latest_df["stability"],
            latest_df["rural_urban"]
        ))

def analyze_enrolment_growth():

    print("\n==============================")
    print("Enrolment Growth Analysis")
    print("==============================")

    df = pd.read_csv(
        "data/processed/master_longitudinal.csv",
        low_memory=False
    )

    # Compute survival years
    survival_df = (
        df.groupby("school_id")["year"]
        .nunique()
        .reset_index()
        .rename(columns={"year": "years_active"})
    )

    survival_df["stability"] = "mid"
    survival_df.loc[survival_df["years_active"] == 7, "stability"] = "stable"
    survival_df.loc[survival_df["years_active"] <= 3, "stability"] = "unstable"

    df = df.merge(
        survival_df[["school_id", "stability"]],
        on="school_id",
        how="left"
    )

    # Sort properly
    df = df.sort_values(["school_id", "year"])

    # Compute year-over-year growth
    df["prev_enrolment"] = df.groupby("school_id")["total_enrolment"].shift(1)

    df["enrolment_growth_pct"] = (
        (df["total_enrolment"] - df["prev_enrolment"])
        / df["prev_enrolment"]
    ) * 100

    # Remove first year rows (no previous year)
    growth_df = df.dropna(subset=["enrolment_growth_pct"])

    print("\nAverage Year-over-Year Growth (%):")
    print(
        growth_df.groupby("stability")["enrolment_growth_pct"]
        .mean()
        .sort_values(ascending=False)
    )

    print("\nMedian Year-over-Year Growth (%):")
    print(
        growth_df.groupby("stability")["enrolment_growth_pct"]
        .median()
        .sort_values(ascending=False)
    )

    return growth_df

df = pd.read_csv("data/processed/master_longitudinal.csv", low_memory=False)
pd.Series(sorted(df.columns)).to_csv("master_columns_list.csv", index=False)



# =====================================================
# MAIN EXECUTION CONTROL
# =====================================================

if __name__ == "__main__":

    print("\nSelect operation:")
    print("1 - Build all yearly master datasets")
    print("2 - Build longitudinal dataset")
    print("3 - Analyze churn")
    print("4 - Compare stable vs unstable")
    print("5 - Analyze enrolment growth")


    choice = input("Enter choice (1/2/3/4/5): ")

    if choice == "1":
        raw_path = "data/raw"
        years = sorted([
            f for f in os.listdir(raw_path)
            if os.path.isdir(os.path.join(raw_path, f))
        ])
        for year in years:
            build_master_dataset(year)

    elif choice == "2":
        build_longitudinal_dataset()

    elif choice == "3":
        analyze_school_churn()

    elif choice == "4":
        compare_stable_unstable()
    elif choice == "5":
        analyze_enrolment_growth()


    else:
        print("Invalid choice.")
