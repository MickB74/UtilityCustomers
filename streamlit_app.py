import streamlit as st
import pandas as pd
import json
import requests
import datetime
import pytz

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

# Navigation
view = st.sidebar.radio("Navigation", ["Dashboard", "Generation Projects", "Market Resources"])

if view == "Dashboard":
    # --- Sidebar Filters ---
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

    # Helper: Get valid options based on other filters
    def get_valid_options(target_col, filters):
        temp_df = df.copy()
        # Apply all filters EXCEPT the one we are generating options for
        for col, values in filters.items():
            if col != target_col and values:
                 temp_df = temp_df[temp_df[col].isin(values)]
        return sorted(list(temp_df[target_col].unique()))

    # Capture Current Selections from Session State
    current_selection = {
        'hub': st.session_state.get('filter_hub', []),
        'type': st.session_state.get('filter_type', []),
        'county': st.session_state.get('filter_county', []),
        'city': st.session_state.get('filter_city', []),
        'status': st.session_state.get('filter_status', [])
    }

    # Hub Filter
    valid_hubs = get_valid_options('hub', current_selection)
    selected_hub = st.sidebar.multiselect("ERCOT Hub", valid_hubs, key="filter_hub")

    # Type Filter
    valid_types = get_valid_options('type', current_selection)
    selected_type = st.sidebar.multiselect("Facility Type", valid_types, key="filter_type")

    # County Filter
    valid_counties = get_valid_options('county', current_selection)
    selected_counties = st.sidebar.multiselect("County", valid_counties, key="filter_county")

    # City Filter
    valid_cities = get_valid_options('city', current_selection)
    selected_cities = st.sidebar.multiselect("City", valid_cities, key="filter_city")

    # Status Filter
    valid_statuses = get_valid_options('status', current_selection)
    if 'filter_status' not in st.session_state:
        st.session_state.filter_status = ["Operational", "Development / Queue", "Aggregate Estimate"]
    
    selected_status = st.sidebar.multiselect("Status", valid_statuses, key="filter_status")

    # MW Range
    min_mw, max_mw = int(df['mw'].min()), int(df['mw'].max())
    selected_mw = st.sidebar.slider("Peak Load (MW)", min_mw, max_mw, (min_mw, max_mw), key="filter_mw")

    # Search
    search_term = st.sidebar.text_input("Search Name/Notes/Source", key="filter_search")

    # --- Apply Filters ---
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

    # --- Dashboard Content ---
    st.markdown("###") # Spacer

    # Helper for status classification
    def is_operational(status):
        return status in ['Operational', 'Aggregate Estimate']

    # Split into Active vs Future
    operational_df = filtered_df[filtered_df['status'].apply(is_operational)]
    dev_df = filtered_df[~filtered_df['status'].apply(is_operational)]

    m1, m2, m3, m4 = st.columns(4)

    # Col 1: Active Facilities
    m1.metric("Active Facilities", f"{len(operational_df):,}", help="Count of Operational + Aggregate Estimate facilities")

    # Col 2: Active Peak Load
    m2.metric("Active Peak Load (MW)", f"{int(operational_df['mw'].sum()):,}", help="Sum of Peak MW for Operational + Aggregate Estimate")

    # Col 3: Future / Queue Load
    m3.metric("Future / Queue Load (MW)", f"{int(dev_df['mw'].sum()):,}", help="Sum of Peak MW for Development / Queue")

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

    # Start index at 1
    display_df.index = range(1, len(display_df) + 1)

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

    # Group data by Hub for STATIC context analysis (Total System)
    # We use 'df' (unfiltered) instead of 'filtered_df' so these totals don't change
    context_op_df = df[df['status'].apply(is_operational)]
    context_dev_df = df[~df['status'].apply(is_operational)]

    total_hub_active = context_op_df.groupby('hub')['mw'].sum().to_dict()
    total_hub_queue = context_dev_df.groupby('hub')['mw'].sum().to_dict()

    # 1. Total ERCOT System (Static)
    total_active_mw = context_op_df['mw'].sum()
    total_queue_mw = context_dev_df['mw'].sum()
    ERCOT_PEAK = 85500 # Aug 2023 Record

    cols = st.columns(5)
    with cols[0]:
        st.metric(
            label="Total ERCOT System",
            value=f"{ERCOT_PEAK:,.0f} MW",
            delta=f"{total_active_mw:,.0f} MW (Active) ({(total_active_mw/ERCOT_PEAK):.1%})"
        )
        st.metric(
            label="Total Queue / Planned",
            value=f"{total_queue_mw:,.0f} MW",
            delta="Future Load",
            delta_color="off"
        )

    # 2. Hub Specific Metrics
    st.markdown("##### Zonal Breakdown")

    for idx, hub_name in enumerate(HUB_PEAKS.keys()):
        est_peak = HUB_PEAKS[hub_name]
        
        # Get Total MW for this hub (Static)
        active_mw = total_hub_active.get(hub_name, 0)
        queue_mw = total_hub_queue.get(hub_name, 0)
        
        coverage = active_mw / est_peak
        
        # Map Hub to column index (1-4)
        with cols[idx + 1]:
            st.metric(
                label=f"{hub_name} Peak (Est.)",
                value=f"{est_peak:,.0f} MW",
                delta=f"{active_mw:,.0f} MW (Active) ({coverage:.1%})"
            )
            st.metric(
                label=f"{hub_name} Queue",
                value=f"{queue_mw:,.0f} MW",
                delta="Future / Planned",
                delta_color="off"
            )
            st.progress(
                min(1.0, coverage), 
                text=f"Active Load: {coverage:.0%}"
            )

elif view == "Generation Projects":
    # Load Generation Data
    @st.cache_data
    def load_gen_data():
        with open('webapp/public/generation_data.json', 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)

    gen_df = load_gen_data()
    
    # --- Sidebar Filters for Generation ---
    st.sidebar.header("Generation Filters")
    
    # Reset Button for Gen
    if st.sidebar.button("Reset Gen Filters"):
        st.session_state.gen_tech = []
        st.session_state.gen_status = []
        st.session_state.gen_county = []
        st.session_state.gen_hub = []
        st.session_state.gen_search = ""
    
    # Tech Filter
    tech_opts = sorted(gen_df['technology'].unique())
    sel_tech = st.sidebar.multiselect("Technology", tech_opts, key="gen_tech")
    
    # Status Filter
    status_opts = sorted(gen_df['status'].unique())
    sel_status = st.sidebar.multiselect("Status", status_opts, key="gen_status")
    
    # Hub Filter
    hub_opts = sorted(gen_df['hub'].unique()) if 'hub' in gen_df.columns else []
    sel_hub = st.sidebar.multiselect("ERCOT Hub", hub_opts, key="gen_hub")

    # County Filter
    county_opts = sorted(gen_df['county'].unique())
    sel_county = st.sidebar.multiselect("County", county_opts, key="gen_county")

    # Search Box
    gen_search = st.sidebar.text_input("Search Project/Dev/Loc", key="gen_search")
    
    # Apply Filters
    filtered_gen = gen_df.copy()
    if sel_tech:
        filtered_gen = filtered_gen[filtered_gen['technology'].isin(sel_tech)]
    if sel_status:
        filtered_gen = filtered_gen[filtered_gen['status'].isin(sel_status)]
    if sel_hub:
        filtered_gen = filtered_gen[filtered_gen['hub'].isin(sel_hub)]
    if sel_county:
        filtered_gen = filtered_gen[filtered_gen['county'].isin(sel_county)]
    
    if gen_search:
        s = gen_search.lower()
        filtered_gen = filtered_gen[
            filtered_gen['project_name'].str.lower().str.contains(s) |
            filtered_gen['developer'].str.lower().str.contains(s) |
            filtered_gen['county'].str.lower().str.contains(s) |
            filtered_gen['city'].str.lower().str.contains(s)
        ]
        
    # --- Dashboard Content ---
    st.header("⚡ Generation Projects")
    
    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    
    total_mw = filtered_gen['capacity_mw'].sum()
    op_mw = filtered_gen[filtered_gen['status'] == 'Operational']['capacity_mw'].sum()
    queue_mw = filtered_gen[filtered_gen['status'] != 'Operational']['capacity_mw'].sum()
    count = len(filtered_gen)
    
    m1.metric("Total Capacity", f"{total_mw:,.0f} MW")
    m2.metric("Operational", f"{op_mw:,.0f} MW")
    m3.metric("Queue / Planned", f"{queue_mw:,.0f} MW")
    m4.metric("Project Count", f"{count}")
    
    st.markdown("---")
    
    # Main Table
    st.subheader(f"Project List ({count})")
    
    # Display Config
    st.dataframe(
        filtered_gen[['project_name', 'technology', 'capacity_mw', 'hub', 'city', 'county', 'status', 'cod_year', 'developer', 'notes']],
        use_container_width=True,
        column_config={
            "capacity_mw": st.column_config.NumberColumn("Capacity (MW)", format="%.0f MW"),
            "cod_year": st.column_config.NumberColumn("COD Year", format="%d"),
            "project_name": "Project Name",
            "technology": "Technology",
            "hub": "Hub",
            "city": "City",
            "county": "County",
            "status": "Status",
            "developer": "Developer",
            "notes": "Notes"
        },
        height=600,
        hide_index=True
    )

    # Generation Mix Section (Totals on Bottom)
    st.markdown("---")
    st.subheader("📊 Generation Context")
    
    # 1. Hub Breakdown (Requested focus for Renewables)
    st.markdown("##### Capacity by ERCOT Hub")
    if not filtered_gen.empty:
        hub_stats = filtered_gen.groupby('hub')['capacity_mw'].sum().sort_values(ascending=False)
        # Use a dynamic number of columns based on Hub count (usually 5-6)
        h_cols = st.columns(min(len(hub_stats), 6))
        
        for idx, (hub, total_mw) in enumerate(hub_stats.items()):
            if idx < len(h_cols):
                # Breakdown op/queue for this hub
                h_op = filtered_gen[(filtered_gen['hub'] == hub) & (filtered_gen['status'] == 'Operational')]['capacity_mw'].sum()
                h_queue = filtered_gen[(filtered_gen['hub'] == hub) & (filtered_gen['status'] != 'Operational')]['capacity_mw'].sum()
                
                with h_cols[idx]:
                    st.metric(
                        label=f"{hub}",
                        value=f"{total_mw:,.0f} MW",
                        delta=f"{h_op:,.0f} MW (Op) / {h_queue:,.0f} MW (Q)",
                        delta_color="off"
                    )

    # 2. Technology Mix
    st.markdown("##### Technology Breakdown")
    tech_stats = filtered_gen.groupby(['technology', 'status'])['capacity_mw'].sum().unstack(fill_value=0)
    for col in ['Operational', 'Queue']:
        if col not in tech_stats.columns:
            tech_stats[col] = 0
            
    active_techs = sorted(filtered_gen['technology'].unique())
    if active_techs:
        cols = st.columns(len(active_techs))
        for idx, tech in enumerate(active_techs):
            t_op = filtered_gen[(filtered_gen['technology'] == tech) & (filtered_gen['status'] == 'Operational')]['capacity_mw'].sum()
            t_queue = filtered_gen[(filtered_gen['technology'] == tech) & (filtered_gen['status'] != 'Operational')]['capacity_mw'].sum()
            t_total = t_op + t_queue
            
            with cols[idx]:
                st.metric(
                    label=f"{tech}",
                    value=f"{t_total:,.0f} MW",
                    delta=f"{t_op:,.0f} MW (Op) / {t_queue:,.0f} MW (Q)",
                    delta_color="off"
                )
    
    # 3. Top Counties
    st.markdown("##### Top 5 Counties")
    if not filtered_gen.empty:
        county_stats = filtered_gen.groupby('county')['capacity_mw'].sum().sort_values(ascending=False).head(5)
        c_cols = st.columns(5)
        for idx, (county, total_mw) in enumerate(county_stats.items()):
            # Breakdown op/queue for this county
            c_op = filtered_gen[(filtered_gen['county'] == county) & (filtered_gen['status'] == 'Operational')]['capacity_mw'].sum()
            c_queue = filtered_gen[(filtered_gen['county'] == county) & (filtered_gen['status'] != 'Operational')]['capacity_mw'].sum()
            
            with c_cols[idx]:
                st.metric(
                    label=f"{county} County",
                    value=f"{total_mw:,.0f} MW",
                    delta=f"{c_op:,.0f} MW (Op) / {c_queue:,.0f} MW (Q)",
                    delta_color="off"
                )
    
    # 4. Top Cities
    st.markdown("##### Top 5 Cities")
    if not filtered_gen.empty:
        city_stats = filtered_gen.groupby('city')['capacity_mw'].sum().sort_values(ascending=False).head(5)
        city_cols = st.columns(5)
        for idx, (city, total_mw) in enumerate(city_stats.items()):
            # Breakdown op/queue for this city
            c_op = filtered_gen[(filtered_gen['city'] == city) & (filtered_gen['status'] == 'Operational')]['capacity_mw'].sum()
            c_queue = filtered_gen[(filtered_gen['city'] == city) & (filtered_gen['status'] != 'Operational')]['capacity_mw'].sum()
            
            with city_cols[idx]:
                st.metric(
                    label=f"{city}",
                    value=f"{total_mw:,.0f} MW",
                    delta=f"{c_op:,.0f} MW (Op) / {c_queue:,.0f} MW (Q)",
                    delta_color="off"
                )
    else:
        st.info("No data selected.")

elif view == "Market Resources":
    st.header("⚡ Market Resources")
    
    # Requested Embed: ERCOT Dashboards
    st.subheader("ERCOT Grid Dashboards")
    st.components.v1.iframe("https://www.ercot.com/gridmktinfo/dashboards", height=800, scrolling=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("EIA Texas Electricity Profile")
        # Embed EIA State Electricity Profile
        st.markdown(
            """
            <iframe src="https://www.eia.gov/state/?sid=TX" width="100%" height="800" style="border:none;"></iframe>
            """, 
            unsafe_allow_html=True
        )
        
    with col2:
        st.subheader("Official ERCOT Dashboards")
        st.info("Direct links to key operational data.")
        
        st.markdown("""
        ### 🟢 Real-Time Operations
        - [**Supply and Demand**](https://www.ercot.com/gridmktinfo/dashboards/supplyanddemand)
        - [**System Frequency**](https://www.ercot.com/gridmktinfo/dashboards/frequency)
        - [**Generation Outages**](https://www.ercot.com/gridmktinfo/dashboards/systemoutages)
        
        ### 💰 Market Prices
        - [**LMP Contour Map**](https://www.ercot.com/gridmktinfo/dashboards/lmpcontourmap)
        - [**DAM Clearing Prices**](https://www.ercot.com/mktinfo/dam)
        - [**AS Capacity Monitor**](https://www.ercot.com/gridmktinfo/dashboards/ascapmonitor)
        
        ### 📅 Planning & Reports
        - [**Resource Adequacy (MORA)**](https://www.ercot.com/gridinfo/resource)
        - [**Interconnection (GIS) Status**](https://www.ercot.com/gridinfo/resource)
        """)
        
    with col3:
        st.subheader("Fuel & Regulatory")
        st.warning("Drivers of Load & Price")
        
        st.markdown("""
        ### 🔥 Natural Gas (Fuel)
        - [**EIA Natural Gas Weekly**](https://www.eia.gov/naturalgas/weekly/)
        - [**Waha Hub Spot Prices**](https://www.eia.gov/dnav/ng/hist/rngwhhdm.htm)
        
        ### 🌦️ Weather (Demand)
        - [**NOAA 6-10 Day Outlook**](https://www.cpc.ncep.noaa.gov/products/predictions/610day/)
        - [**ERCOT Weather Forecast**](https://www.ercot.com/gridmktinfo/dashboards/weatherforecast)
        
        ### 🏛️ Regulatory / IMM
        - [**PUCT Interchange (Filings)**](https://interchange.puc.texas.gov/)
        - [**Independent Market Monitor (IMM)**](https://www.potomaceconomics.com/markets/ercot/)
        """)
        
        st.warning("Note: External links open in a new tab.")
