import streamlit as st
import pandas as pd
import json

# Set Page Layout to Wide
st.set_page_config(layout="wide", page_title="ERCOT Large Loads")

# Load Data
# Load Data
# Removed cache to ensure fresh data load
def load_data():
    with open('webapp/public/data.json', 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()

# Logic: Calculate Estimated Annual MWh
# Formula: MW * 8760 hours * Load Factor
def get_load_factor(facility_type):
    t = facility_type.lower()
    if 'crypto' in t or 'data' in t:
        return 0.90
    if 'steel' in t or 'manufact' in t or 'refin' in t or 'chem' in t or 'lng' in t or 'industrial' in t:
        return 0.80
    if 'health' in t or 'hosp' in t or 'prison' in t:
        return 0.65
    # Retail, Education, Enterprise are peaky but lower utilization
    return 0.40

df['Load Factor'] = df['type'].apply(get_load_factor)
df['Est. Annual MWh'] = df['mw'] * 8760 * df['Load Factor']
df['Est. Annual MWh'] = df['Est. Annual MWh'].astype(int)

# Sort by Peak Load Descending (User requested Top 500)
df = df.sort_values(by='mw', ascending=False).reset_index(drop=True)

# Title
st.title("⚡ ERCOT Large Load Analytics")

# Sidebar Filters
st.sidebar.header("Filters")

# Reset Button
def reset_filters():
    st.session_state.filter_hub = []
    st.session_state.filter_type = []
    st.session_state.filter_county = []
    st.session_state.filter_city = []
    st.session_state.filter_status = ["Operational", "Development / Queue", "Aggregate Estimate"]
    st.session_state.filter_mw = (int(df['mw'].min()), int(df['mw'].max()))
    st.session_state.filter_search = ''

st.sidebar.button("Reset Filters", on_click=reset_filters, type="primary")

# Hub Filter
hubs = sorted(list(df['hub'].unique()))
selected_hub = st.sidebar.multiselect("ERCOT Hub", hubs, key="filter_hub")

# Type Filter
types = sorted(list(df['type'].unique()))
selected_type = st.sidebar.multiselect("Facility Type", types, key="filter_type")

# County Filter
counties = sorted(list(df['county'].unique()))
selected_counties = st.sidebar.multiselect("County", counties, key="filter_county")

# City Filter
if selected_counties:
    cities = sorted(list(df[df['county'].isin(selected_counties)]['city'].unique()))
else:
    cities = sorted(list(df['city'].unique()))

selected_cities = st.sidebar.multiselect("City", cities, key="filter_city")

# Status Filter
statuses = sorted(list(df['status'].unique()))
selected_status = st.sidebar.multiselect("Status", statuses, default=["Operational", "Development / Queue", "Aggregate Estimate"], key="filter_status")

# MW Range
min_mw, max_mw = int(df['mw'].min()), int(df['mw'].max())
selected_mw = st.sidebar.slider("Peak Load (MW)", min_mw, max_mw, (min_mw, max_mw), key="filter_mw")

# Search
search_term = st.sidebar.text_input("Search Name/Notes/Source", key="filter_search")

# Apply Filters
filtered_df = df.copy()
if selected_hub:
    filtered_df = filtered_df[filtered_df['hub'].isin(selected_hub)]
if selected_type:
    filtered_df = filtered_df[filtered_df['type'].isin(selected_type)]
if selected_counties:
    filtered_df = filtered_df[filtered_df['county'].isin(selected_counties)]
if selected_cities:
    filtered_df = filtered_df[filtered_df['city'].isin(selected_cities)]
if selected_status:
    filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]

filtered_df = filtered_df[
    (filtered_df['mw'] >= selected_mw[0]) & 
    (filtered_df['mw'] <= selected_mw[1])
]

if search_term:
    search_term = search_term.lower()
    filtered_df = filtered_df[
        filtered_df['name'].str.lower().str.contains(search_term) |
        filtered_df['notes'].str.lower().str.contains(search_term) |
        filtered_df['source'].str.lower().str.contains(search_term)
    ]

# --- Key Metrics (Refined) ---
st.markdown("###") # Spacer

# Split into Active vs Future
operational_df = filtered_df[filtered_df['status'] == 'Operational']
dev_df = filtered_df[filtered_df['status'] != 'Operational']

m1, m2, m3, m4 = st.columns(4)

# Col 1: Active Facilities
m1.metric("Active Facilities", f"{len(operational_df):,}", help="Count of facilities currently marked as 'Operational'")

# Col 2: Active Peak Load
m2.metric("Active Peak Load (MW)", f"{int(operational_df['mw'].sum()):,}", help="Sum of Peak MW for Operational facilities")

# Col 3: Future / Queue Load
m3.metric("Future / Queue Load (MW)", f"{int(dev_df['mw'].sum()):,}", help="Sum of Peak MW for Development, Queue, or Estimate facilities")

# Col 4: Total Pipeline Count
m4.metric("Total Pipeline Count", f"{len(filtered_df):,}", help="Total including Operational and Development")

st.markdown("---")

# Main Data Table
st.subheader(f"Facility List ({len(filtered_df)})")

# Reorder and Rename Columns for Display
display_df = filtered_df[[
    'name', 'type', 'hub', 'city', 'county', 'mw', 'Est. Annual MWh', 'status', 'source', 'notes'
]].rename(columns={
    'name': 'Name',
    'type': 'Type',
    'hub': 'Hub',
    'city': 'City',
    'county': 'County',
    'mw': 'Peak MW',
    'status': 'Status',
    'source': 'Data Source',
    'notes': 'Notes'
})

# Format MWh as string with commas to avoid Streamlit/sprintf issues
display_df['Est. Annual MWh'] = display_df['Est. Annual MWh'].apply(lambda x: f"{x:,.0f} MWh")

# Display Interactive Table
st.dataframe(
    display_df,
    use_container_width=True,
    column_config={
        "Peak MW": st.column_config.NumberColumn(format="%.0f MW"),
        "Status": st.column_config.TextColumn(
            "Status",
            help="Operational or Development/Queue",
            width="medium"
        ),
    },
    height=500
)

# Hub Analysis Section
st.markdown("---")
st.subheader("📊 Hub Context")

# Estimated Peak Loads (Based on 2023/2024 ERCOT Zonal Data)
HUB_PEAKS = {
    'North': 32000,   # DFW + North Central (~38% of system)
    'Houston': 22500, # Coast Zone (~26% of system)
    'South': 17000,   # South + South Central (~20% of system)
    'West': 10000     # West + Far West (~12% of system)
}

# Group filtered data by Hub for dynamic analysis
filtered_hub_mws = filtered_df.groupby('hub')['mw'].sum().to_dict()

# 1. Total ERCOT System (Dynamic based on filter)
total_filtered_mw = filtered_df['mw'].sum()
ERCOT_PEAK = 85500 # Aug 2023 Record

cols = st.columns(5)
with cols[0]:
    st.metric(
        label="Total ERCOT System",
        value=f"{ERCOT_PEAK:,.0f} MW",
        delta=f"{total_filtered_mw:,.0f} MW (Filtered) ({(total_filtered_mw/ERCOT_PEAK):.1%})"
    )

# 2. Hub Specific Metrics
st.markdown("##### Zonal Breakdown")

for idx, hub_name in enumerate(HUB_PEAKS.keys()):
    est_peak = HUB_PEAKS[hub_name]
    
    # Get MW for this hub from filtered data, default to 0 if none
    list_mw = filtered_hub_mws.get(hub_name, 0)
    coverage = list_mw / est_peak
    
    # Map Hub to column index (1-4)
    with cols[idx + 1]:
        st.metric(
            label=f"{hub_name} Hub Peak (Est.)",
            value=f"{est_peak:,.0f} MW",
            delta=f"{list_mw:,.0f} MW (Filtered List) ({coverage:.1%})"
        )
        st.progress(
            min(1.0, coverage), 
            text=f"Captured Load: {coverage:.0%}"
        )
