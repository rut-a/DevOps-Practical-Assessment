# Module 2: Mini-ETL Pipeline (Currency Exchange System)

## Overview

This project is a simple ETL pipeline that fetches real-time currency exchange rates from a public API, filters specific currencies, transforms the data into a structured format, and stores it in a CSV file. Free version of the public currency exchange APIs don't allow custom base currency query. So I used the default base currency USD.

The pipeline is also automated with systemd timers.

# Project Architecture

The pipeline follows this flow:

API (Exchange Rate Source)
→ Python ETL Script (Extract + Transform)
→ CSV File (Load)
→ systemd Timer (Hourly Automation)


# 1. Environment Setup

## Create project directory

mkdir Module2
cd Module2


## Create and activatevirtual environment

python3 -m venv venv
source venv/bin/activate


## Install dependencies

pip install requests python-dotenv


# 2. Freeze dependencies

pip freeze > requirements.txt


# 3. Environment variables (.env setup)

Create .env:

API_KEY=your_api_key_here

The script loads it using dotenv.


# 4. Currency Exchange Script Breakdown

### Section 1 — Imports & Constants

```python
import os
import requests
import json
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.exchangerate.host/live"
TARGET_CURRENCIES = ["ETB", "EUR", "GBP"]
CSV_FILE = "currency_exchange_rates.csv"
```

I import:

- `os` to access environment variables
- `requests` to make HTTP requests to the currency API
- `json` for handling JSON data
- `csv` for writing transformed data into a CSV file
- `datetime` for formatting timestamps returned by the API
- `load_dotenv()` to load variables from the `.env` file

The constants define:

| Constant | Purpose |
|---|---|
| `API_KEY` | API authentication key loaded from `.env` |
| `BASE_URL` | Currency exchange API endpoint |
| `TARGET_CURRENCIES` | List of currencies to filter |
| `CSV_FILE` | Output CSV file name |


### Section 2 — `fetch_currency()`: Extract Phase

```python
def fetch_currency():
    params = {
        "access_key": API_KEY,
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching currency data: {e}")
        return None
```

This function handles the extraction phase of the ETL pipeline.

1. **Prepare API parameters** — the API key is passed through the `params` dictionary.
2. **Send HTTP request** — `requests.get()` sends a GET request to the exchange rate API.
3. **Validate response** — `raise_for_status()` throws an exception if the request fails.
4. **Return JSON data** — successful responses are converted into Python dictionaries using `response.json()`.
5. **Handle failures** — any request-related exception is caught and logged, and the function returns `None`.


### Section 3 — `transform_currency_data()`: Transform Phase

```python
def transform_currency_data(data):
    rows = []

    api_timestamp = data.get("timestamp")

    formatted_time = (
        datetime.fromtimestamp(api_timestamp)
        .strftime("%Y-%m-%d %H:%M:%S")
    )

    quotes = data.get("quotes", {})

    for key, value in quotes.items():

        currency = key.replace("USD", "")

        if currency in TARGET_CURRENCIES:
            rows.append([
                formatted_time,
                currency,
                value
            ])

    return rows
```

This function transforms the raw API response into a flat CSV-ready structure.

1. **Extract timestamp** — the Unix timestamp from the API response is retrieved.
2. **Format timestamp** — `datetime.fromtimestamp()` converts the Unix timestamp into a human-readable format.
3. **Extract currency quotes** — the `quotes` dictionary contains exchange rate mappings such as `USDEUR`.
4. **Clean currency codes** — `"USD"` is removed from keys like `USDEUR` to get `EUR`.
5. **Filter target currencies** — only currencies listed in `TARGET_CURRENCIES` are kept.
6. **Prepare rows** — each filtered currency is stored as a CSV row containing timestamp, currency, and rate.


### Section 4 — `write_to_csv()`: Load Phase

```python
def write_to_csv(rows):
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "currency",
                "rate"
            ])

        writer.writerows(rows)
```

This function handles the load phase by storing transformed data into a CSV file.

1. **Check if file exists** — `os.path.isfile()` determines whether the CSV file already exists.
2. **Open file in append mode** — `"a"` mode ensures new data is added without overwriting existing records.
3. **Write header once** — the CSV header is only written if the file does not already exist.
4. **Write transformed rows** — all transformed currency rows are appended to the CSV file.


### Section 5 — `main()`: Pipeline Orchestration

```python
def main():
    data = fetch_currency()

    if not data:
        return

    rows = transform_currency_data(data)

    write_to_csv(rows)


if __name__ == "__main__":
    main()
```

This section coordinates the full ETL workflow.

1. **Run extraction** — `fetch_currency()` retrieves raw currency data from the API.
2. **Validate response** — the script exits early if the API request fails.
3. **Run transformation** — `transform_currency_data()` filters and restructures the data.
4. **Run load phase** — `write_to_csv()` stores the final output into the CSV file.
5. **Entry point protection** — `if __name__ == "__main__":` ensures the script only runs when executed directly.

# 5. systemd Service

### I created a service file that runs the currency.py script

/etc/systemd/system/currency.service

[Unit]
Description=Currency Exchange ETL Pipeline
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/Module2/
ExecStart=/home/ubuntu/Module2/venv/bin/python /home/ubuntu/Module2/currency.py

# 6. systemd Timer

### I created a persistent systemd timer that runs currency.service every hour.

/etc/systemd/system/currency.timer

[Unit]
Description=Run currency ETL every hour

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target


# 7. Enable timer

sudo systemctl daemon-reload

sudo systemctl enable currency.timer

sudo systemctl start currency.timer


# 8. Verify

systemctl list-timers
journalctl -u currency.service


# 9. Sample Output

timestamp,currency,rate

2026-05-16 15:07:07,ETB,156.447426

2026-05-16 15:07:07,EUR,0.860404

2026-05-16 15:07:07,GBP,0.750272



