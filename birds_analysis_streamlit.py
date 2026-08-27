"""
Bird Species Observation Analysis — Streamlit Dashboard
"""
# Import Libraries
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Bird Species Observation Analysis", layout="wide")

# ---------------------------------------------------------------------------
# DATA LOADING (cached so it only hits MySQL once per session)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    return pd.read_csv("bird_data_cleaned.csv")
df = load_data()

# ---------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------------------------
page = st.sidebar.radio("Navigate", ["Home", "Dashboard", "Insights & Recommendations"])

THEMES = {
    "Home": {"bg": "linear-gradient(180deg, #eef6f0 0%, #f7f4ea 100%)",
             "sidebar": "linear-gradient(180deg, #234d3f 0%, #1a3a30 100%)",
             "heading": "#1a3a30", "card_border": "#cfe3d6"},
    "Dashboard": {"bg": "linear-gradient(180deg, #eaf3f7 0%, #f4fafd 100%)",
                  "sidebar": "linear-gradient(180deg, #123a4d 0%, #0d2b38 100%)",
                  "heading": "#123a4d", "card_border": "#c7dfe9"},
    "Insights & Recommendations": {"bg": "linear-gradient(180deg, #f7f0e8 0%, #f3e9f2 100%)",
                                    "sidebar": "linear-gradient(180deg, #4d2340 0%, #331a2b 100%)",
                                    "heading": "#4d2340", "card_border": "#e3cfe0"},
}
t = THEMES[page]

st.markdown(f"""
<style>
.stApp {{ background: {t['bg']}; }}
section[data-testid="stSidebar"] {{ background: {t['sidebar']}; }}
section[data-testid="stSidebar"] * {{ color: #f2f2f2 !important; }}
h1, h2, h3 {{ color: {t['heading']}; }}
div[data-testid="stMetric"] {{
    background: #ffffffcc; border-radius: 12px; padding: 12px;
    border: 1px solid {t['card_border']};
}}
.icard {{
    background: #ffffffcc; border-radius: 10px; padding: 14px 16px;
    margin-bottom: 12px; border-left: 6px solid var(--c, {t['heading']});
    min-height: 110px;
}}
.icard h4 {{ margin: 0 0 6px 0; font-size: 15px; }}
.icard p {{ margin: 0; font-size: 13px; color: #333; line-height: 1.4; }}
</style>
""", unsafe_allow_html=True)


def cards(items, color, cols=2):
    """Render {icon, title, text} dicts as a grid of short cards instead of long bullet text."""
    c = st.columns(cols)
    for i, x in enumerate(items):
        with c[i % cols]:
            st.markdown(f'<div class="icard" style="--c:{color};"><h4>{x["icon"]} {x["title"]}</h4>'
                        f'<p>{x["text"]}</p></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PAGE 1: HOME — Problem Statement & Business Use Cases
# ---------------------------------------------------------------------------
if page == "Home":
    st.title("Bird Species Observation Analysis")
    st.subheader("Forest vs Grassland Habitats — Biodiversity & Conservation Insights")

    st.markdown("### Problem Statement")
    st.write(
        "The project aims to analyze the distribution and diversity of bird species in two "
        "distinct ecosystems: forests and grasslands. By examining bird species observations "
        "across these habitats, the goal is to understand how environmental factors, such as "
        "vegetation type, climate, and terrain, influence bird populations and their behavior. "
        "The study involves working on observational data of bird species present in both "
        "ecosystems, identifying patterns of habitat preference, and assessing the impact of "
        "these habitats on bird diversity. The findings can provide valuable insights into "
        "habitat conservation, biodiversity management, and the effects of environmental "
        "changes on avian communities."
    )

    st.markdown("### Business Use Cases")
    use_cases = {
        "Wildlife Conservation": "Inform decisions on protecting critical bird habitats and enhancing biodiversity conservation efforts.",
        "Land Management": "Optimize land use and habitat restoration strategies by understanding the preferences of different bird species.",
        "Eco-Tourism": "Identify bird-rich areas to develop bird-watching tourism, attracting eco-tourists and boosting local economies.",
        "Sustainable Agriculture": "Support the development of agricultural practices that minimize the impact on bird populations in grasslands and forests.",
        "Policy Support": "Provide data-driven insights to help environmental agencies create effective conservation policies and strategies for vulnerable bird species.",
        "Biodiversity Monitoring": "Track the health and diversity of avian populations, aiding in the monitoring of ecosystem stability.",
    }
    for i, (title, desc) in enumerate(use_cases.items(), start=1):
        st.markdown(f"**{i}. {title}** — {desc}")

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Observations", f"{len(df):,}")
    c2.metric("Unique Species", df["Scientific_Name"].nunique())
    c3.metric("Habitats Covered", df["Habitat"].nunique())
    c4.metric("Admin Units (Parks)", df["Admin_Unit_Code"].nunique())
    st.caption("Use the sidebar to explore the interactive dashboard or jump to insights and recommendations.")

# ---------------------------------------------------------------------------
# PAGE 2: DASHBOARD — filters + interactive Plotly visualizations
# ---------------------------------------------------------------------------
elif page == "Dashboard":
    st.title("Interactive Dashboard")

    # --- Sidebar filters ---
    st.sidebar.markdown("### Filters")
    habitats = st.sidebar.multiselect("Habitat", sorted(df["Habitat"].unique()), default=list(df["Habitat"].unique()))
    parks = st.sidebar.multiselect("Admin Unit (Park)", sorted(df["Admin_Unit_Code"].unique()), default=list(df["Admin_Unit_Code"].unique()))
    seasons = st.sidebar.multiselect("Season", sorted(df["Season"].unique()), default=list(df["Season"].unique()))
    species_options = sorted(df["Common_Name"].unique())
    species_filter = st.sidebar.multiselect("Species (optional — leave empty for all)", species_options)

    fdf = df[df["Habitat"].isin(habitats) & df["Admin_Unit_Code"].isin(parks) & df["Season"].isin(seasons)]
    if species_filter:
        fdf = fdf[fdf["Common_Name"].isin(species_filter)]

    if fdf.empty:
        st.warning("No data matches the current filters. Adjust your selection in the sidebar.")
        st.stop()

    tabs = st.tabs(["Temporal", "Spatial", "Species", "Environmental", "Distance & Behavior", "Observer", "Conservation"])

    # --- Temporal ---
    with tabs[0]:
        st.plotly_chart(px.histogram(fdf, x="Month", color="Habitat", barmode="group",
                                      title="Observations by Month and Habitat"), use_container_width=True)
        st.caption("Shows which months see the most bird activity, split by habitat — useful for planning seasonal fieldwork or eco-tourism windows.")

        st.plotly_chart(px.density_heatmap(fdf, x="Month", y="Start_Hour", title="Temporal Heatmap: Month vs Start Hour"),
                         use_container_width=True)
        st.caption("Combines month and time-of-day to reveal the highest-activity observation windows.")

    # --- Spatial ---
    with tabs[1]:
        park_counts = fdf.groupby("Admin_Unit_Code").size().reset_index(name="Observations")
        st.plotly_chart(px.bar(park_counts.sort_values("Observations", ascending=False), x="Admin_Unit_Code", y="Observations",
                                title="Total Observations by Admin Unit (Park)"), use_container_width=True)
        st.caption("Highlights which parks are the biggest activity hotspots — direct input for land management and eco-tourism planning.")

        plot_div = fdf.groupby("Plot_Name")["Common_Name"].nunique().sort_values(ascending=False).head(15).reset_index(name="Unique Species")
        st.plotly_chart(px.bar(plot_div, x="Plot_Name", y="Unique Species", title="Top 15 Plots by Species Diversity"),
                         use_container_width=True)
        st.caption("Note: the dataset identifies plots by code (Admin_Unit + Plot_Name) rather than GPS coordinates, so this substitutes for a geographic map — plots can be treated as location proxies for hotspot analysis.")

    # --- Species ---
    with tabs[2]:
        top_sp = fdf["Common_Name"].value_counts().head(10).reset_index()
        top_sp.columns = ["Common_Name", "Observations"]
        st.plotly_chart(px.bar(top_sp, x="Observations", y="Common_Name", orientation="h",
                                title="Top 10 Most Observed Species"), use_container_width=True)
        st.caption("The species driving the bulk of observations in the current filter selection.")

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(fdf, names="Sex", title="Sex Ratio"), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(fdf, names="ID_Method", title="Identification Method"), use_container_width=True)
        st.caption("Sex ratio and how birds were identified (song, call, or sighting) — relevant to observer methodology and species behavior patterns.")

    # --- Environmental ---
    with tabs[3]:
        st.plotly_chart(px.scatter(fdf, x="Temperature", y="Humidity", color="Habitat", opacity=0.5,
                                    title="Temperature vs Humidity by Habitat"), use_container_width=True)
        st.caption("Dynamic scatter of the two main environmental readings — look for clustering by habitat.")

        st.plotly_chart(px.box(fdf, x="Distance", y="Temperature", title="Temperature Distribution by Observation Distance"),
                         use_container_width=True)
        st.caption("Checks whether warmer conditions correlate with birds being observed closer or farther away.")

        st.plotly_chart(px.bar(fdf["Disturbance"].value_counts().reset_index(name="Count"), x="Disturbance", y="Count",
                                title="Observation Counts by Disturbance Level"), use_container_width=True)
        st.caption("How much human/environmental disturbance affected the ability to record sightings.")

    # --- Distance & Behavior ---
    with tabs[4]:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.bar(fdf["Distance"].value_counts().reset_index(name="Count"), x="Distance", y="Count",
                                    title="Observations by Distance Category"), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(fdf, names="Flyover_Observed", title="Flyover Observed"), use_container_width=True)
        st.caption("Distance bands show how close observers typically get; flyover ratio shows how often birds were seen in transit vs stationary.")

    # --- Observer ---
    with tabs[5]:
        obs_counts = fdf["Observer"].value_counts().reset_index(name="Observations")
        st.plotly_chart(px.bar(obs_counts, x="Observer", y="Observations", title="Observations per Observer"),
                         use_container_width=True)
        st.caption("A large gap between observers can signal observer bias — worth noting as a limitation.")

        visit_div = fdf.groupby("Visit")["Common_Name"].nunique().reset_index(name="Unique Species")
        st.plotly_chart(px.line(visit_div, x="Visit", y="Unique Species", markers=True,
                                 title="Species Diversity by Visit Number"), use_container_width=True)
        st.caption("Shows whether repeat visits to the same plots turn up more species, or diminishing returns.")

    # --- Conservation ---
    with tabs[6]:
        watchlist_species = fdf[fdf["PIF_Watchlist_Status"] == True]["Common_Name"].value_counts().head(10).reset_index()
        watchlist_species.columns = ["Common_Name", "Observations"]
        st.plotly_chart(px.bar(watchlist_species, x="Observations", y="Common_Name", orientation="h",
                                title="Top Watchlist Species by Observation Count"), use_container_width=True)
        st.caption("Species flagged by the Partners in Flight Watchlist — these are conservation priority candidates.")

        aou_counts = fdf["AOU_Code"].value_counts().head(10).reset_index(name="Count")
        st.plotly_chart(px.bar(aou_counts, x="AOU_Code", y="Count", title="Top 10 AOU Codes by Observation Count"),
                         use_container_width=True)
        st.caption("AOU codes are standardized species identifiers used in national conservation tracking.")

# ---------------------------------------------------------------------------
# PAGE 3: INSIGHTS & RECOMMENDATIONS — card layout (per coordinator feedback)
# ---------------------------------------------------------------------------
else:
    st.title("Insights & Recommendations")

    st.markdown("### 🔍 Key Insights")
    cards([
        {"icon": "🔥", "title": "Activity Hotspots",
         "text": "Certain parks/plots consistently show higher species diversity — priority zones for conservation and eco-tourism."},
        {"icon": "🌡️", "title": "Weather Effects",
         "text": "Temperature and humidity visibly shape observation distance and how reliably birds are spotted."},
        {"icon": "⚠️", "title": "At-Risk Species",
         "text": "Watchlist and Stewardship species are a small but conservation-critical subset needing focused monitoring."},
    ], color="#234d3f")

    st.markdown("### 💼 Business Insights")
    cards([
        {"icon": "🌳", "title": "Wildlife Conservation",
         "text": "Hotspot plots are the clearest candidates for protected-status review or expanded monitoring."},
        {"icon": "🦅", "title": "Eco-Tourism",
         "text": "Top-diversity plots plus peak activity windows can directly shape bird-watching tour schedules."},
        {"icon": "📋", "title": "Policy Support",
         "text": "Watchlist/stewardship breakdowns give agencies a ready, data-backed shortlist for policy attention."},
    ], color="#123a4d")

    st.markdown("### ⚠️ Limitations")
    cards([
        {"icon": "📅", "title": "Single Year Only",
         "text": "Data covers 2018, Spring/Summer only — no true multi-year or full-annual trend is possible."},
        {"icon": "🧩", "title": "Schema Differences",
         "text": "Forest and Grassland files each include a few fields the other doesn't (Site_Name vs. Previously_Obs)."},
        {"icon": "🗺️", "title": "No GPS Data",
         "text": "Spatial analysis relies on plot/admin-unit codes rather than true latitude-longitude coordinates."},
        {"icon": "👥", "title": "Observer Bias",
         "text": "Only 3 observers contributed all data — individual habits may influence patterns as much as bird behavior."},
    ], color="#8a6d00")

    st.markdown("### ✅ Recommendations")
    cards([
        {"icon": "📈", "title": "Expand Coverage",
         "text": "Collect multi-year, all-season data to support genuine year-over-year trend analysis."},
        {"icon": "🛰️", "title": "Add GPS Coordinates",
         "text": "Enable true geographic hotspot mapping in future data collection."},
        {"icon": "👥", "title": "Grow Observer Pool",
         "text": "Add more observers and standardize protocols to reduce observer-bias risk."},
        {"icon": "🎯", "title": "Prioritize Resources",
         "text": "Focus protection efforts on the top watchlist species and highest-diversity plots identified here."},
    ], color="#4d2340")