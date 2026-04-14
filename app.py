import streamlit as st
from services.resume_parser import parse_resume
from services.job_fetcher import fetch_all_jobs
from services.matcher import rank_jobs

st.set_page_config(page_title="Job Matcher", page_icon="🎯", layout="wide")

# ── Session state defaults ──────────────────────────────────────────────────

if "profile" not in st.session_state:
    st.session_state.profile = None

# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Job Matcher")
    st.caption("Upload your resume, find matching jobs")

    st.divider()

    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    if uploaded_file and st.button("Parse Resume", use_container_width=True):
        with st.spinner("Extracting profile with Claude..."):
            try:
                profile = parse_resume(uploaded_file)
                st.session_state.profile = profile
                st.success("Resume parsed!")
            except Exception as e:
                st.error(f"Failed to parse resume: {e}")

    # Show parsed profile
    if st.session_state.profile:
        st.divider()
        p = st.session_state.profile
        st.subheader(p.get("name", "Unknown"))
        st.write(f"**Experience:** {p.get('experience_years', '?')} years")
        st.write(f"**Location:** {p.get('location', 'Not specified')}")

        st.write("**Skills:**")
        skills = p.get("skills", [])
        if skills:
            # Render as comma-separated tags
            st.write(", ".join(f"`{s}`" for s in skills))

        st.write("**Past Titles:**")
        for title in p.get("job_titles", []):
            st.write(f"- {title}")

        # Let user add extra skills
        extra = st.text_input("Add more skills (comma-separated)")
        if extra:
            added = [s.strip() for s in extra.split(",") if s.strip()]
            current = st.session_state.profile.get("skills", [])
            st.session_state.profile["skills"] = list(
                dict.fromkeys(current + added)  # deduplicate, preserve order
            )

    st.divider()
    st.subheader("Search Filters")

    search_location = st.text_input(
        "Location",
        value=st.session_state.profile.get("location", "") if st.session_state.profile else "",
    )
    remote_only = st.checkbox("Remote only")
    min_match = st.slider("Minimum match %", 0, 100, 20)

    sources = st.multiselect(
        "Job sources",
        ["JSearch", "Jooble", "Adzuna", "RemoteOK"],
        default=["JSearch", "Jooble", "Adzuna", "RemoteOK"],
    )

    search_clicked = st.button("Search Jobs", type="primary", use_container_width=True,
                                disabled=st.session_state.profile is None)

# ── Main area ───────────────────────────────────────────────────────────────

if st.session_state.profile is None:
    st.markdown("## Welcome to Job Matcher")
    st.info("Upload your resume in the sidebar to get started. "
            "We'll parse your skills and find matching jobs from JSearch, Jooble, Adzuna, and RemoteOK.")
    st.stop()

if search_clicked:
    profile = st.session_state.profile
    skills = profile.get("skills", [])
    titles = profile.get("job_titles", [])

    # Build a search query from top skills + most recent title
    query_parts = titles[:1] + skills[:5]
    query = " ".join(query_parts)

    if not query.strip():
        st.warning("No skills or job titles found in your profile to search with.")
        st.stop()

    with st.spinner(f"Searching for jobs matching: _{query}_"):
        raw_jobs = fetch_all_jobs(query, search_location, remote_only, tuple(sources))

    if not raw_jobs:
        st.warning("No jobs found. Try adjusting your filters or adding more skills.")
        st.stop()

    ranked = rank_jobs(raw_jobs, profile)

    # Filter by minimum match score
    filtered = [j for j in ranked if j["match_score"] >= min_match]

    st.session_state.results = filtered
    st.session_state.query_used = query

# ── Display results ─────────────────────────────────────────────────────────

if "results" in st.session_state and st.session_state.results:
    results = st.session_state.results
    st.subheader(f"Found {len(results)} matching jobs")
    st.caption(f"Search query: {st.session_state.get('query_used', '')}")

    for job in results:
        with st.container(border=True):
            col_score, col_info, col_apply = st.columns([1, 5, 1.5])

            with col_score:
                score = job["match_score"]
                if score >= 70:
                    color = "green"
                elif score >= 40:
                    color = "orange"
                else:
                    color = "red"
                st.markdown(f"### :{color}[{score}%]")
                st.caption("match")

            with col_info:
                st.markdown(f"**{job['title']}**")
                st.write(f"🏢 {job['company']}  ·  📍 {job['location']}")
                if job["salary"] and job["salary"] != "Not specified":
                    st.write(f"💰 {job['salary']}")
                if job["posted"]:
                    st.caption(f"Posted: {job['posted']}  ·  Source: {job['source']}")
                else:
                    st.caption(f"Source: {job['source']}")

                with st.expander("Job description"):
                    st.write(job["description"] or "No description available.")

            with col_apply:
                st.write("")  # spacing
                if job["url"]:
                    st.link_button("Apply →", job["url"], use_container_width=True)

elif "results" in st.session_state:
    st.info("No jobs matched your minimum score filter. Try lowering the threshold.")
