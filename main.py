import os
import random
import csv
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# CSV file
DATA_CSV = "Unstyled1.csv"

app = FastAPI(title="Outfit Suggestion API")

# -----------------------
# Load the CSV file
# -----------------------
def load_csv(csv_path):
    outfits = []
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                outfits.append(row)
    except Exception as e:
        print("Error loading CSV:", e)
    return outfits

@app.on_event("startup")
def startup_event():
    global OUTFITS
    OUTFITS = load_csv(DATA_CSV)
    print(f"Loaded {len(OUTFITS)} outfits from CSV.")

# -----------------------
# Request Model
# -----------------------
class SuggestRequest(BaseModel):
    event: str
    season: Optional[str] = None

# -----------------------
# Filtering Function (CLEANED)
# -----------------------
def filter_outfits(event, season=None):
    event = event.lower().strip()
    season = season.lower().strip() if season else None

    results = []

    for row in OUTFITS:
        # Clean and normalize text
        event_col = str(row.get("Event") or "").lower().strip()
        season_col = str(row.get("season") or "").lower().strip()

        # Remove leftover characters from HYPERLINK()
        event_col = event_col.replace('")', '').replace('"', '')
        season_col = season_col.replace('")', '').replace('"', '')

        # Match event & season
        if event in event_col:
            if season:
                if season in season_col:
                    results.append(row)
            else:
                results.append(row)

    return results

# -----------------------
# API Endpoints
# -----------------------
@app.get("/")
def home():
    return {"message": "Outfit Suggestion API working!"}

@app.get("/suggest")
def suggest(event: str, season: Optional[str] = None):
    matches = filter_outfits(event, season)
    if not matches:
        return {"found": False, "message": "No matching outfits"}
    return {"found": True, "outfit": random.choice(matches)}

@app.post("/suggest")
def suggest_post(req: SuggestRequest):
    matches = filter_outfits(req.event, req.season)
    if not matches:
        return {"found": False, "message": "No matching outfits"}
    return {"found": True, "outfit": random.choice(matches)}

# -----------------------
# Local Run
# -----------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
