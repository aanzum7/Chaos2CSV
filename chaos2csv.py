import json
import pandas as pd
import streamlit as st
import io

# Function to flatten nested JSON
def flatten_json(data, parent_key='', sep='_'):
    """Recursively flattens a nested JSON object into a single-level dictionary."""
    items = {}
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.update(flatten_json(value, new_key, sep=sep))
            elif isinstance(value, list):
                if all(isinstance(i, dict) for i in value):  # List of dicts
                    for i, sub_value in enumerate(value):
                        items.update(flatten_json(sub_value, f"{new_key}_{i}", sep=sep))
                else:  # Simple list
                    items[new_key] = ', '.join(map(str, value)) if value else '*'
            else:
                items[new_key] = value if value is not None else '*'
    return items

# Function to convert JSON to DataFrame
def convert_json_to_csv(json_data):
    """Converts JSON data into a structured CSV-compatible format."""
    expanded_data = []

    if isinstance(json_data, dict):
        if all(isinstance(v, list) for v in json_data.values()):
            if not any(json_data.values()):
                st.error("JSON contains only empty lists.")
                return None
            
            max_length = max(len(v) for v in json_data.values())

            for idx in range(max_length):
                row = {}
                for key, value in json_data.items():
                    if isinstance(value, list) and len(value) > idx:
                        item = value[idx]
                        row.update(flatten_json(item, key) if isinstance(item, dict) else {key: item})
                    else:
                        row[key] = '*'
                expanded_data.append(row)
        else:
            expanded_data.append(flatten_json(json_data))  # Handle normal dict

    elif isinstance(json_data, list):
        if all(isinstance(entry, dict) for entry in json_data):
            expanded_data = [flatten_json(entry) for entry in json_data]
        else:
            st.error("Each JSON entry must be a dictionary.")
            return None

    df = pd.DataFrame(expanded_data).fillna('*')

    # Convert numeric columns
    for col in df.columns:
        if df[col].dtype == 'object':  # If column type is string
            df[col] = df[col].replace('*', pd.NA)  # Replace '*' with NaN
            try:
                df[col] = pd.to_numeric(df[col])  # Convert valid numbers
            except ValueError:
                pass  # Keep non-numeric values as they are

    return df

# Streamlit UI
st.title("chaos2csv: Convert JSON to CSV")

with st.sidebar:
    st.title("chaos2csv")
    st.write("""
        **Unleashing Order from the Chaos of Data**
        
        Easily convert complex JSON files into clean CSV format.
    """)
    
    st.subheader("Key Features:")
    st.write("""
        - **Handles Nested JSON**
        - **Smart Data Flattening**
        - **Instant CSV Preview**
        - **Downloadable CSV File**
    """)
    
    st.subheader("About the Author:")
    st.write("""
        **Tanvir Anzum** – Data & AI Specialist  
        Passionate about transforming chaotic data into meaningful insights.
    """)

# File upload section
uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])

if uploaded_file is not None:
    try:
        json_data = json.load(uploaded_file)
        df = convert_json_to_csv(json_data)
        
        if df is not None:
            st.subheader("Preview of Converted CSV:")
            st.dataframe(df)

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')

            st.download_button(
                label="Download CSV file",
                data=csv_buffer.getvalue(),
                file_name="converted_data.csv",
                mime="text/csv"
            )
    except json.JSONDecodeError:
        st.error("Invalid JSON file. Please upload a valid JSON.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
