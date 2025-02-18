import json
import pandas as pd
import io
import requests
import streamlit as st
import uvicorn
from threading import Thread
from fastapi import FastAPI, File, UploadFile, HTTPException

app = FastAPI()

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

@app.post("/convert/")
async def convert_file(file: UploadFile = File(...)):
    """Handles JSON to CSV conversion with improved edge-case handling."""
    try:
        contents = await file.read()
        if not contents.strip():
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        try:
            json_data = json.loads(contents)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        if not json_data:
            raise HTTPException(status_code=400, detail="Empty JSON content.")

        expanded_data = []

        if isinstance(json_data, dict):
            if all(isinstance(v, list) for v in json_data.values()):  
                if not any(json_data.values()):
                    raise HTTPException(status_code=400, detail="JSON contains only empty lists.")
                
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
                raise HTTPException(status_code=400, detail="Each JSON entry must be a dictionary.")

        df = pd.DataFrame(expanded_data).fillna('*')

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')

        return {"filename": file.filename, "csv_data": csv_buffer.getvalue()}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# Start FastAPI backend in a separate thread
def run_backend():
    uvicorn.run(app, host="127.0.0.1", port=8000)
Thread(target=run_backend, daemon=True).start()

# Streamlit UI
st.title("chaos2csv: Unleashing Order from the Chaos of Data")

with st.sidebar:
    st.title("chaos2csv")
    st.write("""
        **Unleashing Order from the Chaos of Data**

        chaos2csv simplifies the transformation of complex JSON data into structured CSV files.
        It handles nested, unorganized data and converts it into a neat, readable format.
    """)
    
    st.subheader("Key Features:")
    st.write("""
        - **Raw to Refined:** Convert raw JSON into structured CSV.
        - **Seamless Conversion:** Handles deeply nested JSON effortlessly.
        - **Instant Preview & Download:** Real-time preview and easy downloads.
        - **AI-Driven Structure:** Automatically detects and flattens nested data.
    """)
    
    st.subheader("About the Author:")
    st.write("""
        **Tanvir Anzum** – Data Analyst  
        Passionate about transforming chaotic data into meaningful insights.
    """)

uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])

if uploaded_file is not None:
    file_data = uploaded_file.getvalue()
    files = {'file': ('file.json', file_data, 'application/json')}
    
    response = requests.post("http://127.0.0.1:8000/convert/", files=files)
    
    if response.status_code == 200:
        result = response.json()
        filename = result['filename']
        csv_data = result['csv_data']
        df = pd.read_csv(io.StringIO(csv_data))
        
        st.subheader("Preview of Converted CSV:")
        st.dataframe(df)

        st.download_button(
            label="Download CSV file",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv"
        )
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
