import os
from pathlib import Path
import time
import random

import gspread
import requests
from dotenv import load_dotenv

WORKSHEET_NAME = "Scholarships"

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

load_dotenv(BASE_DIR / "poop.env")
BOT_ID = os.getenv("GROUPME_BOT_ID", "").strip()

if not BOT_ID:
    raise RuntimeError("Set GROUPME_BOT_ID in your .env file.")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "").strip()

#connecting to google sheets
client = gspread.service_account(filename=str(CREDENTIALS_FILE))
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet(WORKSHEET_NAME)

data = sheet.get_all_values()

if not data:
    raise RuntimeError("The Scholarships sheet is empty.")

headers = data[0]

#posted should exist, if not add
if "Posted" not in headers:
    posted_col = len(headers) + 1
    sheet.update_cell(1, posted_col, "Posted")
    headers = sheet.row_values(1)
else:
    posted_col = headers.index("Posted") + 1

#refresh data if posted header had to be added
data = sheet.get_all_values()
headers = data[0]
posted_col = headers.index("Posted") + 1

posted_count = 0
skipped_count = 0

for row_number, row in enumerate(data[1:], start=2):
    row = row + [""] * (len(headers) - len(row))
    record = dict(zip(headers, row))

    name = str(record.get("Name", "")).strip()
    status = str(record.get("Status", "")).strip()
    posted_status = str(record.get("Posted", "")).strip().upper()

    if not name:
        continue

    if posted_status in {"TRUE", "YES", "1"}:
        print(f"Already posted, skipping: {name}")
        skipped_count += 1
        continue

    if status not in {"Open", "Upcoming Deadline"}:
        print(f"Inactive scholarship, skipping: {name}")
        skipped_count += 1
        continue

    value = str(record.get("Value", "")).strip()
    deadline = str(record.get("Deadline", "")).strip()
    description = str(record.get("Description", "")).strip()
    link = str(record.get("Link", "")).strip()

    if len(description) > 250:
        description = description[:247] + "..."

    #the message
    message_parts = [
        "Scholarship Opportunity!📚",
        "",
        name,
        f"Award: {value or 'Not listed'}",
        f"Deadline: {deadline or 'Not listed'}",
        f"Status: {status}",
    ]

    if description:
        message_parts.extend(["", description])

    if link:
        message_parts.extend(["", f"Apply here: {link}"])

    message = "\n".join(message_parts)

    #post
    response = requests.post(
        "https://api.groupme.com/v3/bots/post",
        json={"bot_id": BOT_ID, "text": message},
        timeout=30,
    )

    #check is successful post
    if response.status_code != 202:
        print(
            f"POST FAILED: {name} "
            f"({response.status_code}): {response.text}"
        )
        skipped_count += 1
        continue

    #update sheets with checkmark under posted
    sheet.update_cell(row_number, posted_col, True)

    posted_count += 1
    print(f"Posted and checked checkbox: {name}")

#debugging info
print("\nFinished!")
print(f"New scholarships posted: {posted_count}")
print(f"Scholarships skipped or failed: {skipped_count}")