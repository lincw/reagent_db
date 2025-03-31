import pandas as pd

# file path #should be changed according to the path where the excel file is located 
file_path = r"/tmp/H8.1.xlsx"

# Define the columns to extract #take note of the capital letters and special characters
columns_extract = ["ENTREZ_GENE_ID","ORF_ID","Symbol","Name","H8_CONSO_PLA_ID","H8_CONSO_POS_ID"]

# Load the Excel file

 # Read the Excel file into a DataFrame
 #header is set as 1 cause the first row is empty and 
 #column names are in the second row (first row is 0 and
 # and second row is 1)
df = pd.read_excel(file_path , header=1)
#see if the columns names are detected  
print(df.columns)

#incase the column names have spaces before or after the name this code will remove the spaces 
df.columns = df.columns.str.strip()

#to make sure the column names are in string format
df.columns = df.columns.astype(str)
    # Extract the specified columns

extracted_columns = df[columns_extract]

print(extracted_columns)
    # Define the output file path
output_file_path = r"/tmp/extracted_data.xlsx"

    # Save the extracted columns to a new Excel file
extracted_columns.to_excel(output_file_path, index=False)

#converting the extracted columns into table form 
#import directory  #openpyxl is used to read/write excel files 
#workbook helps create a new excel file
#importing table to define a table
#import dataframe_to_row to convert a pandas dataframe to exce rows that can be added to the 
#created exce file 
from openpyxl import Workbook
from openpyxl.worksheet.table import Table
from openpyxl.utils.dataframe import dataframe_to_rows

# Create a new workbook and add the dataframe to it

wb = Workbook()
ws = wb.active

# add the dataframe rows into the new active sheet ws
for row in dataframe_to_rows(extracted_columns, index=False, header=True):ws.append(row)

# Define the table range (e.g., A1:F939 for 6 columns and 939 rows)
table_range8 = f"A1:{chr(64 + extracted_columns.shape[1])}{extracted_columns.shape[0] + 1}"

# Create the table and add it to the worksheet
table1 = Table(displayName="TableH8.1", ref=table_range8)
ws.add_table(table1)

# Save the workbook
wb.save(output_file_path) 

#code for library 9.1
# Define the file path and columns to extract
# Define the file path and columns to extract
file_path9 = r"C:\Users\tehre\OneDrive\Desktop\ofr database\20180927_hORFeome 9.1.xlsx"
columns_extract9 = ["orf_id", "Pool group#", "entrez_gene_id", "entrez_gene_symbol", "h9_plate", "h9_pos"]

# Load the Excel file, specifying the header as the second row (index=1)
df9 = pd.read_excel(file_path9, header=1)

# Clean up column names
df9.columns = df9.columns.str.strip()  # Remove leading/trailing whitespace
df9.columns = df9.columns.astype(str) #convert the column names to string format

df9.columns = df9.columns.str.replace(" ", "_")  # Replace spaces with underscores
df9.columns = df9.columns.str.replace("#", "")  # Remove special characters

# Update column names to match cleaned names
columns_extract_cleaned = ["orf_id", "Pool_group", "entrez_gene_id", "entrez_gene_symbol", "h9_plate", "h9_pos"]
# Extract specified columns
extracted_columns9 = df9[columns_extract_cleaned]
output_file_path9 = r"C:\Users\tehre\OneDrive\Desktop\ofr database\extracted_data9.xlsx"
extracted_columns9.to_excel(output_file_path9, index=False)


########## try to make a table 
wb = Workbook()
ws9 = wb.active

# Append the dataframe rows into the new sheet
for row in dataframe_to_rows(extracted_columns9, index=False, header=True):ws9.append(row)

# Define the table range 
table_range = f"A1:{chr(64 + extracted_columns.shape[1])}{extracted_columns.shape[0] + 1}"

# Create the table and add it to the worksheet
table9 = Table(displayName="Extractedcolumns9", ref=table_range)
ws9.add_table(table9)

# Save the workbook
wb.save(output_file_path9)
