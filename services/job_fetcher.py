import requests
import streamlit as st
from config import JSEARCH_API_KEY, JOOBLE_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY


def _normalize(title="", company="", location="", salary="", description="",
               url="", source="", posted=""):
    """Normalize a job into a common schema."""
    return {
        "title": title or "N/A",
        "company": company or "N/A",
        "location": location or "N/A",
        "salary": salary or "Not specified",
        "description": description or "",
        "url": url or "",
        "source": source,
        "posted": posted or "",
    }


# ---------------------------------------------------------------------------
# JSearch (RapidAPI) -- aggregates LinkedIn, Indeed, Glassdoor, etc.
# ---------------------------------------------------------------------------

def _fetch_jsearch(query: str, location: str, remote_only: bool) -> list[dict]:
    if not JSEARCH_API_KEY:
        return []

    params = {
        "query": f"{query} in {location}" if location else query,
        "num_pages": "1",
    }
    if remote_only:
        params["remote_jobs_only"] = "true"

    try:
        resp = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={
                "X-RapidAPI-Key": JSEARCH_API_KEY,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
            },
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception:
        return []

    jobs = []
    for item in data:
        salary_parts = []
        if item.get("job_min_salary"):
            salary_parts.append(str(int(item["job_min_salary"])))
        if item.get("job_max_salary"):
            salary_parts.append(str(int(item["job_max_salary"])))
        salary = " - ".join(salary_parts) if salary_parts else ""
        if salary and item.get("job_salary_currency"):
            salary = f"{item['job_salary_currency']} {salary}"

        jobs.append(_normalize(
            title=item.get("job_title"),
            company=item.get("employer_name"),
            location=item.get("job_city") or item.get("job_country"),
            salary=salary,
            description=item.get("job_description", "")[:500],
            url=item.get("job_apply_link") or item.get("job_google_link"),
            source="JSearch",
            posted=item.get("job_posted_at_datetime_utc", "")[:10],
        ))
    return jobs


# ---------------------------------------------------------------------------
# Jooble -- free API, 70+ countries
# ---------------------------------------------------------------------------

def _fetch_jooble(query: str, location: str, _remote_only: bool) -> list[dict]:
    if not JOOBLE_API_KEY:
        return []

    payload = {"keywords": query, "location": location or ""}

    try:
        resp = requests.post(
            f"https://jooble.org/api/{JOOBLE_API_KEY}",
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("jobs", [])
    except Exception:
        return []

    jobs = []
    for item in data:
        jobs.append(_normalize(
            title=item.get("title"),
            company=item.get("company"),
            location=item.get("location"),
            salary=item.get("salary"),
            description=(item.get("snippet") or "")[:500],
            url=item.get("link"),
            source="Jooble",
            posted=item.get("updated", "")[:10],
        ))
    return jobs


# ---------------------------------------------------------------------------
# Adzuna -- free tier, 16 countries
# ---------------------------------------------------------------------------

ADZUNA_COUNTRY_MAP = {
    "india": "in", "us": "us", "usa": "us", "uk": "gb", "united kingdom": "gb",
    "canada": "ca", "australia": "au", "germany": "de", "france": "fr",
    "netherlands": "nl", "brazil": "br", "poland": "pl", "russia": "ru",
    "south africa": "za", "new zealand": "nz", "singapore": "sg", "italy": "it",
}


def _guess_adzuna_country(location: str) -> str:
    loc_lower = location.lower().strip()
    for keyword, code in ADZUNA_COUNTRY_MAP.items():
        if keyword in loc_lower:
            return code
    return "in"  # default to India


def _fetch_adzuna(query: str, location: str, _remote_only: bool) -> list[dict]:
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return []

    country = _guess_adzuna_country(location)
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 20,
        "what": query,
    }
    if location:
        params["where"] = location

    try:
        resp = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("results", [])
    except Exception:
        return []

    jobs = []
    for item in data:
        salary = ""
        if item.get("salary_min") and item.get("salary_max"):
            salary = f"{int(item['salary_min'])} - {int(item['salary_max'])}"
        elif item.get("salary_min"):
            salary = f"From {int(item['salary_min'])}"

        jobs.append(_normalize(
            title=item.get("title"),
            company=item.get("company", {}).get("display_name"),
            location=item.get("location", {}).get("display_name"),
            salary=salary,
            description=(item.get("description") or "")[:500],
            url=item.get("redirect_url"),
            source="Adzuna",
            posted=item.get("created", "")[:10],
        ))
    return jobs


# ---------------------------------------------------------------------------
# RemoteOK -- free, no auth, remote jobs only
# ---------------------------------------------------------------------------

def _fetch_remoteok(query: str, _location: str, _remote_only: bool) -> list[dict]:
    try:
        resp = requests.get(
            "https://remoteok.com/api",
            headers={"User-Agent": "JobMatcherApp/1.0"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    # First element is metadata, skip it
    if data and isinstance(data[0], dict) and "id" not in data[0]:
        data = data[1:]

    query_terms = set(query.lower().split())
    jobs = []
    for item in data:
        text = f"{item.get('position', '')} {item.get('description', '')} {' '.join(item.get('tags', []))}".lower()
        if not query_terms or any(term in text for term in query_terms):
            salary = item.get("salary") or ""

            jobs.append(_normalize(
                title=item.get("position"),
                company=item.get("company"),
                location="Remote",
                salary=salary,
                description=(item.get("description") or "")[:500],
                url=item.get("url"),
                source="RemoteOK",
                posted=item.get("date", "")[:10],
            ))

    return jobs[:20]


# ---------------------------------------------------------------------------
# Unified fetch -- cached for 1 hour
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_jobs(query: str, location: str, remote_only: bool,
                   sources: tuple) -> list[dict]:
    """Fetch jobs from all enabled sources and return a combined list."""
    all_jobs = []

    fetchers = {
        "JSearch": _fetch_jsearch,
        "Jooble": _fetch_jooble,
        "Adzuna": _fetch_adzuna,
        "RemoteOK": _fetch_remoteok,
    }

    for source_name, fetcher_fn in fetchers.items():
        if source_name in sources:
            all_jobs.extend(fetcher_fn(query, location, remote_only))

    return all_jobs
