# streamlit_app.py
import json
import pandas as pd
import io
import requests
import streamlit as st

# Streamlit UI
st.title("chaos2csv: Unleashing Order from the Chaos of Data")

# Sidebar content
with st.sidebar:
    st.title("chaos2csv")
    st.write(""" 
        **Unleashing Order from the Chaos of Data**
        chaos2csv is designed to simplify the task of transforming complex JSON data into a structured CSV file.
        With a deep focus on analytical precision, it takes chaotic, nested, or unorganized data and converts it into a neat CSV file.
    """)
    
    st.subheader("Key Features:")
    st.write("""
        - **Raw to Refined:** A journey from raw, chaotic data to structured CSV clarity.
        - **Seamless Conversion:** Handle even the most complex JSON structures with ease.
        - **Instant Preview & Download:** See the results in real-time and download your clean CSV file.
        - **AI-Driven Structure:** Automatically detect and flatten nested data fields.
    """)

    st.subheader("About the Author:")
    st.write("""
        **Tanvir Anzum** – Data Analyst  
        Passionate about turning data chaos into clarity, with a focus on building smarter solutions through data.
    """)

# File upload
uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])

if uploaded_file is not None:
    # Read the JSON file into memory
    file_data = uploaded_file.getvalue()

    # Prepare a request to send the JSON data to the FastAPI backend
    files = {'file': ('file.json', file_data, 'application/json')}
    
    # Sending the JSON file to the FastAPI backend for conversion
    response = requests.post("http://127.0.0.1:8000/convert/", files=files)
    
    if response.status_code == 200:
        # Successfully converted, get CSV data
        result = response.json()
        filename = result['filename']
        csv_data = result['csv_data']
        
        # Convert the CSV data to a Pandas DataFrame for preview
        df = pd.read_csv(io.StringIO(csv_data))

        # Show the preview of the CSV file
        st.subheader("Preview of Converted CSV:")
        st.dataframe(df)

        # Provide download button for the CSV file
        st.download_button(
            label="Download CSV file",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv"
        )

    else:
        st.error(f"Error: {response.status_code} - {response.text}")
