import streamlit as st
import pandas as pd
from collections import Counter
import google.generativeai as genai
import time
from core import ScorerEngine, load_real_db

# === 1. CONFIG & STYLES (THE MAGIC PART) ===
st.set_page_config(
    page_title="AI Career Assistant", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# CUSTOM CSS FOR MODERN UI
st.markdown("""
<style>
    /* 1. Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* 2. Gradient Title Animation */
    .title-text {
        background: linear-gradient(45deg, #FF4B4B, #FF914D, #FF4B4B);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient 5s ease infinite;
        font-weight: 800;
        font-size: 3rem !important;
        padding-bottom: 10px;
    }
    
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    /* 3. Modern Card Style for Jobs */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        /* Это хак для таргетинга контейнеров Streamlit, может требовать настройки */
    }
    
    .job-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        transition: transform 0.2s, box-shadow 0.2s;
        margin-bottom: 15px;
    }
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
    }

    /* 4. Score Badge */
    .score-circle {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        font-weight: bold;
        font-size: 1.2rem;
        color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* 5. Skill Tags */
    .skill-pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 2px;
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #e2e8f0;
    }
    
    .missing-pill {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }

    /* Dark Mode Adjustments */
    @media (prefers-color-scheme: dark) {
        .job-card {
            background-color: #1e1e1e;
            border: 1px solid #333;
        }
        .skill-pill {
            background-color: #2d3748;
            color: #e2e8f0;
            border-color: #4a5568;
        }
    }
</style>
""", unsafe_allow_html=True)

# === 2. INITIALIZATION ===
@st.cache_resource
def get_engine():
    return ScorerEngine()

@st.cache_data(ttl=3600)
def get_jobs():
    return load_real_db()

engine = get_engine()
df_jobs = get_jobs()

if 'calculated' not in st.session_state:
    st.session_state.calculated = False

# === 3. AUTH ===
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    auth_status = "✨ Pro Mode Active"
else:
    api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password")
    auth_status = "⚠️ Key missing"

# === 4. SIDEBAR DESIGN ===
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3048/3048122.png", width=60)
    st.title("My Profile")
    st.caption(f"{auth_status}")
    
    uploaded_file = st.file_uploader("📄 Upload CV (PDF)", type="pdf")
    manual_text = st.text_area("Or paste text:", height=100)
    
    st.divider()
    st.subheader("🎯 Filters")
    
    if not df_jobs.empty:
        unique_locs = sorted(df_jobs['Location'].astype(str).unique().tolist())
        locations = ["All Locations"] + unique_locs
        selected_loc = st.selectbox("📍 City", locations)
        only_remote = st.checkbox("🏠 Remote Only")
    
    st.markdown("---")
    st.caption("v2.1 • Built with 🧠 & ☕ in Prague")

# === 5. FUNCTIONS ===
def generate_cover_letter_gemini(api_key, cv_text, job_description, company_name, job_title):
    if not api_key: return "⚠️ API Key missing."
    genai.configure(api_key=api_key)
    models = ['models/gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
    
    for model_name in models:
        try:
            time.sleep(0.3)
            model = genai.GenerativeModel(model_name)
            with st.spinner(f"✨ Magic happening with {model_name}..."):
                prompt = f"Write a 150-word cover letter. RESUME: {cv_text[:1000]}. JOB: {job_title} at {company_name}. DESC: {job_description[:1000]}. No placeholders."
                response = model.generate_content(prompt)
                if response.text: return response.text
        except: continue
    return "❌ AI is taking a nap. Try again."

# === 6. HERO SECTION ===
st.markdown('<h1 class="title-text">AI Career Launchpad 🚀</h1>', unsafe_allow_html=True)
st.markdown("### Stop searching. Start matching.")
st.markdown("This tool uses **Neural Networks** to analyze your CV against real job market data in Prague.")

if df_jobs.empty:
    st.warning("⚠️ Database empty. Please run `python ingest_ai.py` to generate jobs.")
    st.stop()

# CV Logic
cv_text = ""
if uploaded_file:
    cv_text = engine.extract_text_from_pdf(uploaded_file)
elif manual_text:
    cv_text = manual_text

if cv_text:
    user_skills = engine.extract_skills(cv_text)
    
    # Stylish Skill Display
    st.markdown("#### Your Detected Stack:")
    skills_html = "".join([f'<span class="skill-pill">{s}</span>' for s in user_skills])
    st.markdown(skills_html, unsafe_allow_html=True)
    
    col_main_btn, _ = st.columns([1, 2])
    with col_main_btn:
        if st.button("🔥 Find My Dream Job", type="primary", use_container_width=True):
            st.session_state.calculated = True

    st.markdown("---")

    if st.session_state.calculated:
        # FILTERING
        filtered_df = df_jobs.copy()
        if selected_loc != "All Locations":
            filtered_df = filtered_df[filtered_df['Location'] == selected_loc]
        if only_remote:
             filtered_df = filtered_df[
                 filtered_df['Location'].str.contains('Remote', case=False) | 
                 filtered_df['description'].str.contains('Remote', case=False)
             ]
        
        if not filtered_df.empty:
            descriptions = filtered_df['description'].tolist()
            scores = engine.calculate_hybrid_score(cv_text, descriptions, user_skills)
            filtered_df['Score'] = scores
            filtered_df = filtered_df.sort_values(by='Score', ascending=False).head(15)

            st.subheader(f"🏆 Top {len(filtered_df)} Opportunities")
            
            # === NEW CARD LAYOUT ===
            for idx, row in filtered_df.iterrows():
                score = row['Score']
                missing = engine.analyze_gaps(user_skills, row['description'])
                
                # Dynamic Colors
                if score >= 70: 
                    bg_color = "#2ecc71" # Green
                    status_text = "Perfect Match"
                elif score >= 50: 
                    bg_color = "#f1c40f" # Yellow
                    status_text = "Good Fit"
                else: 
                    bg_color = "#e74c3c" # Red
                    status_text = "Reach"

                # CARD CONTAINER
                with st.container():
                    # Custom HTML Header for the Card to make it look nicer than standard Streamlit
                    st.markdown(f"""
                    <div class="job-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <h3 style="margin:0; color:#1e293b;">{row['title']}</h3>
                                <p style="margin:0; color:#64748b; font-size:0.9rem;">
                                    🏢 <b>{row['company']}</b> &nbsp;•&nbsp; 📍 {row['Location']}
                                </p>
                            </div>
                            <div class="score-circle" style="background-color: {bg_color};">
                                {int(score)}%
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Missing Skills Logic
                    if missing:
                        missing_html = "".join([f'<span class="skill-pill missing-pill">{s}</span>' for s in missing[:4]])
                        if len(missing) > 4: missing_html += f'<span class="skill-pill missing-pill">+{len(missing)-4} more</span>'
                        st.markdown(f"<div style='margin-top:10px;'><b>Missing:</b> {missing_html}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='margin-top:10px; color:#2ecc71;'><b>✨ You have the full stack!</b></div>", unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True) # Close card div

                    # ACTION BUTTONS (Streamlit native widgets underneath the HTML card)
                    c1, c2, c3 = st.columns([1, 1, 2])
                    with c1:
                        if row['url'] and row['url'] != "#":
                            st.link_button("👉 Apply", row['url'], use_container_width=True)
                        else:
                            st.button("No Link", disabled=True, key=f"nl_{idx}", use_container_width=True)
                    
                    with c2:
                         # Expander for details
                        with st.popover("📄 Details", use_container_width=True):
                            st.markdown(f"### {row['title']}")
                            st.write(row['description'])

                    with c3:
                        # AI Letter
                        popover = st.popover("🤖 Write Letter", use_container_width=True)
                        if popover.button("Generate with AI", key=f"gen_{idx}", type="primary"):
                            letter = generate_cover_letter_gemini(
                                api_key, cv_text, row['description'], row['company'], row['title']
                            )
                            popover.text_area("Your Draft:", value=letter, height=300)
                    
                    st.write("") # Spacer

        else:
            st.info("No jobs found with these filters.")

else:
    # EMPTY STATE UI
    st.info("👈 Upload your CV in the sidebar to unlock your career.")