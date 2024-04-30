import pandas as pd

# Load JSON data (replace 'data.json' with your JSON file's name)
json_file = 'C:\\Users\\andre\\Documents\\VKS\\API\\all guidebooks.json'
df = pd.read_json(json_file)

# Convert to Excel and save it (replace 'output.xlsx' with your desired output file name)
excel_file = 'all Guidebooks.xlsx'
df.to_excel(excel_file, index=False, engine='openpyxl')
