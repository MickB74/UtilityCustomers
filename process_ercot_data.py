import pandas as pd
import os
import re

DATA_DIR = 'data'
OUTPUT_FILE = 'historical_gen_load_emissions_2020_2024.csv'

# Emission Factors (approx tons CO2/MWh)
EMISSION_FACTORS = {
    'Coal': 1.0,
    'Gas': 0.43,
    'Gas-CC': 0.4, # Often just "Gas" in report
    'Biomass': 0.0, # Net zero usually assumed or low
    'Wind': 0.0,
    'Solar': 0.0,
    'Nuclear': 0.0,
    'Hydro': 0.0,
    'Other': 0.43 # conservative
}

dfs = []

# List months
SHEETS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

print("Scanning files...")
files = [f for f in os.listdir(DATA_DIR) if 'intgenbyfuel' in f.lower() and f.endswith('.xlsx')]
files.sort()

for file in files:
    match = re.search(r'20[2-3][0-9]', file)
    if not match: continue
    year = int(match.group(0))
    if not (2020 <= year <= 2024): continue
    
    print(f"Processing {file}...")
    file_path = os.path.join(DATA_DIR, file)
    
    xl = pd.ExcelFile(file_path)
    
    for sheet in xl.sheet_names:
        if sheet in SHEETS:
            # Read header first to find time cols
            df_raw = pd.read_excel(file_path, sheet_name=sheet, header=0)
            
            # Identify time columns: typically "0:15", "0:30"... or "00:15"
            # They might be strings or datetime.time objects
            # We want cols from index 4 onwards usually
            # Col 0: Date, Col 1: Fuel
            if 'Fuel' not in df_raw.columns:
                print(f"  Skipping sheet {sheet} (no Fuel col)")
                continue
            
            # Melt
            # Keep Date, Fuel
            # Data columns are everything else except 'Settlement Type', 'Total'
            id_vars = ['Date', 'Fuel']
            value_vars = [c for c in df_raw.columns if c not in id_vars and c not in ['Settlement Type', 'Total']]
            
            melted = df_raw.melt(id_vars=id_vars, value_vars=value_vars, var_name='Time', value_name='MW')
            
            # Convert Date + Time -> Datetime
            # Time is likely "HH:MM" string. 
            # Note: "24:00" might exist, usually handled as next day 00:00 or special handling
            # Check Time format
            # Using str conversion just in case
            melted['TimeStr'] = melted['Time'].astype(str)
            # Handle "24:00:00" if present? ERCOT usually uses 00:15 ... 24:00
            
            # Simple conversion function
            def parse_datetime(row):
                d = row['Date']
                t = row['TimeStr']
                # Clean time string "00:15:00" -> "00:15"
                # If t is "24:00" or similar
                if '24:00' in t:
                    return d + pd.Timedelta(days=1)
                try:
                    return pd.to_datetime(f"{d.date()} {t}")
                except:
                    return None # Error or "Total" col sneak

            # This is slow row-by-row. Vectorized approach:
            # Convert TimeStr to timedelta?
            # Let's assume standard format.
            
            # Pivot primarily on Fuel
            # But first we need clean timestamps
            # Let's pivot first to reduce rows
            # Index: [Date, Time], Columns: Fuel, Values: MW
            pivoted = melted.pivot_table(index=['Date', 'Time'], columns='Fuel', values='MW', aggfunc='sum').reset_index()
            dfs.append(pivoted)

print("Concatenating...")
full_df = pd.concat(dfs, ignore_index=True)

# Create Timestamp
# Fix 24:00 and DST
full_df['TimeStr'] = full_df['Time'].astype(str)
full_df['TimeStr'] = full_df['TimeStr'].str.replace(' (DST)', '', regex=False).str.strip()

mask_24 = full_df['TimeStr'].str.contains('24:00')
full_df.loc[mask_24, 'TimeStr'] = '00:00:00'
full_df['TempDate'] = full_df['Date']
full_df.loc[mask_24, 'TempDate'] = full_df.loc[mask_24, 'Date'] + pd.Timedelta(days=1)

# Ensure TimeStr is HH:MM:SS
# Some might be HH:MM
# Just rely on pandas parser
full_df['Timestamp'] = pd.to_datetime(full_df['TempDate'].astype(str).str.split().str[0] + ' ' + full_df['TimeStr'], errors='coerce')

# Drop NaT
full_df = full_df.dropna(subset=['Timestamp'])

# Resample to Hourly
full_df = full_df.set_index('Timestamp').sort_index()

# Numeric cols only
numeric_cols = full_df.select_dtypes(include=['number']).columns
hourly = full_df[numeric_cols].resample('h').mean()

# Calculate Load (Approx Total Gen)
# Sum of all fuels
hourly['Load'] = hourly.sum(axis=1)

# Calculate Emissions
hourly['Emissions'] = 0.0
for fuel, factor in EMISSION_FACTORS.items():
    # Match fuzzy fuel names
    # E.g. "Gas" matches "Natural Gas", "Combined Cycle", "Gas Steam"??
    # From inspection, Fuel is just "Biomass", "Coal", "Gas", "Hydro", "Nuclear", "Other", "Solar", "Wind" usually.
    # We will map standard names.
    # Check columns
    for col in hourly.columns:
        if fuel.lower() in col.lower():
            hourly['Emissions'] += hourly[col] * factor

# Price is missing. Set to NaN
hourly['Price'] = 0.0 # Placeholder

# Save
hourly.to_csv(OUTPUT_FILE)
print(f"Saved processed data to {OUTPUT_FILE} with {len(hourly)} rows.")
print("Columns:", hourly.columns.tolist())
