# resume-job-matcher

Upload your resume, get matched jobs. Parses your resume with Claude and ranks jobs from multiple boards by how well they fit your skills, titles, and location.

## Sources

- **JSearch** (via RapidAPI) -- aggregates LinkedIn, Indeed, Glassdoor
- **Jooble** -- 70+ countries
- **Adzuna** -- 16 countries
- **RemoteOK** -- remote-only jobs, no API key needed

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill in your API keys in `.env`:

| Variable | Where to get it |
|---|---|
| `MODEL_API` | Your Claude API gateway URL |
| `MODEL_ID` | Claude model ID (e.g. `claude-sonnet-4@20250514`) |
| `USER_KEY` | Your API key for the Claude gateway |
| `JSEARCH_API_KEY` | [RapidAPI - JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) |
| `JOOBLE_API_KEY` | [Jooble API](https://jooble.org/api/about) |
| `ADZUNA_APP_ID` | [Adzuna API](https://developer.adzuna.com/) |
| `ADZUNA_APP_KEY` | Same as above |

You don't need all of them -- the app skips any source with missing keys.

## Run

```bash
streamlit run app.py
```

Then:
1. Upload your resume (PDF) in the sidebar
2. It gets parsed into skills, titles, location
3. Hit **Search Jobs** -- results are ranked by match score
4. Click **Apply** to go to the job posting

## How matching works

Each job gets a score out of 100:
- **Skills overlap** -- up to 60 points
- **Job title similarity** -- up to 25 points
- **Location match** -- up to 15 points

## License

MIT
