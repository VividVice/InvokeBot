import pandas as pd
import csv

# Input and output file names
input_csv = 'input.csv'
output_csv = 'output_cleaned.csv'

# Read CSV into DataFrame
df = pd.read_csv(input_csv, header=None)

# Predefined team and unit labels
columns = [
    ('Defense', 'Unit 1'),
    ('Defense', 'Unit 2'),
    ('Defense', 'Unit 3'),
    ('Attack', 'Unit 1'),
    ('Attack', 'Unit 2'),
    ('Attack', 'Unit 3'),
]

# Positions of relevant columns (every 3rd col because of merged-like format)
col_indices = [0, 3, 6, 9, 13, 17]

# Notes column index
notes_col_index = 21

# Prepare clean rows
cleaned_rows = []

# Iterate over rows
for index, row in df.iterrows():
    # Skip completely empty rows
    if row.isnull().all():
        continue

    # Extract Notes (if any)
    notes = row[notes_col_index] if notes_col_index < len(row) else ""

    # Extract units from predefined columns
    for (team, slot), col in zip(columns, col_indices):
        if col < len(row):
            unit = row[col]
            if pd.notnull(unit) and unit != '':
                cleaned_rows.append({
                    'Team': team,
                    'Slot': slot,
                    'Unit': unit,
                    'Notes': notes
                })

# Write the cleaned CSV
with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Team', 'Slot', 'Unit', 'Notes']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for row in cleaned_rows:
        writer.writerow(row)

print(f"Cleaned CSV written to {output_csv}")

# Extract unique units and save to units.txt
unique_units = set()
for row in cleaned_rows:
    unique_units.add(row['Unit'])

# Sort the units alphabetically
sorted_units = sorted(unique_units)

# Write unique units to units.txt
with open('units.txt', 'w', encoding='utf-8') as f:
    for unit in sorted_units:
        f.write(f"{unit}\n")

print(f"Unique units written to units.txt")