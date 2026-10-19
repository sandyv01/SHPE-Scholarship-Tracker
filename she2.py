from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from pathlib import Path
import requests
import gspread
import re
import time
from dotenv import load_dotenv
import os

#websites used :p
URLS = [
    "https://scholarships360.org/scholarships/top-scholarships-for-college-students//",
    "https://scholarships360.org/scholarships/top-scholarships-for-college-students/?sidebar_sort=relevant&current_page=1&filter=minority",
]

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / "poop.env")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "").strip()

#timeframe for accepted scholarships
START_DATE = datetime(2026, 10, 15).date()
END_DATE = datetime(2027, 6, 1).date()

#headers for google sheets
HEADERS = [
    "Name", "Value", "Deadline", "Description", "Link", "Status",
    "Location-Based FLags", "Posted",
]
POSTED_COL = HEADERS.index("Posted")

AUTO_SKIP_FLAGS = set()

STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming", "District of Columbia",
]

#takes sheets value and turns into bool
def to_bool(value):
    return str(value).strip().upper() == "TRUE"

def detect_flags(text):
    low = text.lower()
    flags = []

    mentioned_states = [
        state for state in STATES
        if re.search(rf"\b{re.escape(state)}\b", text, re.IGNORECASE)
    ]

    if mentioned_states:
        flags.append("Location: " + ", ".join(mentioned_states[:5]))

    return "; ".join(flags)

#connecting to sheets
credentials_file = Path(__file__).with_name("credentials.json")
client = gspread.service_account(filename=str(credentials_file))

if not SPREADSHEET_ID:
    raise RuntimeError("SPREADSHEET_ID is missing from your .env file.")

WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Scholarships")

spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet(WORKSHEET_NAME)

#reading existing data
existing_data = sheet.get_all_values()

#creating header IF it is empty 
if not existing_data:
    sheet.update(values=[HEADERS], range_name="A1")
    existing_data = [HEADERS]

#map existing scholarships by name
headers = existing_data[0]
existing_scholarships = {}

for row in existing_data[1:]:
    row = row + [""] * (len(headers) - len(row))
    record = dict(zip(headers, row))

    name = record.get("Name", "").strip()
    if name:
        existing_scholarships[name] = [
            record.get("Name", ""),
            record.get("Value", ""),
            record.get("Deadline", ""),
            record.get("Description", ""),
            record.get("Link", ""),
            record.get("Status", "Open"),
            "",  # Flags are recalculated below
            to_bool(record.get("Posted", "")),
        ]

#scholarship tracking
scholarships = []

for url in URLS:
    print(f"\nScraping: {url}") #for debugging purposes

    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status() #checks HTTP response status

    soup = BeautifulSoup(response.text, "html.parser")
    page_scholarships = soup.select("div.re-scholarship-card")

    print(f"Found {len(page_scholarships)} scholarship cards.") #for debugging purpose

    #saving source url for that specific card
    for card in page_scholarships:
        scholarships.append((card, url))
    
    #pause break :]
    time.sleep(3)

print(f"\nTotal cards collected: {len(scholarships)}")

#runtime error catch in case of website html changes
if not scholarships:
    raise RuntimeError(
        "No Scholarships360 cards found. "
        "Check the page URL or CSS selectors. Spreadsheet was not updated."
    )

today = datetime.now().date()
original_names = set(existing_scholarships)

#purely debugging info
skip_counts = {}
def log_skip(reason, name, source_url, details=""):
    skip_counts[reason] = skip_counts.get(reason, 0) + 1
    print(f"SKIPPED [{reason}] {name or '(unknown title)'}"
          f" | {details} | Source: {source_url}")

for s, source_url in scholarships:
    title_link = s.select_one("h4 a[href]")
    if not title_link:
        print("Could not find title link. Card HTML:")
        print(s.prettify()[:1500])
        log_skip("missing title link", "(unknown title)", source_url)
        continue

    name = title_link.get_text(strip=True)
    link = urljoin(source_url, title_link["href"])

    #remove verification tooltip
    tooltip = title_link.select_one(".re-verified_title-tooltip")
    if tooltip:
        tooltip.decompose()
    name = title_link.get_text(" ", strip=True)
 
    value = ""
    deadline_text = ""

    for info in s.select(".re-scholarship-card-info"):
        label = info.select_one(".re-scholarship-card-info-name")
        field_value = info.select_one(".re-scholarship-card-info-value")

        if not label or not field_value:
            continue

        label_text = label.get_text(" ", strip=True).lower()
        field_text = field_value.get_text(" ", strip=True)

        if "award worth" in label_text:
            value = field_text
        elif "deadline" in label_text:
            deadline_text = field_text

    #try mobile if not foundin desktop version
    if not deadline_text:
        for info in s.select(".re-scholarship-card-info_mob"):
            label = info.select_one(".re-scholarship-card-info_mob-name")
            field_value = info.select_one(".re-scholarship-card-info_mob-value")
            if label and field_value and "deadline" in label.get_text(" ", strip=True).lower():
                deadline_text = field_value.get_text(" ", strip=True)
                break

    desc_tag = s.select_one(".re-scholarship-card-main-hidden .re-text p")
    if not desc_tag:
        desc_tag = s.select_one(".re-scholarship-card-main .re-text p")

    description = desc_tag.get_text(" ", strip=True) if desc_tag else ""

    #SKIP IF NO TITLE for the scholarship
    if not name:
        continue

    #deadline reformatted
    match = re.search(
    r"([A-Za-z]{3,9} \d{1,2}, \d{4})",
    deadline_text
)
    #if deadline not found
    if not match:
        log_skip("unrecognized deadline", name, source_url, deadline_text)
        continue

    deadline = None
    for date_format in ("%b %d, %Y", "%B %d, %Y"):
        try:
            deadline = datetime.strptime(
                match.group(1), date_format
            ).date()
            break
        except ValueError:
            pass

    if deadline is None:
        log_skip("invalid deadline", name, source_url, deadline_text)
        continue

    #apply the date window
    if name not in existing_scholarships:
        if not START_DATE <= deadline <= END_DATE:
            log_skip("outside date window", name, source_url, str(deadline))
            continue
    elif deadline > END_DATE:
        log_skip("existing deadline after end date", name, source_url, str(deadline))
        continue

    flags = detect_flags(f"{name} {description}")

    days_left = (deadline - today).days
    if days_left < 0:
        status = "Past Due"
    elif days_left <= 7:
        status = "Upcoming Deadline"
    else:
        status = "Open"

    if name in existing_scholarships:
        already_posted = existing_scholarships[name][POSTED_COL]
    else:
        already_posted = False

    existing_scholarships[name] = [
        name,
        value,
        deadline_text,
        description,
        link,
        status,
        flags,
        already_posted,
    ]

    print(f"Updated: {name} — {status}" + (f" [{flags}]" if flags else ""))

#keep existing scholarships and add new ones
rows = [HEADERS] + list(existing_scholarships.values())

#check for needed space
needed_rows = max(sheet.row_count, len(rows) + 100)
needed_cols = max(sheet.col_count, len(HEADERS))
if (needed_rows, needed_cols) != (sheet.row_count, sheet.col_count):
    sheet.resize(rows=needed_rows, cols=needed_cols)

# Update the sheet without clearing it
sheet.update(
    values=rows,
    range_name="A1",
    value_input_option="USER_ENTERED",
)

print("\n--- Skip summary ---")
for reason, count in skip_counts.items():
    print(f"{reason}: {count}")
    
print(f"\nTotal scholarships saved: {len(rows) - 1}")
print(
    f"New scholarships added: "
    f"{len(set(existing_scholarships) - original_names)}"
)