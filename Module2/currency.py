import os
import requests
import json
import requests
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.exchangerate.host/live"
TARGET_CURRENCIES = ["ETB", "EUR", "GBP"]
CSV_FILE = "currency_exchange_rates.csv"

def fetch_currency():
    params = {
            "access_key":API_KEY,
        }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching currency data: {e}")
        return None   

def transform_currency_data(data):
    rows = []

    api_timestamp = data.get("timestamp")
    formatted_time = datetime.fromtimestamp(api_timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    quotes = data.get("quotes", {})
    for key, value in quotes.items():
        # convert key from 'USDEUR' format to 'EUR' format
        currency = key.replace("USD", "")

        if currency in TARGET_CURRENCIES:
            rows.append([formatted_time, currency, value])

    return rows


def write_to_csv(rows):
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)

        # write header first time only
        if not file_exists:
            writer.writerow(["timestamp", "currency", "rate"])

        writer.writerows(rows)

def main():
    data = fetch_currency()
    if not data:
        return

    rows = transform_currency_data(data)
    write_to_csv(rows)


if __name__ == "__main__":
    main()
