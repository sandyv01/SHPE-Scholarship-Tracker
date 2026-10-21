# SHPE Scholarship Tracker

A Python-based scholarship tracker that scrapes [Scholarship360](https://scholarships360.org/) for scholarship opportunities and organizes them in Google Sheets for the SHPE (Society of Hispanic Professional Engineers) GroupMe community.

## Overview

The goal of this project is to help SHPE members discover scholarship opportunities by automating the process of finding, organizing, and sharing scholarships with students.

The scraper collects scholarship information from Scholarship360, filters opportunities based on configured eligibility criteria, and saves the results to a Google Sheet. A GroupMe bot then shares open scholarships with the SHPE community.

## Features

- **Automated scraping:** Collects scholarship opportunities from Scholarship360.
- **Google Sheets integration:** Organizes scholarship details in a centralized tracker.
- **Eligibility filtering:** Filters scholarships based on configured criteria, including location and student eligibility.
- **Deadline tracking:** Tracks deadlines and identifies open, upcoming, and closed opportunities.
- **Manual approval:** Allows scholarships to be reviewed before being shared.
- **GroupMe integration:** Posts eligible scholarships to the SHPE GroupMe.
- **Duplicate prevention:** Tracks previously posted scholarships to avoid repeatedly sharing the same opportunities.
- **Scheduled execution:** Supports automated daily runs through GitHub Actions.

## Tech Stack

- **Python** — scraping and automation
- **Requests** — retrieving webpage content and communicating with APIs
- **Beautiful Soup** — parsing scholarship webpages
- **gspread** — Google Sheets integration
- **Google Sheets** — scholarship database and approval tracker
- **GroupMe Bot API** — posting scholarship opportunities
- **GitHub Actions** — scheduled automation

## Project Structure

```text
.
├── she2.py                       # Scholarship scraper and Sheets updater
├── groupmeBot2.py                # GroupMe posting bot
├── requirements.txt              # Python dependencies
├── .gitignore                    # Excludes secrets and local files
└── .github/
    └── workflows/
        └── daily-scholarships.yml # Scheduled automation
```

## How It Works

1. **Scrape:** Retrieve scholarship listings from selected Scholarship360 pages.
2. **Filter:** Evaluate scholarships using configured criteria and deadline rules.
3. **Store:** Add or update scholarship information in Google Sheets.
4. **Review:** Review opportunities and mark scholarships as approved.
5. **Share:** The GroupMe bot posts eligible, approved scholarships that have not already been posted.
6. **Track:** Update the spreadsheet to record posted scholarships and prevent duplicate announcements.

## Google Sheets

The spreadsheet serves as the central database for scholarship opportunities. Depending on the current scraper configuration, columns can include:

| Column | Purpose |
|---|---|
| Name | Scholarship name |
| Value | Award amount |
| Deadline | Application deadline |
| Description | Scholarship details |
| Link | Application or information URL |
| Status | Deadline-based status |
| Location-Based Flags | Eligibility or category labels |
| Posted | Whether it has been posted to GroupMe |

## Setup

### Prerequisites

- Python 3.9 or newer
- A Google Cloud service account with Google Sheets API access
- A Google spreadsheet shared with the service account as an editor
- A GroupMe bot created for the SHPE group
- A GitHub repository for scheduled execution (optional)

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY_NAME
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` file should include:

```text
requests
beautifulsoup4
gspread
python-dotenv
```

### 3. Configure credentials

For local development, configure the required environment variables and Google service-account credentials.

Example `.env` file:

```env
SPREADSHEET_ID=your_google_spreadsheet_id
WORKSHEET_NAME=Scholarships
GROUPME_BOT_ID=your_groupme_bot_id
```

Place your Google service-account JSON credentials in the location expected by the scripts, such as `credentials.json`.

**Security:** Never commit `.env`, `*.env`, `credentials.json`, GroupMe bot IDs, or other secrets to GitHub.

### 4. Run the scraper

```bash
python she2.py
```

This retrieves scholarship listings and updates the Google Sheet.

### 5. Run the GroupMe bot

```bash
python groupmeBot2.py
```

This checks the spreadsheet for scholarships eligible to be shared and posts them to the SHPE GroupMe according to the bot's configured posting rules.

## Automated Workflow

The project can use GitHub Actions to run the scraper and GroupMe bot on a daily schedule.

Configure the following repository secrets under **Settings → Secrets and variables → Actions**:

- `SPREADSHEET_ID`
- `WORKSHEET_NAME`
- `GROUPME_BOT_ID`
- `GOOGLE_CREDENTIALS_JSON` — the complete Google service-account JSON

The workflow installs dependencies, configures credentials, runs the scraper, and then runs the GroupMe bot.

You can also trigger the workflow manually from the **Actions** tab if `workflow_dispatch` is enabled.

## Data and Usage Notes

- Scholarship listings and eligibility requirements may change. Verify application details on the scholarship provider's website before applying.
- Review opportunities before posting them to the SHPE community.
- Scraping should follow Scholarship360's applicable terms, access restrictions, and rate limits.
- Keep credentials private and grant the Google service account access only to the spreadsheet it needs.

## Purpose

This project aims to make scholarship discovery easier for SHPE members by reducing manual searching and providing a centralized, automated way to distribute opportunities to students.

