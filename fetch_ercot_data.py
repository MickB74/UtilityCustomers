import requests
import zipfile
import io
import os
import pandas as pd
import re

DATA_DIR = 'data'
# os.makedirs(DATA_DIR, exist_ok=True) # Already downloaded

# Helper to merge years
dfs = []
print("Scanning data directory...")
for file in os.listdir(DATA_DIR):
    # Match IntGenbyFuelYYYY.xlsx case insensitive
    if 'intgenbyfuel' in file.lower() and file.endswith('.xlsx'):
        # Extract year
        match = re.search(r'20[2-3][0-9]', file)
        if match:
            year = int(match.group(0))
            if 2020 <= year <= 2024:
                print(f"Processing {file}...")
                file_path = os.path.join(DATA_DIR, file)
                # Load Excel.
                # Usually these have 'Date', 'Time' or 'Date-Time'
                try:
                    df = pd.read_excel(file_path)
                    print(f"  Loaded {len(df)} rows. Columns: {list(df.columns[:5])}...")
                    dfs.append(df)
                except Exception as e:
                    print(f"  Error reading {file}: {e}")

if dfs:
    full_df = pd.concat(dfs, ignore_index=True)
    
    # Clean up Date/Time
    # Inspect columns to unify timestamp
    # Common ERCOT columns in these reports: 'Date', 'Fuel', 'Settlement Point', OR 'Date', 'Fuel1', 'Fuel2'...
    # Actually Fuel Mix report is usually: Date, Fuel -> Gen (Stacked) OR Date, Time, Wind, Solar...
    
    # We will save it first, inspecting structure
    output_path = 'historical_fuel_mix_2020_2024.csv'
    full_df.to_csv(output_path, index=False)
    print(f"Saved merged data to {output_path} with shape {full_df.shape}")
else:
    print("No matching years found.")
