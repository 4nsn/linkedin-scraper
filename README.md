# LinkedIn Job Scraper

A small Python script that searches LinkedIn's public job listings for the job titles you choose and saves the results as an HTML page that opens in your browser.

## Features

- Search one or more job titles in one run
- Filter by UK location, experience level and how recently the job was posted
- Remove senior-level titles automatically (senior, lead, manager, etc.)
- Removes duplicate listings
- Saves a clean results table, named after the job title (e.g. `jobs_mechanical_engineer.html`)

## Requirements

- Python 3.9 or newer
- The `requests` and `beautifulsoup4` packages

## Setup

```
pip install requests beautifulsoup4
```

## Usage

1. Open `linkedin.py` and edit the settings near the top:

   ```python
   KEYWORDS = [
       "Mechanical Engineer",
       # "Full Stack Developer",
   ]
   GEO_ID = 101165590          # United Kingdom
   PAGES = 10                   # 10 jobs per page
   SECONDS = 86400             # 3600 = last hour, 86400 = last 24 hours,604800 = 1 week
   EXPERIENCE_LEVEL = "2"      # "1" internship, "2" entry level, "3" associate, or None
   EXCLUDE_WORDS = ("senior", "lead", "principal", "staff", "manager", "head of")
   ```

2. Run the script:

   ```
   python linkedin.py
   ```

3. The results page is saved in the same folder and opens automatically.

## Settings

| Setting | What it does |
| --- | --- |
| `KEYWORDS` | Job titles to search. Remove the `#` to turn one on, add `#` to turn it off. |
| `GEO_ID` | LinkedIn location ID. `101165590` is the United Kingdom. |
| `PAGES` | Number of result pages to fetch, 10 jobs each. |
| `SECONDS` | Only show jobs posted within this many seconds. |
| `EXPERIENCE_LEVEL` | `"1"` internship, `"2"` entry level, `"3"` associate, or `None` for all. |
| `EXCLUDE_WORDS` | Jobs with any of these words in the title are removed. |

## Notes

- This uses LinkedIn's public guest endpoint, so no login is needed. LinkedIn may change it or limit requests at any time.
- Use it sparingly and check LinkedIn's terms of use before relying on it.
- Generated `jobs*.html` files are ignored by Git and are not uploaded.
