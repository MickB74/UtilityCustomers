import streamlit as st
import pandas as pd
import json
import os
import altair as alt
import plotly.express as px

# Set Page Layout to Wide
st.set_page_config(layout="wide", page_title="ERCOT Data")

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
st.title("⭐ ERCOT Data")

# Navigation
view = st.sidebar.radio("Navigation", ["Electricity Users", "Generation Fleet", "External Dashboards", "Historical Trends"])

if view == "Electricity Users":
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

    # Estimated Peak Loads (Reflective of new strict Hub mapping)
    HUB_PEAKS = {
        'North': 30000,   # DFW, East, North Central (Waco/Temple)
        'Houston': 23000, # Coast Zone
        'South': 24000,   # Austin, San Antonio, Valley, Corpus
        'West': 12000     # Permian, Far West, Lubbock
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

elif view == "Generation Fleet":
    # Load Generation Data
    def load_operational_data():
        with open('webapp/public/generation_operational.json', 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    
    def load_queue_data():
        with open('webapp/public/generation_queue.json', 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    
    # --- Dashboard Header ---
    st.header("⚡ Generation Fleet")
    
    # Create Tabs
    tab1, tab2 = st.tabs(["🟢 Operational", "🔵 Interconnection Queue"])
    
    # ==================== TAB 1: OPERATIONAL ====================
    with tab1:
        op_df = load_operational_data()
        
        # --- Sidebar Filters for Operational ---
        st.sidebar.header("Operational Filters")
        
        # Reset Button
        if st.sidebar.button("Reset Operational Filters"):
            st.session_state.op_tech = []
            st.session_state.op_county = []
            st.session_state.op_hub = []
            st.session_state.op_search = ""
        
        # Tech Filter
        op_tech_opts = sorted(op_df['technology'].unique())
        op_sel_tech = st.sidebar.multiselect("Technology", op_tech_opts, key="op_tech")
        
        # Hub Filter
        op_hub_opts = sorted(op_df['hub'].unique()) if 'hub' in op_df.columns else []
        op_sel_hub = st.sidebar.multiselect("ERCOT Hub", op_hub_opts, key="op_hub")

        # County Filter
        op_county_opts = sorted(op_df['county'].unique())
        op_sel_county = st.sidebar.multiselect("County", op_county_opts, key="op_county")

        # Search Box
        op_search = st.sidebar.text_input("Search Project/Dev/Loc", key="op_search")
        
        # Apply Filters
        filtered_op = op_df.copy()
        if op_sel_tech:
            filtered_op = filtered_op[filtered_op['technology'].isin(op_sel_tech)]
        if op_sel_hub:
            filtered_op = filtered_op[filtered_op['hub'].isin(op_sel_hub)]
        if op_sel_county:
            filtered_op = filtered_op[filtered_op['county'].isin(op_sel_county)]
        
        if op_search:
            s = op_search.lower()
            filtered_op = filtered_op[
                filtered_op['project_name'].str.lower().str.contains(s) |
                filtered_op['developer'].str.lower().str.contains(s) |
                filtered_op['county'].str.lower().str.contains(s) |
                filtered_op['city'].str.lower().str.contains(s)
            ]
        
        # Metrics
        m1, m2, m3 = st.columns(3)
        total_op_mw = filtered_op['capacity_mw'].sum()
        count_op = len(filtered_op)
        
        m1.metric("Total Operational Capacity", f"{total_op_mw:,.0f} MW")
        m2.metric("Project Count", f"{count_op}")
        m3.metric("Average Project Size", f"{total_op_mw/count_op:,.0f} MW" if count_op > 0 else "N/A")
        
        st.markdown("---")
        
        # Main Table
        st.subheader(f"Operational Projects ({count_op})")
        
        st.dataframe(
            filtered_op[['project_name', 'technology', 'capacity_mw', 'hub', 'city', 'county', 'cod_year', 'developer', 'notes']],
            use_container_width=True,
            column_config={
                "capacity_mw": st.column_config.NumberColumn("Capacity (MW)", format="%.0f MW"),
                "cod_year": st.column_config.NumberColumn("COD Year", format="%d"),
                "project_name": "Project Name",
                "technology": "Technology",
                "hub": "Hub",
                "city": "City",
                "county": "County",
                "developer": "Developer",
                "notes": "Notes"
            },
            height=600,
            hide_index=True
        )

        # Analysis Section
        st.markdown("---")
        st.subheader("📊 Operational Fleet Analysis")
        
        # Technology Breakdown
        st.markdown("##### Technology Mix")
        if not filtered_op.empty:
            tech_stats = filtered_op.groupby('technology')['capacity_mw'].sum().sort_values(ascending=False)
            cols = st.columns(len(tech_stats))
            for idx, (tech, mw) in enumerate(tech_stats.items()):
                with cols[idx]:
                    pct = (mw / total_op_mw * 100) if total_op_mw > 0 else 0
                    st.metric(
                        label=f"{tech}",
                        value=f"{mw:,.0f} MW",
                        delta=f"{pct:.1f}%",
                        delta_color="off"
                    )
        
        # Hub Breakdown
        st.markdown("##### Capacity by Hub")
        if not filtered_op.empty:
            hub_stats = filtered_op.groupby('hub')['capacity_mw'].sum().sort_values(ascending=False)
            h_cols = st.columns(len(hub_stats))
            for idx, (hub, mw) in enumerate(hub_stats.items()):
                with h_cols[idx]:
                    pct = (mw / total_op_mw * 100) if total_op_mw > 0 else 0
                    st.metric(
                        label=f"{hub}",
                        value=f"{mw:,.0f} MW",
                        delta=f"{pct:.1f}%",
                        delta_color="off"
                    )
        
        # Top Counties
        st.markdown("##### Top 5 Counties")
        if not filtered_op.empty:
            county_stats = filtered_op.groupby('county')['capacity_mw'].sum().sort_values(ascending=False).head(5)
            c_cols = st.columns(5)
            for idx, (county, mw) in enumerate(county_stats.items()):
                with c_cols[idx]:
                    st.metric(label=f"{county} County", value=f"{mw:,.0f} MW")
    
    # ==================== TAB 2: QUEUE ====================
    with tab2:
        queue_df = load_queue_data()
        
        # --- Sidebar Filters for Queue ---
        st.sidebar.header("Queue Filters")
        
        # Reset Button
        if st.sidebar.button("Reset Queue Filters"):
            st.session_state.queue_tech = []
            st.session_state.queue_county = []
            st.session_state.queue_hub = []
            st.session_state.queue_search = ""
        
        # Tech Filter
        queue_tech_opts = sorted(queue_df['technology'].unique())
        queue_sel_tech = st.sidebar.multiselect("Technology", queue_tech_opts, key="queue_tech")
        
        # Hub Filter
        queue_hub_opts = sorted(queue_df['hub'].unique()) if 'hub' in queue_df.columns else []
        queue_sel_hub = st.sidebar.multiselect("ERCOT Hub", queue_hub_opts, key="queue_hub")

        # County Filter
        queue_county_opts = sorted(queue_df['county'].unique())
        queue_sel_county = st.sidebar.multiselect("County", queue_county_opts, key="queue_county")

        # Search Box
        queue_search = st.sidebar.text_input("Search Project/Dev/Loc", key="queue_search")
        
        # Apply Filters
        filtered_queue = queue_df.copy()
        if queue_sel_tech:
            filtered_queue = filtered_queue[filtered_queue['technology'].isin(queue_sel_tech)]
        if queue_sel_hub:
            filtered_queue = filtered_queue[filtered_queue['hub'].isin(queue_sel_hub)]
        if queue_sel_county:
            filtered_queue = filtered_queue[filtered_queue['county'].isin(queue_sel_county)]
        
        if queue_search:
            s = queue_search.lower()
            filtered_queue = filtered_queue[
                filtered_queue['project_name'].str.lower().str.contains(s) |
                filtered_queue['developer'].str.lower().str.contains(s) |
                filtered_queue['county'].str.lower().str.contains(s) |
                filtered_queue['city'].str.lower().str.contains(s)
            ]
        
        # Metrics
        m1, m2, m3 = st.columns(3)
        total_queue_mw = filtered_queue['capacity_mw'].sum()
        count_queue = len(filtered_queue)
        
        m1.metric("Total Queue Capacity", f"{total_queue_mw:,.0f} MW")
        m2.metric("Project Count", f"{count_queue}")
        m3.metric("Average Project Size", f"{total_queue_mw/count_queue:,.0f} MW" if count_queue > 0 else "N/A")
        
        st.markdown("---")
        
        # Main Table
        st.subheader(f"Queue Projects ({count_queue})")
        
        st.dataframe(
            filtered_queue[['project_name', 'technology', 'capacity_mw', 'hub', 'city', 'county', 'cod_year', 'developer', 'notes']],
            use_container_width=True,
            column_config={
                "capacity_mw": st.column_config.NumberColumn("Capacity (MW)", format="%.0f MW"),
                "cod_year": st.column_config.NumberColumn("COD Year", format="%d"),
                "project_name": "Project Name",
                "technology": "Technology",
                "hub": "Hub",
                "city": "City",
                "county": "County",
                "developer": "Developer",
                "notes": "Notes"
            },
            height=600,
            hide_index=True
        )

        # Analysis Section
        st.markdown("---")
        st.subheader("📊 Interconnection Queue Analysis")
        
        # Technology Breakdown
        st.markdown("##### Technology Mix")
        if not filtered_queue.empty:
            tech_stats = filtered_queue.groupby('technology')['capacity_mw'].sum().sort_values(ascending=False)
            cols = st.columns(len(tech_stats))
            for idx, (tech, mw) in enumerate(tech_stats.items()):
                with cols[idx]:
                    pct = (mw / total_queue_mw * 100) if total_queue_mw > 0 else 0
                    st.metric(
                        label=f"{tech}",
                        value=f"{mw:,.0f} MW",
                        delta=f"{pct:.1f}%",
                        delta_color="off"
                    )
        
        # Hub Breakdown
        st.markdown("##### Capacity by Hub")
        if not filtered_queue.empty:
            hub_stats = filtered_queue.groupby('hub')['capacity_mw'].sum().sort_values(ascending=False)
            h_cols = st.columns(len(hub_stats))
            for idx, (hub, mw) in enumerate(hub_stats.items()):
                with h_cols[idx]:
                    pct = (mw / total_queue_mw * 100) if total_queue_mw > 0 else 0
                    st.metric(
                        label=f"{hub}",
                        value=f"{mw:,.0f} MW",
                        delta=f"{pct:.1f}%",
                        delta_color="off"
                    )
        
        # Top Counties
        st.markdown("##### Top 5 Counties")
        if not filtered_queue.empty:
            county_stats = filtered_queue.groupby('county')['capacity_mw'].sum().sort_values(ascending=False).head(5)
            c_cols = st.columns(5)
            for idx, (county, mw) in enumerate(county_stats.items()):
                with c_cols[idx]:
                    st.metric(label=f"{county} County", value=f"{mw:,.0f} MW")

elif view == "External Dashboards":
    st.header("⚡ External Dashboards")
    
    # Requested Embed: ERCOT Dashboards
    st.subheader("ERCOT Grid Dashboards")
    st.link_button("Open ERCOT Dashboards", "https://www.ercot.com/gridmktinfo/dashboards", type="primary")
    
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
        - [**System Frequency**](https://www.ercot.com/content/cdr/html/real_time_system_conditions.html)
        - [**Generation Outages**](https://www.ercot.com/gridmktinfo/dashboards/generationoutages)
        
        ### 💰 Market Prices
        - [**LMP Contour Map**](https://www.ercot.com/content/cdr/contours/rtmLmp.html)
        - [**DAM Clearing Prices**](https://www.ercot.com/mktinfo/dam)
        - [**AS Capacity Monitor**](https://www.ercot.com/content/cdr/html/as_capacity_monitor.html)
        
        ### 📅 Planning & Reports
        - [**Resource Adequacy (MORA)**](https://www.ercot.com/gridinfo/resource)
        - [**Interconnection (GIS) Status**](https://www.ercot.com/gridinfo/resource)
        """)
        
    with col3:
        st.subheader("Fuel & Regulatory")
        st.warning("Drivers of Load & Price")
        
        st.markdown("""
        ### 🔥 Natural Gas (Fuel)
        - [**EIA Natural Gas Weekly (incl. Waha)**](https://www.eia.gov/naturalgas/weekly/)
        - [**CME Henry Hub Futures**](https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.settlements.html)
        
        ### 🌦️ Weather (Demand)
        - [**NOAA 6-10 Day Outlook**](https://www.cpc.ncep.noaa.gov/products/predictions/610day/)
        - [**ERCOT Weather Forecast**](https://www.ercot.com/gridmktinfo/dashboards/weatherforecast)
        
        ### 🏛️ Regulatory / IMM
        - [**PUCT Interchange (Filings)**](https://interchange.puc.texas.gov/)
        - [**Independent Market Monitor (IMM)**](https://www.potomaceconomics.com/markets/ercot/)
        """)
        
        st.warning("Note: External links open in a new tab.")

elif view == "Historical Trends":
    st.header("📈 Historical Trends (2020-2024)")
    
    # File Uploader (Hidden by default)
    with st.expander("Upload Custom CSV (Optional)"):
        uploaded_file = st.file_uploader("Upload Historical CSV", type=['csv'])
    
    # Check for default local file
    default_file = 'historical_gen_load_emissions_2020_2024.csv'
    df_hist = None
    time_col = None
    
    if uploaded_file is not None:
        try:
            df_hist = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
    elif os.path.exists(default_file):
        # st.info(f"Using pre-loaded ERCOT Fuel Mix data (2020-2024).") # Removed per user request
        df_hist = pd.read_csv(default_file)
    else:
        st.warning("Data not found. Please upload a CSV file.")

    if df_hist is not None:
        try:
            # Try to parse timestamp
            # Common column names: 'Timestamp', 'Date', 'Time', 'OperDay'
            for col in df_hist.columns:
                if 'time' in col.lower() or 'date' in col.lower():
                    time_col = col
                    break
            
            if time_col:
                df_hist[time_col] = pd.to_datetime(df_hist[time_col])
                df_hist = df_hist.sort_values(by=time_col)
            
            # Add Year/Month columns for filtering if they don't exist
            if 'Year' not in df_hist.columns and time_col:
                df_hist['Year'] = df_hist[time_col].dt.year
            if 'Month_Num' not in df_hist.columns and time_col:
                df_hist['Month_Num'] = df_hist[time_col].dt.month
            
            # Filter by Year and Month
            if time_col and 'Year' in df_hist.columns:
                # Get min and max dates
                min_date = df_hist[time_col].min().date()
                max_date = df_hist[time_col].max().date()
                
                # Date Range Selector
                st.write("**Select Date Range**")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input(
                        "Start Date",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="hist_start_date"
                    )
                
                with col2:
                    end_date = st.date_input(
                        "End Date",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="hist_end_date"
                    )
                
                # Quick Selection Buttons
                st.write("**Quick Select:**")
                quick_cols = st.columns(5)
                
                with quick_cols[0]:
                    if st.button("Last Month"):
                        st.session_state.hist_start_date = (max_date - pd.DateOffset(months=1)).date()
                        st.session_state.hist_end_date = max_date
                        st.rerun()
                
                with quick_cols[1]:
                    if st.button("Last 3 Months"):
                        st.session_state.hist_start_date = (max_date - pd.DateOffset(months=3)).date()
                        st.session_state.hist_end_date = max_date
                        st.rerun()
                
                with quick_cols[2]:
                    if st.button("Last 6 Months"):
                        st.session_state.hist_start_date = (max_date - pd.DateOffset(months=6)).date()
                        st.session_state.hist_end_date = max_date
                        st.rerun()
                
                with quick_cols[3]:
                    if st.button("Last Year"):
                        st.session_state.hist_start_date = (max_date - pd.DateOffset(years=1)).date()
                        st.session_state.hist_end_date = max_date
                        st.rerun()
                
                with quick_cols[4]:
                    if st.button("All Time"):
                        st.session_state.hist_start_date = min_date
                        st.session_state.hist_end_date = max_date
                        st.rerun()
                
                # Filter data by date range
                if start_date and end_date:
                    filtered_hist = df_hist[
                        (df_hist[time_col].dt.date >= start_date) & 
                        (df_hist[time_col].dt.date <= end_date)
                    ]
                    
                    # 1. Key Metrics (Calculate on raw hourly data for accuracy)
                    st.subheader("Key Metrics")
                    cols = st.columns(4)
                    
                    # Try to find standard columns loosely
                    def get_col(keywords):
                        for c in filtered_hist.columns:
                            if any(k in c.lower() for k in keywords):
                                return c
                        return None
                    
                    price_col = get_col(['price', 'lmp', 'settlement'])
                    load_col = get_col(['load', 'demand'])
                    emis_col = get_col(['emission', 'co2', 'carbon'])
                    wind_col = get_col(['wind'])
                    
                    if price_col:
                        avg_price = filtered_hist[price_col].mean()
                        # Check if price is real (not just 0s)
                        if avg_price > 0.01:
                            cols[0].metric("Avg Price", f"${avg_price:.2f}")
                        else:
                            cols[0].metric("Avg Price", "N/A")
                            st.warning("Price data appears to be missing (all zeros).")
                    if load_col:
                        max_load = filtered_hist[load_col].max()
                        max_load_idx = filtered_hist[load_col].idxmax()
                        max_load_time = filtered_hist.loc[max_load_idx, time_col]
                        cols[1].metric("Peak Load", f"{max_load:,.0f} MW")
                        cols[1].caption(f"on {max_load_time.strftime('%b %d, %Y %H:%M')}")
                    if emis_col:
                        total_emis = filtered_hist[emis_col].sum()
                        cols[2].metric("Total Emissions", f"{total_emis:,.0f} tons")
                    
                    # Monthly Summary Table
                    with st.expander("View Monthly Detailed Metrics"):
                        st.write("### Monthly Summary")
                        summary_df = filtered_hist.copy()
                        summary_df['Month'] = summary_df[time_col].dt.month_name()
                        summary_df['Month_Num'] = summary_df[time_col].dt.month
                        
                        agg_rules = {}
                        col_renames = {}
                        
                        if price_col:
                            agg_rules[price_col] = 'mean'
                            col_renames[price_col] = 'Avg Price ($/MWh)'
                        if load_col:
                            agg_rules[load_col] = 'max'
                            col_renames[load_col] = 'Peak Load (MW)'
                        if emis_col:
                            agg_rules[emis_col] = 'sum'
                            col_renames[emis_col] = 'Total Emissions (tons)'
                            
                        if agg_rules:
                            monthly_stats = summary_df.groupby(['Year', 'Month_Num', 'Month']).agg(agg_rules).reset_index()
                            monthly_stats = monthly_stats.sort_values(['Year', 'Month_Num'])
                            monthly_stats = monthly_stats.drop(columns=['Month_Num'])
                            monthly_stats = monthly_stats.rename(columns=col_renames)
                            
                            # Format columns
                            format_dict = {}
                            if price_col:
                                format_dict['Avg Price ($/MWh)'] = "${:,.2f}"
                            if load_col:
                                format_dict['Peak Load (MW)'] = "{:,.0f}"
                            if emis_col:
                                format_dict['Total Emissions (tons)'] = "{:,.0f}"
                                
                            st.dataframe(monthly_stats.style.format(format_dict), hide_index=True, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # Resampling Controls
                    st.subheader("Trends")
                    freq_map = {'Hourly': 'h', 'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M'}
                    # Default to Monthly if date range > 1 year, else Weekly or Daily
                    date_range_days = (end_date - start_date).days
                    default_ix = 3 if date_range_days > 365 else (2 if date_range_days > 90 else 1)  # Monthly, Weekly, or Daily
                    selected_freq = st.radio("Resolution", list(freq_map.keys()), index=default_ix, horizontal=True)
                    
                    # Resample Data for Charts
                    chart_data = filtered_hist.set_index(time_col).resample(freq_map[selected_freq]).mean().reset_index()
                    
                    # Performance Check: Smart Downsampling
                    MAX_POINTS = 5000
                    if len(chart_data) > MAX_POINTS and selected_freq == 'Hourly':
                        st.warning(f"⚠️ High data volume ({len(chart_data):,} points). Displaying 6-hour averages to optimize performance.")
                        chart_data = filtered_hist.set_index(time_col).resample('6h').mean().reset_index()
                    
                    # 2. Price & Load Chart
                    st.write("### Price & Load")
                    
                    if price_col and load_col and chart_data[price_col].sum() > 1:
                         # Dual Axis Chart using Altair
                         base = alt.Chart(chart_data).encode(
                             x=alt.X(time_col, title='Time', axis=alt.Axis(format='%b %Y', labelOverlap=True))
                         )
                         
                         line_load = base.mark_line(color='#1f77b4').encode(
                             y=alt.Y(load_col, title='Load (MW)', axis=alt.Axis(titleColor='#1f77b4')),
                             tooltip=[
                                 alt.Tooltip(time_col, title='Time', format='%Y-%m-%d %H:%M'),
                                 alt.Tooltip(load_col, title='Load (MW)', format=',.2f')
                             ]
                         )
                         
                         line_price = base.mark_line(color='#ff7f0e').encode(
                             y=alt.Y(price_col, title='Price ($/MWh)', axis=alt.Axis(titleColor='#ff7f0e')),
                             tooltip=[
                                 alt.Tooltip(time_col, title='Time', format='%Y-%m-%d %H:%M'),
                                 alt.Tooltip(price_col, title='Price ($/MWh)', format=',.2f')
                             ]
                         )
                         
                         c = alt.layer(line_load, line_price).resolve_scale(
                             y='independent'
                         ).interactive()
                         
                         st.altair_chart(c, use_container_width=True)
                         
                    elif price_col and load_col:
                         # Just Load if Price is 0
                         st.line_chart(chart_data, x=time_col, y=[load_col])
                         
                    elif price_col and chart_data[price_col].sum() > 1:
                        st.line_chart(chart_data, x=time_col, y=[price_col])
                    
                    # 3. Generation Mix (if columns exist)
                    st.write("### Generation Mix")
                    gen_cols = []
                    potential_gens = ['wind', 'solar', 'gas', 'coal', 'nuclear', 'hydro', 'biomass', 'other']
                    for g in potential_gens:
                         matches = [c for c in filtered_hist.columns if g.lower() in c.lower()]
                         if matches:
                             # Exclude Price and Emissions columns
                             valid_matches = [m for m in matches if 'price' not in m.lower() and 'emissions' not in m.lower()]
                             if valid_matches:
                                 gen_cols.extend(valid_matches)
                    
                    # Remove duplicates
                    gen_cols = list(set(gen_cols))
                    
                    if gen_cols:
                        # Calculate Total Generation for the line
                        chart_data['Total Gen'] = chart_data[gen_cols].sum(axis=1)

                        # Use Plotly for interactive legend
                        # Melt to long format
                        melted_gen = chart_data.melt(id_vars=[time_col], value_vars=gen_cols, var_name='Fuel', value_name='MW')
                        
                        fig = px.area(melted_gen, x=time_col, y='MW', color='Fuel',
                                      title="Generation by Fuel Type",
                                      labels={'MW': 'Generation (MW)', 'Timestamp': 'Time'},
                                      color_discrete_sequence=px.colors.qualitative.Bold)
                        
                        # Add Total Generation Line
                        import plotly.graph_objects as go
                        fig.add_trace(go.Scatter(
                            x=chart_data[time_col], 
                            y=chart_data['Total Gen'],
                            mode='lines',
                            name='Total Generation',
                            line=dict(color='white', width=2, dash='dot'),
                            hovertemplate='%{y:,.2f} MW<extra>Total Generation</extra>'
                        ))
                        
                        # Fix layout and tooltips
                        fig.update_traces(selector=dict(type='area'), hovertemplate='%{y:,.2f} MW')
                        fig.update_layout(legend_title_text='Fuel Type', xaxis_tickformat='%b %Y')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Could not identify specific generation columns (Wind, Solar, Gas, etc.) automatically.")
                    
                    st.markdown("---")
                    
                    # 4. Data Preview & Download
                    st.write("### Data Preview")
                    st.dataframe(filtered_hist.head(100), use_container_width=True)
                    
                    csv = filtered_hist.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Filtered Data (CSV)",
                        data=csv,
                        file_name='ercot_historical_data.csv',
                        mime='text/csv',
                    )
                        
                else:
                    st.warning("Please select at least one year.")
            else:
                 if df_hist is not None:
                    st.error("Could not identify a Timestamp/Date column.")
                    st.write("Preview:", df_hist.head())

        except Exception as e:
            st.error(f"Error processing data: {e}")
