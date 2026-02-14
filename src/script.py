import pandas as pd
import re
import os

# --- Configuration for Column Aliases ---
# Add any future column names here (lowercase)
NAME_ALIASES = ['name', 'full name', 'full_name', 'first name', 'student name', 'customer name']
PHONE_ALIASES = ['phone', 'phone number', 'phone_number', 'mobile', 'contact', 'contact number', 'cell']
EMAIL_ALIASES = ['email', 'email address', 'email_address', 'e-mail', 'mail']

def clean_name(name):
    if pd.isna(name):
        return name
    
    # Strip whitespace
    name = str(name).strip()
    
    # Check if string contains *only* ASCII characters (English)
    # If it contains any non-ASCII character (Hindi, accents, emoji, etc.), return as is
    try:
        name.encode('ascii')
    except UnicodeEncodeError:
        return name
    
    # Otherwise, capitalize first letters (Title Case)
    return name.title()

def clean_phone(phone):
    if pd.isna(phone):
        return phone
    
    # Convert to string and extract only digits
    phone_str = str(phone)
    digits = re.sub(r'\D', '', phone_str)
    
    # Extract exactly 10 digits (handling cases like +91, 091, etc.)
    if len(digits) >= 10:
        # If it has country code 91, take the last 10 digits
        if digits.startswith('91') and len(digits) > 10:
            digits = digits[-10:]
        # If someone added a 0 in front (e.g., 09876543210)
        elif len(digits) == 11 and digits.startswith('0'):
            digits = digits[-10:]
        # Fallback: just grab the last 10 digits if it's longer
        elif len(digits) > 10:
             digits = digits[-10:]
             
    return digits if digits else None

def clean_email(email):
    if pd.isna(email):
        return email
    # Strip spaces and convert to lowercase
    return str(email).strip().lower()

def process_file(input_filepath, output_filepath):
    print(f"Reading file: {input_filepath}")
    
    # 1. Read the file based on extension
    ext = os.path.splitext(input_filepath)[1].lower()
    if ext == '.csv':
        encodings_to_try = ['utf-8', 'utf-16', 'utf-8-sig', 'latin-1', 'cp1252']
        df = None
        for encoding in encodings_to_try:
            try:
                print(f"Attempting to read CSV with encoding: {encoding}")
                # Use engine='python' and sep=None to sniff delimiter automatically
                df = pd.read_csv(input_filepath, encoding=encoding, sep=None, engine='python')
                print(f"Successfully read CSV with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Failed with encoding {encoding}: {e}")
                continue
        
        if df is None:
            raise ValueError(f"Could not read the CSV file. Tried encodings: {encodings_to_try}")

    elif ext in ['.xlsx', '.xls']:
        df = pd.read_excel(input_filepath)
    else:
        raise ValueError("Unsupported file format. Please provide a .csv or .xlsx file.")

    # 2. Identify the columns dynamically
    # Convert columns to lowercase and strip spaces for easier matching
    original_cols = df.columns.tolist()
    normalized_cols = [str(c).strip().lower() for c in original_cols]
    
    # Map to hold our standardized column names
    col_mapping = {}
    
    for orig, norm in zip(original_cols, normalized_cols):
        if norm in NAME_ALIASES and 'full_name' not in col_mapping.values():
            col_mapping[orig] = 'full_name'
        elif norm in PHONE_ALIASES and 'phone_number' not in col_mapping.values():
            col_mapping[orig] = 'phone_number'
        elif norm in EMAIL_ALIASES and 'email' not in col_mapping.values():
            col_mapping[orig] = 'email'

    # Rename the columns in the dataframe
    df = df.rename(columns=col_mapping)
    
    # Check what columns we successfully found
    found_cols = [col for col in ['full_name', 'phone_number', 'email'] if col in df.columns]
    
    if not found_cols:
         print("Error: Could not find any recognizable Name, Phone, or Email columns.")
         return

    # 3. Clean the Data
    print("Cleaning data...")
    if 'full_name' in df.columns:
        df['full_name'] = df['full_name'].apply(clean_name)
    
    if 'phone_number' in df.columns:
        df['phone_number'] = df['phone_number'].apply(clean_phone)
        
    if 'email' in df.columns:
        df['email'] = df['email'].apply(clean_email)

    # 4. Reorder and export the final dataframe
    # Filter the dataframe to only include the found columns in the desired order
    final_df = df[found_cols]
    
    print(f"Saving cleaned data to: {output_filepath}")
    # Save to CSV without the index column
    final_df.to_csv(output_filepath, index=False, encoding='utf-8-sig')
    print("Done!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_file> <output_file>")
        sys.exit(1)

    INPUT_FILE = sys.argv[1]
    OUTPUT_FILE = sys.argv[2]
    
    try:
        process_file(INPUT_FILE, OUTPUT_FILE)
    except FileNotFoundError:
        print(f"Error: The file '{INPUT_FILE}' was not found. Please check the path.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)