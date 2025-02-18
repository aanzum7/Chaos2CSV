import json
import pandas as pd
import streamlit as st
import io

# ---- Streamlit Page Config ----
st.set_page_config(
    page_title="chaos2csv - JSON to CSV Converter",
    page_icon="🔄",
    layout="centered"
)

# ---- Function: Flatten JSON ----
def flatten_json(data, parent_key='', sep='_'):
    """Recursively flattens a nested JSON object into a single-level dictionary."""
    items = {}
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.update(flatten_json(value, new_key, sep=sep))
            elif isinstance(value, list):
                if all(isinstance(i, dict) for i in value):  
                    for i, sub_value in enumerate(value):
                        items.update(flatten_json(sub_value, f"{new_key}_{i}", sep=sep))
                else:  
                    items[new_key] = ', '.join(map(str, value)) if value else '*'
            else:
                items[new_key] = value if value is not None else '*'
    return items

# ---- Function: Convert JSON to CSV ----
def convert_json_to_csv(json_data):
    """Converts JSON data into a structured CSV-compatible format."""
    expanded_data = []

    if isinstance(json_data, dict):
        if all(isinstance(v, list) for v in json_data.values()):
            if not any(json_data.values()):
                st.error("❌ JSON contains only empty lists.")
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
            expanded_data.append(flatten_json(json_data))  

    elif isinstance(json_data, list):
        if all(isinstance(entry, dict) for entry in json_data):
            expanded_data = [flatten_json(entry) for entry in json_data]
        else:
            st.error("❌ Each JSON entry must be a dictionary.")
            return None

    df = pd.DataFrame(expanded_data).fillna('*')

    # Convert numeric columns safely
    for col in df.columns:
        if df[col].dtype == 'object':  
            df[col] = df[col].replace('*', pd.NA)  
            try:
                df[col] = pd.to_numeric(df[col])  
            except ValueError:
                pass  

    return df

# ---- Sidebar ----
with st.sidebar:
    st.image("https://img.icons8.com/external-flat-juicy-fish/100/000000/external-data-science-data-science-flat-flat-juicy-fish.png", width=150)
    
    st.title("chaos2csv")
    st.write("**Unleashing Order from the Chaos of Data**")

    st.write("""
        🔹 **Convert Complex JSON Files to CSV**  
        🔹 **Handles Nested & Structured Data**  
        🔹 **Download Ready-to-Use CSV Files**
    """)

    st.subheader("📌 About Developer")
    st.write("🔹 **Tanvir Anzum** – Analytics Scientist & AI Enthusiast")
    st.write("🚀 Passionate about transforming messy data into insights.")
    st.markdown("📧 [Connect on LinkedIn](https://www.linkedin.com/in/aanzum/)")

# ---- Main Section ----
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>chaos2csv: JSON to CSV Converter</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555;'>Convert nested JSON files into structured CSV effortlessly.</p>", unsafe_allow_html=True)

st.divider()

# ---- Upload Section ----
st.subheader("📂 Upload Your JSON File")
uploaded_file = st.file_uploader("Upload JSON File", type=["json"], label_visibility="collapsed")

if uploaded_file is not None:
    try:
        json_data = json.load(uploaded_file)
        df = convert_json_to_csv(json_data)
        
        if df is not None:
            st.subheader("📊 Converted CSV Preview")
            st.dataframe(df, use_container_width=True)

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')

            # ---- Download Button ----
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_buffer.getvalue(),
                file_name="converted_data.csv",
                mime="text/csv",
                key="download-btn"
            )
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file. Please upload a valid JSON.")
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
