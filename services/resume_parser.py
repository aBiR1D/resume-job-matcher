import json
import urllib3
import requests
import pdfplumber
from config import MODEL_API, MODEL_ID, USER_KEY

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EXTRACTION_PROMPT = """Analyze this resume and extract structured information as JSON. 
Return ONLY valid JSON with no extra text. Use this exact schema:

{
  "name": "Full name",
  "skills": ["skill1", "skill2"],
  "job_titles": ["most recent title", "previous title"],
  "experience_years": 5,
  "location": "City, Country",
  "summary": "2-3 sentence professional summary"
}

Rules:
- "skills" should include programming languages, frameworks, tools, and soft skills
- "job_titles" should list roles held, most recent first
- "experience_years" should be total professional experience (integer)
- If something is unclear or not found, use empty string or empty list

Resume text:
"""


def extract_text_from_pdf(pdf_file) -> str:
    """Extract raw text from an uploaded PDF file."""
    text_parts = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def parse_resume_with_claude(resume_text: str) -> dict:
    """Send resume text to Claude via Vertex AI gateway and get structured profile data."""
    url = f"{MODEL_API}/sonnet/models/{MODEL_ID}:streamRawPredict"

    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {USER_KEY}",
        },
        json={
            "anthropic_version": "vertex-2023-10-16",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": EXTRACTION_PROMPT + resume_text}],
                }
            ],
        },
        timeout=60,
        verify=False,
    )
    resp.raise_for_status()
    data = resp.json()

    response_text = data["content"][0]["text"]

    # Handle cases where Claude wraps JSON in markdown code blocks
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    return json.loads(response_text.strip())


def parse_resume(pdf_file) -> dict:
    """Full pipeline: PDF -> text -> structured profile."""
    raw_text = extract_text_from_pdf(pdf_file)
    if not raw_text.strip():
        raise ValueError("Could not extract any text from the PDF.")
    profile = parse_resume_with_claude(raw_text)
    return profile
