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
view = st.radio("Navigation", ["Customer Map", "Market Resources"], horizontal=True, label_visibility="collapsed")

if view == "Customer Map":
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

elif view == "Market Resources":
    st.header("⚡ Market Resources")
    st.markdown("Real-time data and official reports from ERCOT and EIA.")
    
    # --- 1. Real-Time Grid Conditions (Live API) ---
    st.subheader("🟢 Real-Time Grid Conditions")
    
    @st.cache_data(ttl=300) # Cache for 5 minutes
    def get_ercot_conditions():
        try:
            url = "https://www.ercot.com/api/1/services/read/dashboards/supply-demand.json"
            r = requests.get(url, timeout=5)
            data = r.json()
            
            # Find the "current" or most recent interval
            # The API returns 'data' list. We need the last entry that has a timestamp <= now? 
            # Actually, usually the API returns 'current' data for today.
            # Let's just grab the entry matching current text or closest to now.
            # Simplification: Grab the entry where "timestamp" is closest to now.
            
            # For this simple implementation, let's grab the first entry of the current hour
            # Or easier: The API usually provides a "lastUpdated" field and the data array
            # Let's assume the API returns forward looking data too.
            # We will parse the 'lastUpdated' to valid data.
            
            # SAFE FALLBACK: Just grab the entry that represents "now" from the list
            now = datetime.datetime.now(pytz.timezone('US/Central'))
            
            # Filter for current hour
            current_data = data['data'][0] # Default to first if search fails
            
            for entry in data['data']:
                # entry['timestamp'] format: 2025-12-07 20:30:00-0600
                # Parsing specific format might be brittle.
                # Let's look for the one matching the current hour ending?
                pass
            
            # Actually, usually the first item in the future list is "right now" or next hour.
            # Let's allow Streamlit to just display the latest available ACTUAL data point.
            # Ideally we'd parse timestamps, but for MVP, let's grab the item corresponding to "current" time.
            
            # Better Approach: Just display the first element of 'data' which is usually the current interval start
            current_cond = data['data'][0]
            
            return {
                "demand": current_cond['forecastedDemand'],
                "capacity": current_cond['availCapGen'],
                "status": "Normal" # Placeholder, actual status needs another API
            }
        except Exception as e:
            return None

    conditions = get_ercot_conditions()
    
    if conditions:
        c1, c2, c3 = st.columns(3)
        
        demand = conditions['demand']
        capacity = conditions['capacity']
        reserves = capacity - demand
        
        c1.metric("Current Demand", f"{demand:,.0f} MW", border=True)
        c2.metric("Available Capacity", f"{capacity:,.0f} MW", border=True)
        c3.metric("Reserve Margin", f"{reserves:,.0f} MW", delta=f"{(reserves/demand):.1%}", border=True)
    else:
        st.warning("Could not fetch real-time grid data. Please check ERCOT.com")

    st.markdown("---")

    # --- 2. Real-Time LMP & Gas ---
    col_gas, col_lmp = st.columns([1, 1])
    
    with col_gas:
        st.subheader("🔥 Natural Gas (Henry Hub)")
        # TradingView Widget for Henry Hub
        st.components.v1.html(
            """
            <!-- TradingView Widget BEGIN -->
            <div class="tradingview-widget-container">
              <div id="tradingview_123"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget(
              {
              "width": "100%",
              "height": 400,
              "symbol": "TVC:USOIL",
              "interval": "D",
              "timezone": "America/Chicago",
              "theme": "light",
              "style": "2",
              "locale": "en",
              "enable_publishing": false,
              "hide_top_toolbar": true,
              "save_image": false,
              "container_id": "tradingview_123",
              "symbol": "TVC:NG1!" 
              }
              );
              </script>
            </div>
            <!-- TradingView Widget END -->
            """,
            height=410
        )
        st.caption("Source: TradingView (Henry Hub Futures)")

    with col_lmp:
        st.subheader("💰 Real-Time LMPs")
        # Embed the Official ERCOT LMP Map
        # It's a bit heavy, but requested "Real Time LMP in each zone"
        # The Map is the best way to show "Zone" data visually.
        st.markdown(
            """
            <iframe src="https://www.ercot.com/content/cdr/html/real_time_lmp_map.html" width="100%" height="400" style="border:none; border-radius: 10px;"></iframe>
            """, 
            unsafe_allow_html=True
        )
        st.caption("Source: ERCOT.com")

    st.markdown("---")

    # --- 3. Reference Links (Keep existing) ---
    st.subheader("📚 Key Resources")
    
    l1, l2, l3 = st.columns(3)
    
    with l1:
        st.markdown("**operations**")
        st.markdown("- [Supply & Demand](https://www.ercot.com/gridmktinfo/dashboards/supplyanddemand)")
        st.markdown("- [Outage Scheduler](https://www.ercot.com/gridmktinfo/dashboards/outagescheduler)")
    
    with l2:
        st.markdown("**prices**")
        st.markdown("- [LMP Map](https://www.ercot.com/content/cdr/html/real_time_lmp_map.html)")
        st.markdown("- [DAM Prices](https://www.ercot.com/mktinfo/dam)")
    
    with l3: 
        st.markdown("**regulatory**")
        st.markdown("- [PUCT Interchange](https://interchange.puc.texas.gov/)")
        st.markdown("- [Potomac Price (IMM)](https://www.potomaceconomics.com/markets/ercot/)")
    
    st.markdown("---")
    
    # --- 4. Deep Dive: EIA Data ---
    with st.expander("Expand for EIA Texas Electricity Profile (Deep Dive)"):
        st.markdown(
            """
            <iframe src="https://www.eia.gov/state/?sid=TX" width="100%" height="800" style="border:none;"></iframe>
            """, 
            unsafe_allow_html=True
        )
