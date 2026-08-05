import streamlit as st
import json
from auth.session import SessionManager
from db.sqlite import init_db
from db.repository import Repository
from graph.workflow import create_workflow
from agent.career_intelligence import generate_career_intelligence, format_intelligence_report

# Initialize Database
init_db()

# --- Page Config ---
st.set_page_config(page_title="AI Job Search Agent", page_icon="🤖", layout="wide")

repo = Repository()
app = create_workflow()

# --- Helper functions ---
def load_profile(user_id):
    """Load existing profile from database."""
    return repo.get_profile(user_id)

def save_profile_to_db(user_id, data):
    """Save profile to database."""
    repo.save_profile(
        user_id,
        data.get("cv", {}),
        data.get("prefs", {}),
        data.get("identity", {})
    )

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Configuration")
    
    user_id = st.text_input("User ID", value="user_1", help="Your unique identifier")
    
    # Load existing profile
    existing_profile = load_profile(user_id)
    existing_identity = existing_profile.get("identity", {})
    existing_cv = existing_profile.get("cv", {})
    existing_prefs = existing_profile.get("prefs", {})
    
    st.divider()
    
    # --- Professional Identity Section ---
    st.subheader("👤 Professional Identity")
    
    headline = st.text_input(
        "Professional Headline",
        value=existing_identity.get("headline", ""),
        placeholder="e.g., Senior Java Backend Engineer",
        help="Your professional title. Used to match you with relevant jobs."
    )
    
    primary_skills = st.text_input(
        "Primary Skills",
        value=", ".join(existing_identity.get("primary_skills", [])),
        placeholder="e.g., Java, Spring Boot, Microservices",
        help="Core skills you want to be matched with. Comma-separated."
    )
    
    secondary_skills = st.text_input(
        "Secondary Skills",
        value=", ".join(existing_identity.get("secondary_skills", [])),
        placeholder="e.g., AWS, Kubernetes, Docker",
        help="Additional skills that complement your primary skills."
    )
    
    target_roles = st.text_input(
        "Target Roles",
        value=", ".join(existing_identity.get("target_roles", [])),
        placeholder="e.g., Senior Backend Engineer, Platform Engineer",
        help="Job titles you're targeting. Comma-separated."
    )
    
    st.divider()
    
    # --- Rejection Rules Section ---
    st.subheader("🚫 Rejection Rules")
    
    reject_if = existing_identity.get("reject_if", {})
    
    reject_languages = st.text_input(
        "Reject Languages",
        value=", ".join(reject_if.get("languages", [])),
        placeholder="e.g., PHP, Ruby, PHP",
        help="Languages you do NOT want to work with. Jobs requiring these will be rejected."
    )
    
    reject_frameworks = st.text_input(
        "Reject Frameworks",
        value=", ".join(reject_if.get("frameworks", [])),
        placeholder="e.g., Laravel, Rails, SharePoint",
        help="Frameworks you do NOT want to work with."
    )
    
    reject_roles = st.text_input(
        "Reject Roles",
        value=", ".join(reject_if.get("roles", [])),
        placeholder="e.g., Frontend-heavy, QA Engineer",
        help="Role types you want excluded from results."
    )
    
    st.divider()
    
    # --- CV Data Section ---
    st.subheader("📄 CV Data (Optional)")
    
    cv_skills = st.text_input(
        "CV Skills",
        value=", ".join(existing_cv.get("skills", [])),
        placeholder="e.g., Java, Spring Boot, PostgreSQL",
        help="Skills from your CV. Used as fallback if identity skills are empty."
    )
    
    cv_experience = st.text_area(
        "Experience Summary",
        value=existing_cv.get("experience", ""),
        placeholder="e.g., 8 years backend development with Java/Spring Boot",
        height=80,
        help="Brief description of your experience."
    )
    
    cv_education = st.text_input(
        "Education",
        value=existing_cv.get("education", ""),
        placeholder="e.g., BSc Computer Science",
        help="Your educational background."
    )
    
    st.divider()
    
    # --- Preferences Section ---
    st.subheader("💰 Preferences")
    
    col1, col2 = st.columns(2)
    with col1:
        pref_remote = st.checkbox(
            "Remote Only",
            value=existing_prefs.get("remote", True),
            help="Only show remote jobs"
        )
    with col2:
        pref_work_type = st.selectbox(
            "Work Type",
            options=["remote", "hybrid", "office", "any"],
            index=["remote", "hybrid", "office", "any"].index(existing_prefs.get("work_type", "remote")),
            help="Preferred work arrangement"
        )
    
    col3, col4 = st.columns(2)
    with col3:
        salary_min = st.number_input(
            "Min Salary (USD/mo)",
            value=int(existing_prefs.get("salary_min", 0) or 0),
            min_value=0,
            step=500,
            help="Minimum monthly salary in USD"
        )
    with col4:
        salary_max = st.number_input(
            "Max Salary (USD/mo)",
            value=int(existing_prefs.get("salary_max", 0) or 0),
            min_value=0,
            step=500,
            help="Maximum monthly salary in USD (0 = no limit)"
        )
    
    st.divider()
    
    # --- Authentication Section ---
    st.subheader("🔐 Authentication (Optional)")
    
    djinni_cookies = st.text_area(
        "Djinni Cookies JSON",
        value=existing_prefs.get("djinni_cookies", ""),
        placeholder='{"sessionid": "...", "csrftoken": "..."}',
        height=80,
        help="Export cookies from browser after logging into djinni.co"
    )
    
    linkedin_cookies = st.text_area(
        "LinkedIn Cookies JSON",
        value=existing_prefs.get("linkedin_cookies", ""),
        placeholder='{"li_at": "...", "JSESSIONID": "..."}',
        height=80,
        help="Export cookies from browser after logging into LinkedIn. Provides richer job data."
    )
    
    st.divider()
    
    # --- Save Profile Button ---
    if st.button("💾 Save Profile", type="primary", use_container_width=True):
        # Build identity data
        identity_data = {}
        if headline:
            identity_data["headline"] = headline
        if primary_skills:
            identity_data["primary_skills"] = [s.strip() for s in primary_skills.split(",") if s.strip()]
        if secondary_skills:
            identity_data["secondary_skills"] = [s.strip() for s in secondary_skills.split(",") if s.strip()]
        if target_roles:
            identity_data["target_roles"] = [s.strip() for s in target_roles.split(",") if s.strip()]
        
        reject_if_data = {}
        if reject_languages:
            reject_if_data["languages"] = [s.strip() for s in reject_languages.split(",") if s.strip()]
        if reject_frameworks:
            reject_if_data["frameworks"] = [s.strip() for s in reject_frameworks.split(",") if s.strip()]
        if reject_roles:
            reject_if_data["roles"] = [s.strip() for s in reject_roles.split(",") if s.strip()]
        if reject_if_data:
            identity_data["reject_if"] = reject_if_data
        
        # Build CV data
        cv_data = {}
        if cv_skills:
            cv_data["skills"] = [s.strip() for s in cv_skills.split(",") if s.strip()]
        if cv_experience:
            cv_data["experience"] = cv_experience
        if cv_education:
            cv_data["education"] = cv_education
        
        # Build preferences
        prefs_data = {
            "remote": pref_remote,
            "work_type": pref_work_type,
        }
        if salary_min > 0:
            prefs_data["salary_min"] = salary_min
        if salary_max > 0:
            prefs_data["salary_max"] = salary_max
        if djinni_cookies:
            prefs_data["djinni_cookies"] = djinni_cookies
        if linkedin_cookies:
            prefs_data["linkedin_cookies"] = linkedin_cookies
        
        # Save to database
        save_profile_to_db(user_id, {
            "cv": cv_data,
            "prefs": prefs_data,
            "identity": identity_data
        })
        
        st.success("✅ Profile saved successfully!")
        st.rerun()
    
    # --- Clear Chat ---
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # --- Query Guide ---
    with st.expander("📝 How to Write Queries", expanded=True):
        st.markdown("""
**Format:** `[seniority] [role] [work_type] in [location] salary [amount] posted [when]`

---
**Work Types:**
- `remote` - Work from anywhere
- `hybrid` - Mix of remote and office
- `office` - On-site only
- `worldwide` - Any location worldwide

---
**Posted:**
- `today` - Last 24 hours
- `this week` - Last 7 days
- `this month` - Last 30 days
- `last N days` - Custom range

---
**Examples:**

| Query | Description |
|-------|-------------|
| `Senior java developer remote in Tbilisi` | Java role in Tbilisi |
| `Python engineer salary 5000 usd` | Python with min salary |
| `React developer remote worldwide posted today` | Remote React, posted today |
| `Junior developer in Batumi last 7 days` | Junior role, recent |
| `Senior full stack engineer hybrid in New York salary 8000-12000 usd` | NYC hybrid, salary range |
| `Devops engineer remote posted this week` | DevOps, recent postings |
| `AI engineer remote in Europe salary 10000-15000 usd` | AI role in Europe |

---
**Tips:**
- Location can be city or country
- Salary is monthly in USD
- Combine multiple filters in one query
        """)

# --- Initialize Session & Cookies ---
session = None
all_cookies = {}

# Use saved cookies from profile
if existing_prefs.get("djinni_cookies"):
    try:
        all_cookies.update(json.loads(existing_prefs["djinni_cookies"]))
    except Exception:
        pass

if existing_prefs.get("linkedin_cookies"):
    try:
        all_cookies.update(json.loads(existing_prefs["linkedin_cookies"]))
    except Exception:
        pass

if all_cookies:
    try:
        session = SessionManager()
        session.set_cookies(all_cookies)
    except Exception as e:
        st.sidebar.error(f"Session Error: {e}")

# --- Main Chat Interface ---
st.title("🤖 AI Job Search Agent")
st.caption("Ask me to find jobs, and I'll match them to your professional profile.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Show example prompts when chat is empty
if not st.session_state.messages:
    with st.chat_message("assistant"):
        headline_display = headline or "your role"
        st.markdown(f"Hi! I can help you find jobs for **{headline_display}**. Try something like:")
        
        example_queries = [
            f"Senior java developer remote in Tbilisi",
            f"Remote backend engineer salary 5000 usd posted this week",
            f"AI engineer remote worldwide",
        ]
        for eq in example_queries:
            st.code(eq, language=None)

# User Input
if prompt := st.chat_input("Search for jobs..."):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process Agent Response
    with st.chat_message("assistant"):
        with st.spinner("Searching and ranking jobs..."):
            response_text = ""
            try:
                # Build profile from saved data
                identity_data = {}
                if headline:
                    identity_data["headline"] = headline
                if primary_skills:
                    identity_data["primary_skills"] = [s.strip() for s in primary_skills.split(",") if s.strip()]
                if secondary_skills:
                    identity_data["secondary_skills"] = [s.strip() for s in secondary_skills.split(",") if s.strip()]
                if target_roles:
                    identity_data["target_roles"] = [s.strip() for s in target_roles.split(",") if s.strip()]
                
                reject_if_data = {}
                if reject_languages:
                    reject_if_data["languages"] = [s.strip() for s in reject_languages.split(",") if s.strip()]
                if reject_frameworks:
                    reject_if_data["frameworks"] = [s.strip() for s in reject_frameworks.split(",") if s.strip()]
                if reject_roles:
                    reject_if_data["roles"] = [s.strip() for s in reject_roles.split(",") if s.strip()]
                if reject_if_data:
                    identity_data["reject_if"] = reject_if_data
                
                cv_data = {}
                if cv_skills:
                    cv_data["skills"] = [s.strip() for s in cv_skills.split(",") if s.strip()]
                if cv_experience:
                    cv_data["experience"] = cv_experience
                if cv_education:
                    cv_data["education"] = cv_education
                
                prefs_data = {
                    "remote": pref_remote,
                    "work_type": pref_work_type,
                }
                if salary_min > 0:
                    prefs_data["salary_min"] = salary_min
                if salary_max > 0:
                    prefs_data["salary_max"] = salary_max
                
                # Persist profile
                profile = {"cv": cv_data, "prefs": prefs_data, "identity": identity_data}
                repo.save_profile(user_id, cv_data, prefs_data, identity_data)
                
                # Run LangGraph Agent
                config = {"configurable": {"thread_id": user_id}}
                initial_state = {
                    "user_id": user_id,
                    "query": prompt,
                    "user_profile": profile,
                    "parsed_query": {},
                    "scraped_jobs": [],
                    "validated_jobs": [],
                    "enriched_jobs": [],
                    "jobs": [],
                    "filtered_jobs": [],
                    "ranked_jobs": [],
                    "verified_jobs": [],
                    "final_response": "",
                    "errors": [],
                    "crawler_stats": {},
                    "rejection_log": [],
                    "session_cookies": all_cookies,
                }
                
                final_state = app.invoke(initial_state, config)
                verified_jobs = final_state.get("verified_jobs", [])
                ranked_jobs = final_state.get("ranked_jobs", [])
                jobs_to_show = verified_jobs if verified_jobs else ranked_jobs
                
                if jobs_to_show:
                    intelligence = generate_career_intelligence(jobs_to_show, profile, final_state.get("parsed_query", {}))
                    
                    summary = intelligence["summary"]
                    current = intelligence.get("current_employability", {})
                    
                    intro = f"I found **{summary['total_jobs']}** matching roles for **{current.get('headline', 'your profile')}**. **{summary['top_opportunities']}** are top opportunities."
                    st.markdown(intro)
                    response_text = intro
                    
                    with st.expander("View Full Intelligence Report", expanded=False):
                        st.markdown(format_intelligence_report(intelligence))
                    
                    future = intelligence.get("future_trajectory", {})
                    predicted = future.get("predicted_direction")
                    if predicted:
                        st.info(f"**Future Trajectory:** Your profile suggests {predicted['name']} ({future.get('trajectory_score', 0)}% confidence)")
                    
                    skill_roi = intelligence.get("skill_roi", [])
                    if skill_roi:
                        with st.expander("View Skill Learning ROI", expanded=False):
                            from agent.skill_roi import format_skill_roi_report
                            st.markdown(format_skill_roi_report(skill_roi))
                    
                    for job in intelligence["opportunity_scores"]:
                        identity_align = job.get('identity_alignment', 0)
                        color = "green" if identity_align >= 60 else "orange" if identity_align >= 40 else "red"
                        
                        sub_scores = job.get('sub_scores', {})
                        matched = job.get('matched_skills', [])
                        missing = job.get('missing_skills', [])
                        skill_gaps = job.get('skill_gaps', {})
                        
                        with st.expander(f"[{identity_align}%] {job['title']} @ {job.get('company', 'Unknown')}"):
                            st.markdown(f"**Identity Alignment:** :{color}[{identity_align}%]")
                            st.caption(job.get('identity_explanation', ''))
                            
                            if sub_scores:
                                st.markdown("**Score Breakdown:**")
                                cols = st.columns(5)
                                with cols[0]:
                                    st.metric("Technical", sub_scores.get('technical_fit', 0))
                                with cols[1]:
                                    st.metric("Salary", sub_scores.get('salary_match', 0))
                                with cols[2]:
                                    st.metric("Growth", sub_scores.get('career_growth', 0))
                                with cols[3]:
                                    st.metric("Hiring", sub_scores.get('hiring_probability', 0))
                                with cols[4]:
                                    st.metric("Interest", sub_scores.get('interest_match', 0))
                            
                            if matched:
                                st.markdown("**Your Skills That Match:**")
                                st.markdown(" ".join([f"`{s}`" for s in matched[:5]]))
                            
                            if missing:
                                st.markdown("**Skills to Learn:**")
                                for skill in missing[:3]:
                                    gap = skill_gaps.get(skill, {})
                                    time_display = gap.get('time_display', 'Unknown')
                                    salary_impact = gap.get('salary_impact', 0)
                                    st.markdown(f"- `{skill}` ({time_display}, +${salary_impact}/mo potential)")
                            
                            st.markdown(f"**Why it matches:** {job.get('why', 'N/A')}")
                            st.markdown(f"**Description:**\n{job.get('description', 'No description provided.')}")
                            st.link_button("Apply Here", job.get('url', '#'))
                            st.caption(f"Source: {job.get('source', 'Web')}")
                else:
                    response_text = "I couldn't find any jobs matching that criteria. Try adjusting your search!"
                    st.warning(response_text)
            
            except Exception as e:
                import traceback
                traceback.print_exc()
                error_msg = str(e)
                if "Expecting value" in error_msg:
                    response_text = "LLM service returned an invalid response. Using fallback parser..."
                    st.warning(response_text)
                else:
                    response_text = f"An error occurred: {e}"
                    st.error(response_text)
            
            if response_text:
                st.session_state.messages.append({"role": "assistant", "content": response_text})
