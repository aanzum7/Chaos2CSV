import json
import pandas as pd
import io
from fastapi import FastAPI, File, UploadFile, HTTPException
import uvicorn

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

        # 🔹 Handle dictionary with lists as values
        if isinstance(json_data, dict):
            if all(isinstance(v, list) for v in json_data.values()):  
                if not any(json_data.values()):  # Ensure lists are non-empty
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

        # 🔹 Handle standard JSON array format
        elif isinstance(json_data, list):
            if all(isinstance(entry, dict) for entry in json_data):  
                expanded_data = [flatten_json(entry) for entry in json_data]
            else:
                raise HTTPException(status_code=400, detail="Each JSON entry must be a dictionary.")

        # 🔹 Convert to DataFrame
        df = pd.DataFrame(expanded_data).fillna('*')

        # 🔹 Convert to CSV (UTF-8 for Bangla & other languages)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')

        return {"filename": file.filename, "csv_data": csv_buffer.getvalue()}

    except HTTPException:
        raise  # Re-raise known HTTP errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
