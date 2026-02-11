import pandas as pd
import json

def process_eia_data():
    file_path = 'EIA860M_december_generator2025.xlsx'
    
    # Load headers mostly to find the right sheet
    # Sheets are usually "Operating", "Planned", "Retired", "Canceled"
    # We want "Operating"
    
    print(f"Reading {file_path}...")
    try:
        # Skip top rows if needed. Usually EIA files have 1-2 header rows.
        # Inspect_eia_headers.py showed header is at row index 2 (line 3 in Excel)
        df = pd.read_excel(file_path, sheet_name='Operating', header=2)
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    print(f"Columns found: {list(df.columns)}")

    # Filter for ERCOT
    # Column "Balancing Authority Code" should be "ERCO"
    if 'Balancing Authority Code' in df.columns:
        ercot_df = df[df['Balancing Authority Code'] == 'ERCO']
    else:
        print("Column 'Balancing Authority Code' not found.")
        return

    print(f"Found {len(ercot_df)} operational units in ERCOT.")

    # Select relevant columns
    # We need: Entity Name, Plant Name, Technology, Nameplate Capacity (MW), County, Operating Year/Month
    
    # Standardize Technology
    # EIA uses "Prime Mover" and "Energy Source 1"
    # We need to map to: Solar, Wind, Battery, Gas, Coal, Nuclear, etc.
    
    ercot_df['Technology'] = 'Other'
    
    # Simple mapping based on Energy Source Code
    # SUN = Solar
    # WND = Wind
    # NG = Natural Gas
    # SUB = Bituminous Coal, LIG = Lignite Coal -> Coal
    # BAT = Battery (Energy Source might be empty for battery, use Prime Mover 'BA')
    # NUC = Nuclear
    
    def map_technology(row):
        prime_mover = str(row.get('Prime Mover Code', '')).upper()
        energy_source = str(row.get('Energy Source Code', '')).upper()
        
        if prime_mover == 'BA':
            return 'Battery'
        if energy_source == 'SUN':
            return 'Solar'
        if energy_source == 'WND':
            return 'Wind'
        if energy_source == 'NG':
            return 'Gas'
        if energy_source in ['SUB', 'LIG', 'RC', 'WC']:
            return 'Coal'
        if energy_source == 'NUC':
            return 'Nuclear'
        if energy_source == 'WAT':
            return 'Hydro'
        
        return 'Other'

    ercot_df['Technology'] = ercot_df.apply(map_technology, axis=1)
    
    # Create list of dicts
    projects = []
    for _, row in ercot_df.iterrows():
        try:
            capacity = float(row.get('Nameplate Capacity (MW)', 0))
            if capacity <= 0: continue
            
            project = {
                'name': f"{row.get('Plant Name')} {row.get('Generator ID')}", # Unique name
                'technology': row['Technology'],
                'mw': capacity,
                'county': str(row.get('County', '')).title(),
                'status': 'Operational',
                'cod_year': int(row.get('Operating Year', 0)) if not pd.isna(row.get('Operating Year')) else 0,
                'developer': str(row.get('Entity Name', '')),
                'notes': f"EIA-860M Dec 2025. Prime Mover: {row.get('Prime Mover Code')}"
            }
            projects.append(project)
        except Exception as e:
            continue
            
    # Save to JSON
    output_file = 'webapp/public/generation_operational_eia.json'
    with open(output_file, 'w') as f:
        json.dump(projects, f, indent=2)
        
    print(f"Saved {len(projects)} projects to {output_file}")
    
    # Optional: Calculate summary stats
    summary = ercot_df.groupby('Technology')['Nameplate Capacity (MW)'].sum().sort_values(ascending=False)
    print("\nCapacity by Technology (MW):")
    print(summary)

if __name__ == "__main__":
    process_eia_data()
