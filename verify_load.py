import pandas as pd
df = pd.read_csv('historical_gen_load_emissions_2020_2024.csv')
print(df[['Timestamp', 'Load']].head())
print("Peak Load:", df['Load'].max())
print("Avg Load:", df['Load'].mean())
