import pdfplumber
import pandas as pd

def extract_tables_by_headers(pdf_path, target_headers):
    """
    Scans a multi-page PDF for tables matching a list of target headers 
    and returns a dictionary of Pandas DataFrames.
    """
    # Dictionary to hold data frames for each found table type
    extracted_data = {header: [] for header in target_headers}
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages to process: {len(pdf.pages)}")
        
        # Loop through every page in the PDF
        for page_num, page in enumerate(pdf.pages, start=1):
            
            # Extract all tables found on the current page
            tables = page.extract_tables()
            
            for table in tables:
                if not table or len(table) < 2:
                    continue  # Skip empty tables or tables with no data rows
                
                # Examine the first row (potential header row)
                # Convert cells to lowercase strings to make matching case-insensitive
                first_row_str = " ".join([str(cell).lower() for cell in table[0] if cell is not None])
                
                # Check if this table matches any of our target headers
                for target in target_headers:
                    if target.lower() in first_row_str:
                        print(f"-> Found table matching '{target}' on Page {page_num}")
                        
                        # Process rows: Clean up whitespace and newlines (\n) within cells
                        cleaned_table = []
                        for row in table:
                            cleaned_row = [
                                str(cell).replace('\n', ' ').strip() if cell is not None else "" 
                                for cell in row
                            ]
                            cleaned_table.append(cleaned_row)
                        
                        # Convert to DataFrame using the first cleaned row as the column names
                        df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
                        
                        # Store it in our master dictionary
                        extracted_data[target].append(df)
                        
    # Concatenate tables if the same header spanned across multiple pages
    final_dfs = {}
    for target, df_list in extracted_data.items():
        if df_list:
            # ignore_index=True ensures the index resets seamlessly across combined pages
            final_dfs[target] = pd.concat(df_list, ignore_index=True)
        else:
            final_dfs[target] = None
            print(f"No table found for target header: '{target}'")
            
    return final_dfs

# --- EXECUTION ---

# Define your file path and the list of headers you are searching for
PDF_FILE = "your_document.pdf"
HEADERS_TO_FIND = ["Account Summary", "Risk Rating", "Risk Elements"]

# Run the extraction
all_tables = extract_tables_by_headers(PDF_FILE, HEADERS_TO_FIND)

# Access and save your structured DataFrames
if all_tables["Account Summary"] is not None:
    account_summary_df = all_tables["Account Summary"]
    print("\n--- Final Account Summary Table ---")
    print(account_summary_df)
    account_summary_df.to_csv("account_summary_final.csv", index=False)

if all_tables["Risk Rating"] is not None:
    risk_rating_df = all_tables["Risk Rating"]
    risk_rating_df.to_csv("risk_rating_final.csv", index=False)
  
