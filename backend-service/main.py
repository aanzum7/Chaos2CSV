from fastapi import FastAPI, File, UploadFile
import json
import pandas as pd
import io

app = FastAPI()

@app.post("/convert/")
async def convert_file(file: UploadFile = File(...)):
    # Read the uploaded JSON file
    contents = await file.read()

    # Parse the JSON data
    try:
        json_data = json.loads(contents)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON file."}

    # Normalize the JSON data into a DataFrame
    try:
        df = pd.json_normalize(json_data)
    except ValueError as e:
        return {"error": f"Error normalizing JSON: {str(e)}"}

    # Expand nested lists of dictionaries (if any exist)
    for column in df.columns:
        if df[column].apply(lambda x: isinstance(x, list)).any():  # Check if any row has a list
            expanded_data = pd.json_normalize(df[column].explode().dropna().tolist())
            df = pd.concat([df.drop(columns=[column]), expanded_data], axis=1)

    # Convert float columns to object before replacing NaN to avoid FutureWarning
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = df[col].astype(object)

    # Replace missing values with an asterisk (*)
    df.fillna('*', inplace=True)

    # Convert DataFrame to CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    return {
        "filename": file.filename,
        "csv_data": csv_data
    }
