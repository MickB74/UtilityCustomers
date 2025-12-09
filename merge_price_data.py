import pandas as pd
import os

MAIN_DATA_FILE = 'historical_gen_load_emissions_2020_2024.csv'
TEMP_DIR = 'temp_prices'

print("Loading main data...")
df_main = pd.read_csv(MAIN_DATA_FILE)
df_main['Timestamp'] = pd.to_datetime(df_main['Timestamp'])
df_main = df_main.set_index('Timestamp').sort_index()

# Drop existing Price if needed
if 'Price' in df_main.columns:
    df_main = df_main.drop(columns=['Price'])

years = [2020, 2021, 2022, 2023, 2024]
price_dfs = []

print("Loading Price Parquet files...")
for year in years:
    fpath = os.path.join(TEMP_DIR, f'ercot_rtm_{year}.parquet')
    if os.path.exists(fpath):
        print(f"  Processing {year}...")
        try:
            df_p = pd.read_parquet(fpath)
            
            # Filter HB_NORTH
            if 'Location' in df_p.columns:
                mask = df_p['Location'] == 'HB_NORTH'
                df_north = df_p[mask].copy()
            else:
                # 2023/2024 might have different schema?
                # Check columns if Location missing.
                # Assuming standard gridstatus schema.
                pass 
                
            if 'Time_Central' in df_north.columns:
                df_north = df_north[['Time_Central', 'SPP']].rename(columns={'Time_Central': 'Timestamp', 'SPP': 'Price'})
            elif 'Interval Ending' in df_north.columns: # 2023/2024 gridstatus parquet might have this
                # Check column mapping
                # GridStatus 2023/2024 from repo are often raw.
                # Let's handle 'Time' or 'Interval Ending'
                time_c = 'Interval Ending' if 'Interval Ending' in df_north.columns else 'Time'
                df_north = df_north[[time_c, 'Settlement Point Price']].rename(columns={time_c: 'Timestamp', 'Settlement Point Price': 'Price'})

            # Standardize Time
            # df_north['Timestamp'] usually tz-aware.
            # Convert to naive to match main data
            if df_north['Timestamp'].dt.tz is not None:
                df_north['Timestamp'] = df_north['Timestamp'].dt.tz_convert(None)
            
            # Resample to Hourly Mean
            df_north = df_north.set_index('Timestamp').resample('h').mean()
            price_dfs.append(df_north)
            
        except Exception as e:
            print(f"    Error processing {year}: {e}")
    else:
        print(f"  Warning: File not found for {year}: {fpath}")

if price_dfs:
    df_prices = pd.concat(price_dfs)
    print(f"Collected {len(df_prices)} price records.")
    
    # Merge
    df_final = df_main.join(df_prices, how='left')
    df_final = df_final.reset_index()
    
    df_final.to_csv(MAIN_DATA_FILE, index=False)
    print(f"Updated {MAIN_DATA_FILE} with Price data.")
else:
    print("No price data found.")
