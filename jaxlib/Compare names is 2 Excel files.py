import pandas as pd
import difflib

def read_excel(file_path, column_name):
    """Read names from an Excel file."""
    df = pd.read_excel(file_path, engine='openpyxl')
    return df[column_name].dropna().unique()

def find_similar_names(names_list1, names_list2, threshold=0.8):
    """Compare two lists of names and find similar names based on a threshold."""
    similar_names = []
    for name1 in names_list1:
        for name2 in names_list2:
            similarity = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            if similarity >= threshold:
                similar_names.append((name1, name2, similarity))
    return similar_names

# Update these paths and column names according to your Excel files
file_path1 = r'C:\Users\andre\Downloads\Southern Manufacturing 2024 Lead List.xlsx'
file_path2 = r'C:\Users\andre\Downloads\Session21.xlsx'
column_name1 = 'Company'  # Column name in the first Excel where names are stored
column_name2 = 'company'  # Column name in the second Excel where names are stored

# Read names from the Excel files
names_list1 = read_excel(file_path1, column_name1)
names_list2 = read_excel(file_path2, column_name2)

# Find similar names
similar_names = find_similar_names(names_list1, names_list2, threshold=0.6)

# Print similar names
for name1, name2, similarity in similar_names:
    print(f'"{name1}" and "{name2}" are similar with a similarity score of {similarity:.2f}')
