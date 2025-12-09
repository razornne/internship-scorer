import streamlit as st
import pandas as pd
from collections import Counter
import google.generativeai as genai
import time
from core import ScorerEngine, load_real_db

# === 1. CONFIG & STYLES ===
st.set_page_config(
    page_title="AI Internship Scorer", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# CUSTOM CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* ЗАГОЛОВОК */
    .title-text {
        background: linear-gradient(90deg, #2563EB, #9333EA);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient 6s ease infinite;
        font-weight: 800;
        font-size: 3rem !important;
        padding-bottom: 10px;
    }
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    /* КВАДРАТНЫЕ ТЕГИ */
    .skill-tag {
        display: inline-flex;
        align-items: center;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 2px;
        border: 1px solid transparent;
        font-family: 'Consolas', 'Monaco', monospace;
    }

    /* Светлая тема */
    .skill-tag { background-color: #F1F5F9; color: #334155; border-color: #E2E8F0; }
    .missing-tag { background-color: #FEF2F2 !important; color: #DC2626 !important; border-color: #FECACA !important; }

    /* Темная тема */
    @media (prefers-color-scheme: dark) {
        .skill-tag { background-color: #1E293B; color: #E2E8F0; border-color: #334155; }
        .missing-tag { background-color: #450a0a !important; color: #fca5a5 !important; border-color: #7f1d1d !important; }
    }

    /* КАРТОЧКА ВАКАНСИИ */
    .job-card {
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid transparent;
        transition: transform 0.2s;
    }
    .job-card:hover { transform: translateY(-3px); }

    /* Темизация карточки */
    .job-card { background-color: #ffffff; border-color: #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    @media (prefers-color-scheme: dark) {
        .job-card { background-color: #262730; border-color: #3f3f46; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    }

    /* БОЛЬШОЙ СКОР */
    .big-score {
        font-size: 2.5rem;
        font-weight: 800;
        line-height: 1;
        text-align: right;
    }
    .status-label {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-align: right;
        margin-top: 4px;
    }

    /* КНОПКА */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #2563EB, #1D4ED8);
        color: white; border: none; border-radius: 8px; font-weight: 600;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #1D4ED8, #1E40AF);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# === 2. INITIALIZATION ===
@st.cache_resource
def get_engine(): return ScorerEngine()

@st.cache_data(ttl=3600)
def get_jobs(): return load_real_db()

engine = get_engine()
df_jobs = get_jobs()

if 'calculated' not in st.session_state: st.session_state.calculated = False

# === 3. AUTH ===
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    auth_status = "✨ AI Ready"
else:
    api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password")
    auth_status = "⚠️ Key missing"

# === 4. SIDEBAR ===
with st.sidebar:
    st.title("👨‍💻 Profile")
    st.caption(auth_status)
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
    st.caption("v2.6 • Stable UI")

# === 5. FUNCTIONS ===
def generate_cover_letter_gemini(api_key, cv_text, job_description, company_name, job_title):
    if not api_key: return "⚠️ API Key missing."
    genai.configure(api_key=api_key)
    models = ['models/gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
    for model_name in models:
        try:
            time.sleep(0.3)
            model = genai.GenerativeModel(model_name)
            with st.spinner(f"✨ Generating with {model_name}..."):
                prompt = f"Write a 150-word cover letter. RESUME: {cv_text[:1000]}. JOB: {job_title} at {company_name}. DESC: {job_description[:1000]}. No placeholders."
                response = model.generate_content(prompt)
                if response.text: return response.text
        except: continue
    return "❌ AI is taking a nap. Try again."

# === 6. MAIN UI ===
st.markdown('<h1 class="title-text">AI Internship Scorer 🚀</h1>', unsafe_allow_html=True)
st.markdown("### Find your perfect match.")

if df_jobs.empty:
    st.warning("⚠️ Database empty. Please run `python ingest_ai.py`.")
    st.stop()

# CV Processing
cv_text = ""
if uploaded_file:
    cv_text = engine.extract_text_from_pdf(uploaded_file)
elif manual_text:
    cv_text = manual_text

if cv_text:
    user_skills = engine.extract_skills(cv_text)
    
    st.markdown("#### Your Stack:")
    skills_html = "".join([f'<span class="skill-tag">{s}</span>' for s in user_skills])
    st.markdown(skills_html, unsafe_allow_html=True)
    
    st.write("")
    if st.button("🔥 Analyze Market", type="primary", use_container_width=True):
        st.session_state.calculated = True

    st.markdown("---")

    if st.session_state.calculated:
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

            st.subheader(f"🏆 Top {len(filtered_df)} Recommendations")
            
            for idx, row in filtered_df.iterrows():
                score = row['Score']
                missing = engine.analyze_gaps(user_skills, row['description'])
                
                # Colors
                if score >= 70: 
                    score_color = "#10B981"
                    status_text = "HIGH MATCH"
                elif score >= 50: 
                    score_color = "#3B82F6"
                    status_text = "MEDIUM MATCH"
                else: 
                    score_color = "#94A3B8"
                    status_text = "LOW MATCH"

                # HTML CARD GENERATION
                # Используем f-строку без лишних отступов и комментариев, чтобы не сломать Markdown
                card_html = f"""
<div class="job-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div style="flex: 1; padding-right: 20px;">
            <h3 style="margin:0; font-size: 1.4rem; color:inherit;">{row['title']}</h3>
            <p style="margin:6px 0 0 0; opacity:0.8; font-size:1rem;">
                🏢 <b>{row['company']}</b> &nbsp;•&nbsp; 📍 {row['Location']}
            </p>
        </div>
        <div style="text-align:right; min-width: 120px;">
            <div class="big-score" style="color: {score_color};">{int(score)}%</div>
            <div class="status-label" style="color: {score_color};">{status_text}</div>
        </div>
    </div>
"""
                
                # Добавляем навыки
                if missing:
                    missing_html = "".join([f'<span class="skill-tag missing-tag">{s}</span>' for s in missing[:5]])
                    if len(missing) > 5: missing_html += f'<span class="skill-tag missing-tag">+{len(missing)-5}</span>'
                    card_html += f"<div style='margin-top:16px; font-size:0.9rem;'><b>Missing Skills:</b> {missing_html}</div>"
                else:
                    card_html += f"<div style='margin-top:16px; color:{score_color}; font-weight:600;'>✨ Perfect Technical Match!</div>"

                card_html += "</div>"

                # === РЕНДЕРИНГ HTML (Самое важное!) ===
                st.markdown(card_html, unsafe_allow_html=True)

                # КНОПКИ
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    if row['url'] and row['url'] != "#":
                        st.link_button("👉 Apply", row['url'], use_container_width=True, key=f"btn_{idx}")
                    else:
                        st.button("No Link", disabled=True, key=f"nl_{idx}", use_container_width=True)
                with c2:
                    with st.popover("📄 Details", use_container_width=True):
                        st.markdown(f"### {row['title']}")
                        st.write(row['description'])
                with c3:
                    popover = st.popover("🤖 Draft Letter", use_container_width=True)
                    if popover.button("Generate", key=f"gen_{idx}", type="primary"):
                        letter = generate_cover_letter_gemini(api_key, cv_text, row['description'], row['company'], row['title'])
                        popover.text_area("Result:", value=letter, height=300)
                
                st.write("") # Отступ

        else:
            st.info("No jobs found.")
else:
    st.info("👈 Upload your CV to start.")