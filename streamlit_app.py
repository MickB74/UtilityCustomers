import streamlit as st
import pandas as pd
import json
import os
import altair as alt
import plotly.express as px

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
view = st.sidebar.radio("Navigation", ["Electricity Users", "Generation Projects", "Market Resources", "Historical Analysis"])

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

elif view == "Generation Projects":
    # Load Generation Data
    # @st.cache_data  <-- Commented out to ensure fresh load
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
    st.info("The official ERCOT dashboards cannot be embedded directly. Please view them here:")
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

elif view == "Historical Analysis":
    st.header("📈 Historical Analysis (2020-2024)")
    
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
                # Year Selection
                years = sorted(df_hist['Year'].unique())
                st.write("**Select Years**")
                
                # Year Actions
                col_y_act1, col_y_act2, _ = st.columns([1,1,4])
                if col_y_act1.button("Select All Years"):
                    for y in years:
                        st.session_state[f"year_{y}"] = True
                if col_y_act2.button("Clear All Years"):
                    for y in years:
                        st.session_state[f"year_{y}"] = False
                
                cols_y = st.columns(len(years))
                selected_years = []
                for i, year in enumerate(years):
                    with cols_y[i]:
                        # Default True if not in state
                        key = f"year_{year}"
                        if key not in st.session_state:
                            st.session_state[key] = True
                        if st.checkbox(str(year), key=key):
                            selected_years.append(year)

                # Month Selection
                st.write("**Select Months**")
                import calendar
                month_names = list(calendar.month_name)[1:] # ['January', 'February', ...]
                
                # Month Actions
                col_m_act1, col_m_act2, _ = st.columns([1,1,4])
                if col_m_act1.button("Select All Months"):
                    for i in range(1, 13):
                        st.session_state[f"month_{i}"] = True
                if col_m_act2.button("Clear All Months"):
                    for i in range(1, 13):
                        st.session_state[f"month_{i}"] = False
                
                cols_m = st.columns(6) # 2 rows of 6
                selected_months = []
                
                for i, m_name in enumerate(month_names):
                    month_num = i + 1
                    col_idx = i % 6
                    with cols_m[col_idx]:
                        key = f"month_{month_num}"
                        if key not in st.session_state:
                            st.session_state[key] = True
                        if st.checkbox(m_name, key=key):
                            selected_months.append(month_num)

                if selected_years and selected_months:
                    filtered_hist = df_hist[
                        (df_hist['Year'].isin(selected_years)) & 
                        (df_hist['Month_Num'].isin(selected_months))
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
                    # Default to Monthly if multiple years, else Weekly or Daily
                    default_ix = 2 if len(selected_years) > 1 else 1 # Weekly vs Daily
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
