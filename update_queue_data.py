import pandas as pd
import os
import glob

def update_queue_data():
    # 1. Find the latest GIS Report Excel file
    list_of_files = glob.glob('*.xlsx') # Assuming file is in root, or modify path
    # Look for pattern if needed, e.g. GIS_Report*.xlsx
    gis_files = [f for f in list_of_files if 'GIS_Report' in f]
    
    if not gis_files:
        print("No GIS Report Excel file found.")
        return

    latest_file = max(gis_files, key=os.path.getctime)
    print(f"Reading latest GIS Report: {latest_file}")

    # 2. Read the "Project Details - Large Gen" sheet
    # inspect_gis.py showed that skiprows=20 makes the header row the first row.
    try:
        df = pd.read_excel(latest_file, sheet_name='Project Details - Large Gen', skiprows=30)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    print(f"Read {len(df)} rows from Excel.")
    
    # 3. Export to CSV
    # The target CSV is 'projects_in_queue_all_generators.csv'
    output_csv = 'projects_in_queue_all_generators.csv'
    
    # We export assuming the columns in Excel match what we want in CSV.
    # inspect_gis.py output confirmed the headers ("INR", "Project Name", etc.) match.
    
    df.to_csv(output_csv, index=False)
    print(f"Successfully updated {output_csv}")

if __name__ == "__main__":
    update_queue_data()
