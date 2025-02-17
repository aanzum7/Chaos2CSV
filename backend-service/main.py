from fastapi import FastAPI, File, UploadFile
import json
import pandas as pd
from typing import Optional
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

    # Flatten the JSON data
    for key, value in json_data.items():
        # Check if the value is a string representing a list
        if isinstance(value, str):
            try:
                json_data[key] = json.loads(value)  # Parse the string as JSON
            except json.JSONDecodeError:
                return {"error": f"Invalid JSON in field {key}"}

    # Normalize the JSON data into a flat structure
    try:
        df = pd.json_normalize(json_data)
    except ValueError as e:
        return {"error": "Error normalizing JSON: " + str(e)}

    # Now, let's manually expand nested columns like `transaction_details` and `gregorian_date`
    # Assuming `transaction_details` and `gregorian_date` are lists of dictionaries
    for column in df.columns:
        if isinstance(df[column][0], list):  # Check if the column is a list
            # Expand the list of dictionaries into separate columns
            expanded_data = pd.json_normalize(df[column].explode().dropna().tolist())
            df = pd.concat([df.drop(columns=[column]), expanded_data], axis=1)

    # Replace missing values with asterisk (*)
    df.fillna('*', inplace=True)

    # Convert DataFrame to CSV
    csv_data = df.to_csv(index=False)

    return {
        "filename": file.filename,
        "csv_data": csv_data
    }
