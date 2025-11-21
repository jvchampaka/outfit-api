import csv
import random
import re
import requests
from datetime import datetime
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Weather-Based Outfit Recommendation API")

# ==============================
# File Paths
# ==============================
DATASET_FILE = "Unstyled1.csv"
WEATHER_API_KEY = "e7b15095fe3450a04772a31d67478817"   # Your weather API key


# ==============================
# Load & Clean CSV
# ==============================
def load_dataset():
    outfits = []
    try:
        with open(DATASET_FILE, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                normalized_row = {}

                for k, v in row.items():
                    if not v:
                        continue

                    key = k.strip().lower()
                    value = v.strip()

                    # Convert Excel HYPERLINK to real URL
                    if value.startswith("=HYPERLINK"):
                        match = re.search(r'\"(https?://[^\"]+)\"', value)
                        if match:
                            value = match.group(1)

                    # Keep important columns only
                    if key in ["event", "season", "topwear", "bottomwear", "footwear", "accessories", "gender"]:
                        normalized_row[key] = value

                outfits.append(normalized_row)
    except Exception as e:
        print("Error loading dataset:", e)

    return outfits


DATASET = load_dataset()


# ==============================
# IP → City
# ==============================
def get_location():
    try:
        res = requests.get("https://ipinfo.io")
        return res.json().get("city")
    except:
        return None


# ==============================
# Weather → Season
# ==============================
def get_season_from_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url).json()
        temp = res["main"]["temp"]

        if temp >= 25:
            return "summer"
        elif temp <= 15:
            return "winter"
        else:
            return "rainy"
    except:
        return "summer"  # default


# ==============================
# Find Matching Outfits
# ==============================
def find_outfits(event, season):
    matches = []

    for row in DATASET:
        row_event = row.get("event", "").strip().lower()
        row_season = row.get("season", "").strip().lower()

        if event.lower() == row_event and season.lower() == row_season:
            matches.append(row)

    return matches


# ==============================
# FastAPI Routes
# ==============================
@app.get("/")
def home():
    return {"message": "Weather-Based Outfit Recommendation API is running!"}


@app.get("/suggest")
def suggest(event: str = Query(..., description="Type of event: office, party, trip, marriage, etc.")):
    # Step 1: Get city via IP
    city = get_location()
    if not city:
        season = "summer"  # fallback
    else:
        season = get_season_from_weather(city)

    # Step 2: Find matching outfits
    outfits = find_outfits(event, season)

    if not outfits:
        return {
            "success": False,
            "message": f"No outfits found for event '{event}' in season '{season}'.",
            "season_detected": season,
            "city_detected": city
        }

    # Step 3: Pick random outfit
    selected = random.choice(outfits)

    return {
        "success": True,
        "event": event,
        "season_detected": season,
        "city_detected": city,
        "outfit": selected
    }