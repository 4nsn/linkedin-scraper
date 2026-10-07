import html
import os
import re
import time
import webbrowser
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}

# ---- Settings -------------------------------------------------------------
KEYWORDS = [
    # "Mechanical Engineer",
    "Junior Software Engineer",
    # "Full Stack Developer",
    # "Python Developer",
    # "cyber security analyst",
]

# Each location is either a geoId or a free-text location (+ optional distance in miles)
LOCATIONS = [
    {"name": "Manchester", "location": "Manchester, England, United Kingdom", "distance": 25},
    {"name": "United Kingdom", "geoId": 101165590},
]

DISTANCE = 25                # miles around each typed location
PAGES = 10                   # 10 jobs per page
SECONDS = 604800             # 3600 = last hour, 86400 = last 24 hours, 604800 = 1 week
EXPERIENCE_LEVEL = "2,3"     # "1" internship, "2" entry level, "3" associate, "2,3" both, or None
EXCLUDE_WORDS = ("senior", "lead", "principal", "staff", "manager", "head of")
# ---------------------------------------------------------------------------


def scrape_jobs(keywords, loc, pages=3, seconds=86400, experience=None):
    jobs = []
    for page in range(pages):
        params = {
            "keywords": keywords,
            "start": page * 10,
            "f_TPR": f"r{seconds}",
            "sortBy": "DD",
        }
        if "geoId" in loc:
            params["geoId"] = loc["geoId"]
        else:
            params["location"] = loc["location"]
            if loc.get("distance"):
                params["distance"] = loc["distance"]
        if experience:
            params["f_E"] = experience

        r = requests.get(BASE, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"  Stopped at page {page}: HTTP {r.status_code}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("li")
        if not cards:
            break

        for card in cards:
            title = card.find("h3", class_="base-search-card__title")
            company = card.find("h4", class_="base-search-card__subtitle")
            location = card.find("span", class_="job-search-card__location")
            link = card.find("a", class_="base-card__full-link")
            date = card.find("time")

            jobs.append({
                "title": title.get_text(strip=True) if title else None,
                "company": company.get_text(strip=True) if company else None,
                "location": location.get_text(strip=True) if location else None,
                "url": link["href"].split("?")[0] if link else None,
                "posted": date.get("datetime") if date else None,
            })
        time.sleep(3)
    return jobs


def scrape_many(keyword_list, locations, pages=3, seconds=86400, experience=None):
    seen = set()
    all_jobs = []
    for kw in keyword_list:
        for loc in locations:
            print(f"Searching: {kw} in {loc['name']}")
            for job in scrape_jobs(kw, loc, pages=pages, seconds=seconds, experience=experience):
                if job["url"] and job["url"] in seen:
                    continue
                seen.add(job["url"])
                job["search"] = f"{kw} / {loc['name']}"
                all_jobs.append(job)
    return all_jobs


def filter_jobs(jobs, exclude_words):
    return [
        j for j in jobs
        if j["title"] and not any(w in j["title"].lower() for w in exclude_words)
    ]


EXPERIENCE_NAMES = {
    "1": "Internship",
    "2": "Entry level",
    "3": "Associate",
    "2,3": "Entry level / Associate",
}


def describe_period(seconds):
    """Turn a number of seconds into text like 'last 1 hour' or 'last 24 hours'."""
    if seconds < 3600:
        n, unit = max(seconds // 60, 1), "minute"
    elif seconds < 86400:
        n, unit = seconds // 3600, "hour"
    else:
        n, unit = seconds // 86400, "day"
    return f"last {n} {unit}" + ("s" if n != 1 else "")


def make_filename(keywords):
    """Build a safe file name from the job titles, e.g. jobs_mechanical_engineer.html"""
    name = "_".join(keywords).lower()
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return f"jobs_{name}.html"


def save_html(jobs, keywords, locations, seconds, experience, filename):
    heading = html.escape(", ".join(keywords))
    where = html.escape(", ".join(l["name"] for l in locations))
    period = describe_period(seconds)
    level = EXPERIENCE_NAMES.get(experience)
    level_text = f" ({level})" if level else ""
    rows = ""
    for job in jobs:
        title = html.escape(job["title"] or "N/A")
        company = html.escape(job["company"] or "N/A")
        location = html.escape(job["location"] or "N/A")
        posted = html.escape(job["posted"] or "N/A")
        url = html.escape(job["url"] or "#")
        search = html.escape(job.get("search") or "")
        rows += f"""
        <tr>
            <td><a href="{url}" target="_blank">{title}</a></td>
            <td>{company}</td>
            <td>{location}</td>
            <td>{posted}</td>
            <td>{search}</td>
        </tr>"""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{heading} - Job Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2rem; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #0a66c2; color: white; }}
        tr:nth-child(even) {{ background: #f6f6f6; }}
        a {{ color: #0a66c2; text-decoration: none; }}
    </style>
</head>
<body>
    <h1>{heading}{level_text} jobs in {where}, {period} ({len(jobs)})</h1>
    <table>
        <tr><th>Title</th><th>Company</th><th>Location</th><th>Posted</th><th>Search</th></tr>
        {rows}
    </table>
</body>
</html>"""

    path = Path(filename).resolve()
    path.write_text(page, encoding="utf-8")
    print(f"Saved to: {path}")
    try:
        os.startfile(path)  # Windows
    except AttributeError:
        webbrowser.open(path.as_uri())  # macOS / Linux


def ask_locations():
    """Let the user type locations, e.g. 'Manchester, Leeds, London'. Blank = defaults."""
    print("Type any place in the world. Separate several with a semicolon (;).")
    print("Add the country to avoid mix-ups, e.g.  Berlin, Germany; Toronto, Canada; Dubai; Worldwide")
    raw = input("Locations (blank = defaults): ").strip()
    if not raw:
        return LOCATIONS
    locs = []
    for name in raw.split(";"):
        name = name.strip()
        if not name:
            continue
        low = name.lower()
        if low in ("uk", "united kingdom"):
            locs.append({"name": "United Kingdom", "geoId": 101165590})
        elif low in ("worldwide", "world", "global", "anywhere"):
            locs.append({"name": "Worldwide", "location": "Worldwide"})
        else:
            locs.append({"name": name, "location": name, "distance": DISTANCE})
    return locs or LOCATIONS


if __name__ == "__main__":
    LOCATIONS = ask_locations()
    results = scrape_many(KEYWORDS, LOCATIONS, pages=PAGES, seconds=SECONDS,
                          experience=EXPERIENCE_LEVEL)
    print(f"Found {len(results)} unique jobs")

    results = filter_jobs(results, EXCLUDE_WORDS)
    print(f"{len(results)} left after filtering out senior-level titles")

    for job in results:
        print(job["title"], "-", job["company"], "-", job["location"])

    save_html(results, KEYWORDS, LOCATIONS, SECONDS, EXPERIENCE_LEVEL, make_filename(KEYWORDS))