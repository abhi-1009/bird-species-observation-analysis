# Bird Species Observation Analysis
# ==================================
# Stage 1: Library installation, data upload, preprocessing, cleaning, and EDA.
# ==================================

# Import Libraries
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
CHART_DIR = "eda_outputs"
os.makedirs(CHART_DIR, exist_ok=True)

FOREST_FILE = "Bird_Monitoring_Data_FOREST.XLSX"
GRASSLAND_FILE = "Bird_Monitoring_Data_GRASSLAND.XLSX"

def load_habitat(path, label):
    """Load every sheet from one habitat's Excel workbook and tag each row with its habitat label."""
    sheets = pd.read_excel(path, sheet_name=None)
    for name, d in sheets.items():
        d["Habitat"], d["Source_Sheet"] = label, name
    return pd.concat(sheets.values(), ignore_index=True)
 
def show(title, series):
    """Print a labeled summary (used throughout EDA to keep output readable in the terminal)."""
    print(f"\n--- {title} ---")
    print(series)

def chart(kind, filename, title, **kwargs):
    """Build one chart (count/hist/box/barh) and save it into eda_outputs/."""
    plt.figure(figsize=kwargs.pop("figsize", (8, 5)))
    if kind == "count":
        sns.countplot(**kwargs)
    elif kind == "hist":
        sns.histplot(**kwargs)
    elif kind == "box":
        sns.boxplot(**kwargs)
    elif kind == "barh":
        kwargs["data"].plot(kind="barh")
        plt.gca().invert_yaxis()
    plt.title(title)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, filename))
    plt.close()

# ---------- STEP 1: Data upload ----------

df = pd.concat(
    [load_habitat(FOREST_FILE, "Forest"), load_habitat(GRASSLAND_FILE, "Grassland")],
    ignore_index=True,
)
print("Combined dataset shape:", df.shape)

# ---------- STEP 2: Preprocessing ----------

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Start_Hour"] = pd.to_datetime(df["Start_Time"].astype(str), errors="coerce").dt.hour

# Distance & Interval_Length are bucketed categories (e.g. "<= 50 Meters"), NOT numeric — keep as text. 
# Only these columns are genuinely numeric:
for col in ["Year", "Temperature", "Humidity", "Visit"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

text_cols = ["Common_Name", "Scientific_Name", "Sex", "Observer", "Sky", "Wind", "ID_Method",
             "Distance", "Interval_Length", "Disturbance", "AOU_Code", "Location_Type"]
for col in text_cols:
    df[col] = df[col].astype(str).str.strip().replace("nan", "Unknown")

# ---------- STEP 3: Cleaning ----------

show("Missing values (top 10)", df.isnull().sum().sort_values(ascending=False).head(10))
print("Note: Site_Name/NPSTaxonCode are Forest-only, Previously_Obs is Grassland-only — "
      "missing values there are expected, not a data quality issue.")

before = len(df)
df = df.drop_duplicates()
print(f"Dropped {before - len(df)} duplicate rows")
assert df["Temperature"].between(-50, 60).all(), "Temperature has implausible values"
assert 10000 <= len(df) <= 20000, "Row count outside expected range after cleaning"

df["Month"] = df["Date"].dt.month
df["Season"] = df["Month"].map(lambda m: "Winter" if m in (12, 1, 2) else
                                "Spring" if m in (3, 4, 5) else
                                "Summer" if m in (6, 7, 8) else
                                "Fall" if pd.notna(m) else "Unknown")

df.to_csv("bird_data_cleaned.csv", index=False)
print("Cleaned data saved to bird_data_cleaned.csv | shape:", df.shape)

# ---------- Load into MySQL ----------

from sqlalchemy import create_engine
from urllib.parse import quote_plus
from config import DB_PASSWORD
 
password = quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://root:{password}@localhost:3306/bird_observations")
df.to_sql("bird_observations", engine, if_exists="replace", index=False)
print("Data loaded into MySQL table 'bird_observations'")

# ---------- STEP 4: EDA — 7 sections ----------

print("\n========== 1. TEMPORAL ANALYSIS ==========")
show("Observations by Year", df["Year"].value_counts().sort_index())
show("Observations by Season", df["Season"].value_counts())
chart("count", "01_seasonal_trends.png", "Seasonal Trends by Habitat",
      data=df, x="Season", hue="Habitat", order=["Winter", "Spring", "Summer", "Fall"])
chart("count", "02_monthly_trend.png", "Observations by Month & Habitat",
      data=df, x="Month", hue="Habitat")
chart("count", "03_activity_by_hour.png", "Bird Activity by Start Hour",
      data=df, x="Start_Hour", hue="Habitat", figsize=(9, 5))

print("\n========== 2. SPATIAL ANALYSIS ==========")
show("Species Diversity by Location_Type", df.groupby("Location_Type")["Common_Name"].nunique())
chart("count", "04_habitat_counts.png", "Total Observations: Forest vs Grassland",
      data=df, x="Habitat", figsize=(6, 4))
plot_div = df.groupby("Plot_Name")["Common_Name"].nunique().sort_values(ascending=False).head(15)
show("Top 15 Plots by Species Diversity", plot_div)
chart("barh", "05_top_plots_diversity.png", "Top 15 Plots by Species Diversity",
      data=plot_div, figsize=(9, 6))

print("\n========== 3. SPECIES ANALYSIS ==========")
print("Total unique species:", df["Scientific_Name"].nunique())
show("Unique Species by Location_Type", df.groupby("Location_Type")["Scientific_Name"].nunique())
top_species = df["Common_Name"].value_counts().head(10)
show("Top 10 Species", top_species)
chart("barh", "06_top_species.png", "Top 10 Most Observed Species", data=top_species)
show("Activity Type (ID_Method)", df["ID_Method"].value_counts())
show("Interval Length Distribution", df["Interval_Length"].value_counts())
show("Sex Ratio", df["Sex"].value_counts())
chart("count", "07_sex_ratio.png", "Sex Ratio of Observed Birds",
      data=df, x="Sex", order=df["Sex"].value_counts().index, figsize=(6, 5))

print("\n========== 4. ENVIRONMENTAL CONDITIONS ==========")
show("Temperature Stats", df["Temperature"].describe())
chart("hist", "08_temperature_distribution.png", "Temperature Distribution",
      data=df["Temperature"].dropna(), bins=30, kde=True)
show("Humidity Stats", df["Humidity"].describe())
show("Sky Conditions", df["Sky"].value_counts())
show("Wind Conditions", df["Wind"].value_counts())
chart("box", "09_temperature_vs_distance.png", "Temperature vs Observation Distance",
      data=df, x="Distance", y="Temperature")
show("Disturbance Effect", df["Disturbance"].value_counts())
chart("count", "10_disturbance_effect.png", "Observations by Disturbance Level",
      data=df, y="Disturbance", order=df["Disturbance"].value_counts().index, figsize=(7, 5))

print("\n========== 5. DISTANCE AND BEHAVIOR ==========")
show("Distance Categories", df["Distance"].value_counts())
chart("count", "11_distance_counts.png", "Observations by Distance Category",
      data=df, x="Distance", order=df["Distance"].value_counts().index, figsize=(6, 4))
show("Flyover Observed", df["Flyover_Observed"].value_counts())
show("Top Flyover Species", df[df["Flyover_Observed"] == True]["Common_Name"].value_counts().head(10))

print("\n========== 6. OBSERVER TRENDS ==========")
observer_counts = df["Observer"].value_counts()
show("Observations per Observer", observer_counts)
chart("barh", "12_observer_counts.png", "Total Observations per Observer", data=observer_counts)
show("Visit Number vs Species Diversity", df.groupby("Visit")["Common_Name"].nunique())

print("\n========== 7. CONSERVATION INSIGHTS ==========")
show("PIF Watchlist Status", df["PIF_Watchlist_Status"].value_counts())
show("Regional Stewardship Status", df["Regional_Stewardship_Status"].value_counts())
show("Top 10 AOU Codes", df["AOU_Code"].value_counts().head(10))

print(f"\nEDA complete. 12 charts saved inside '{CHART_DIR}/'.")
