# backend.py
import json
import pandas as pd
import io
from fastapi import FastAPI, File, UploadFile
import uvicorn

# FastAPI backend
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

    # Initialize a dictionary to hold expanded lists for CSV conversion
    expanded_data = []

    # Process each field in the JSON and normalize it
    for idx in range(len(next(iter(json_data.values())))):  # Assuming all lists have the same length
        row = {}
        for key, value in json_data.items():
            if isinstance(value, list) and len(value) > idx:  # Ensure the index exists
                item = value[idx]
                if isinstance(item, dict):  # Flatten the dictionary
                    for sub_key, sub_value in item.items():
                        if isinstance(sub_value, dict):  # Handle nested dictionaries (like coordinates)
                            for coord_key, coord_value in sub_value.items():
                                row[f"{key}_{sub_key}_{coord_key}"] = coord_value
                        else:
                            row[f"{key}_{sub_key}"] = sub_value
                else:
                    row[key] = item
        expanded_data.append(row)

    # Convert the expanded data to a DataFrame
    try:
        df = pd.DataFrame(expanded_data)
    except ValueError as e:
        return {"error": f"Error creating DataFrame: {str(e)}"}

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

# Start FastAPI backend
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
