import streamlit as st
import pandas as pd
from collections import Counter
import google.generativeai as genai
import time
from core import ScorerEngine, load_real_db

# === 1. CONFIG & STYLES ===
st.set_page_config(page_title="AI Career Assistant", layout="wide", page_icon="🚀")

# CUSTOM CSS (Для красоты)
st.markdown("""
<style>
    /* Стиль для тегов навыков */
    .skill-tag {
        display: inline-block;
        background-color: #f0f2f6;
        color: #31333F;
        padding: 4px 10px;
        border-radius: 15px;
        margin: 2px;
        font-size: 0.85em;
        border: 1px solid #d0d2d6;
    }
    /* Темная тема для тегов (авто-адаптация) */
    @media (prefers-color-scheme: dark) {
        .skill-tag {
            background-color: #262730;
            color: #fafafa;
            border: 1px solid #464b5c;
        }
    }
    /* Стиль для метрики скора */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)

# === 2. INITIALIZATION ===
@st.cache_resource
def get_engine():
    return ScorerEngine()

@st.cache_data
def get_jobs():
    return load_real_db()

engine = get_engine()
df_jobs = get_jobs()

# Инициализация Session State
if 'calculated' not in st.session_state:
    st.session_state.calculated = False

# === 3. AUTH (SECRETS) ===
# Пытаемся достать ключ из секретов, иначе просим ввести
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    auth_status = "✅ Key loaded from Secrets"
else:
    api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password")
    auth_status = "⚠️ Key not found in secrets"

# === 4. SIDEBAR ===
with st.sidebar:
    st.title("👨‍💻 Profile")
    st.caption(auth_status)
    
    uploaded_file = st.file_uploader("Upload CV (PDF)", type="pdf")
    manual_text = st.text_area("Or paste text:", height=150)
    
    st.divider()
    st.subheader("🌍 Filters")
    
    if not df_jobs.empty:
        unique_locs = sorted(df_jobs['Location'].astype(str).unique().tolist())
        locations = ["All Locations"] + unique_locs
        selected_loc = st.selectbox("City", locations)
        only_remote = st.checkbox("Remote Only")
    else:
        st.error("Database empty")

# === 5. FUNCTIONS ===
def generate_cover_letter_gemini(api_key, cv_text, job_description, company_name, job_title):
    if not api_key: return "⚠️ API Key missing."
    
    genai.configure(api_key=api_key)
    # Retry logic + Fallback
    models = ['models/gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
    
    for model_name in models:
        try:
            time.sleep(0.3)
            model = genai.GenerativeModel(model_name)
            with st.spinner(f"✨ Magic with {model_name}..."):
                prompt = f"""
                Write a short, punchy Cover Letter for a Junior IT role.
                RESUME: {cv_text[:1500]}
                JOB: {company_name} - {job_title}
                DESC: {job_description[:1500]}
                Constraints: Max 150 words. Focus on matching skills. No placeholders.
                """
                response = model.generate_content(prompt)
                if response.text: return response.text
        except: continue
    return "❌ AI is currently overloaded. Try again in 30s."

# === 6. MAIN UI ===
st.title("🚀 AI Internship Scorer")
st.markdown("Find your perfect match in **Prague** & beyond.")

if df_jobs.empty:
    st.warning("No data. Run `python ingest.py` first.")
    st.stop()

# CV Logic
cv_text = ""
if uploaded_file:
    cv_text = engine.extract_text_from_pdf(uploaded_file)
elif manual_text:
    cv_text = manual_text

if cv_text:
    user_skills = engine.extract_skills(cv_text)
    
    # Красивое отображение навыков
    st.write("YOUR SKILLS:")
    skills_html = "".join([f'<span class="skill-tag">{s}</span>' for s in user_skills])
    st.markdown(skills_html, unsafe_allow_html=True)

    if st.button("🔥 Analyze Market", type="primary", use_container_width=True):
        st.session_state.calculated = True

    st.divider()

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
        
        # SCORING
        if not filtered_df.empty:
            descriptions = filtered_df['description'].tolist()
            scores = engine.calculate_hybrid_score(cv_text, descriptions, user_skills)
            filtered_df['Score'] = scores
            filtered_df = filtered_df.sort_values(by='Score', ascending=False).head(15)

            # RESULTS LOOP
            st.subheader(f"🏆 Top {len(filtered_df)} Recommendations")
            
            for idx, row in filtered_df.iterrows():
                score = row['Score']
                missing = engine.analyze_gaps(user_skills, row['description'])
                
                # Logic for Color/Emoji
                if score >= 65: 
                    color = "green"
                    emoji = "🟢"
                    status = "Excellent Match"
                elif score >= 45: 
                    color = "orange"
                    emoji = "🟡"
                    status = "Good Start"
                else: 
                    color = "red"
                    emoji = "🔴"
                    status = "Hard Reach"

                # === CARD UI ===
                with st.container(border=True):
                    # Header Grid
                    c1, c2, c3 = st.columns([0.1, 0.7, 0.2])
                    with c1: st.title(emoji)
                    with c2: 
                        st.markdown(f"### {row['title']}")
                        st.caption(f"🏢 **{row['company']}** | 📍 {row['Location']}")
                    with c3:
                        st.metric("Score", f"{score}%")
                    
                    # Missing Skills (Visual Pills)
                    if missing:
                        st.markdown("**Missing:** " + "".join([f'<span class="skill-tag" style="border-color:#ff4b4b; color:#ff4b4b">{s}</span>' for s in missing[:5]]), unsafe_allow_html=True)
                    else:
                        st.success("✅ Full Stack Match!")

                    # Description Expander
                    with st.expander(f"Details & Stats ({status})"):
                        st.write(row['description'])

                    # ACTIONS ROW (Buttons side-by-side)
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        # Кнопка Apply (если есть ссылка)
                        if row['url'] and row['url'] != "#":
                            st.link_button("👉 Apply Now", row['url'], use_container_width=True)
                        else:
                            st.button("No Link", disabled=True, use_container_width=True)

                    with col_btn2:
                        # Кнопка AI Letter
                        popover = st.popover("🤖 Draft Letter", use_container_width=True)
                        if popover.button("Generate Text", key=f"gen_{idx}", type="primary"):
                            letter = generate_cover_letter_gemini(
                                api_key, cv_text, row['description'], row['company'], row['title']
                            )
                            popover.text_area("Result:", value=letter, height=300)
        else:
            st.info("No jobs found with these filters.")

else:
    st.info("👋 Upload your CV to see the magic.")