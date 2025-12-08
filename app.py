import streamlit as st
import pandas as pd
from collections import Counter
import google.generativeai as genai
from core import ScorerEngine, load_real_db

st.set_page_config(page_title="AI Career Assistant", layout="wide")

@st.cache_resource
def get_engine():
    return ScorerEngine()

@st.cache_data
def get_jobs():
    return load_real_db()

engine = get_engine()
df_jobs = get_jobs()

# === SIDEBAR ===
st.sidebar.title("👨‍💻 Your Profile")

# --- API KEY INPUT (SECURE) ---
st.sidebar.subheader("🔑 AI Settings")
api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get it free at aistudio.google.com")
# ------------------------------

uploaded_file = st.sidebar.file_uploader("Upload CV (PDF)", type="pdf")
manual_text = st.sidebar.text_area("Or paste text manually:", height=150)

st.sidebar.divider()
st.sidebar.subheader("🌍 Filters")

if not df_jobs.empty:
    unique_locs = sorted(df_jobs['Location'].astype(str).unique().tolist())
    locations = ["All Locations"] + unique_locs
    selected_loc = st.sidebar.selectbox("Location", locations)
    only_remote = st.sidebar.checkbox("Remote only")
else:
    st.sidebar.error("Job database is empty!")

# === FUNCTION: GEMINI COVER LETTER ===
def generate_cover_letter_gemini(api_key, cv_text, job_description, company_name, job_title):
    if not api_key:
        return "⚠️ Please enter your Gemini API Key in the sidebar to generate magic letters!"
    
    try:
        genai.configure(api_key=api_key)
        # Используем модель Flash - она очень быстрая и дешевая (бесплатная во free tier)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Act as an expert career coach. Write a professional, engaging cover letter for a Junior IT position.
        
        MY RESUME TEXT:
        {cv_text[:2000]}
        
        JOB DESCRIPTION:
        {job_description[:2000]}
        
        COMPANY: {company_name}
        POSITION: {job_title}
        
        INSTRUCTIONS:
        1. Keep it concise (max 200 words).
        2. Don't simply list skills. Explain how my specific experience fits THEIR specific needs found in the description.
        3. Tone: Professional, enthusiastic, and confident.
        4. Use placeholders like [Your Name], [Phone Number] only at the end.
        """
        
        with st.spinner("🤖 Gemini is writing your letter..."):
            response = model.generate_content(prompt)
            return response.text
            
    except Exception as e:
        return f"Error connecting to Gemini: {str(e)}"

# === MAIN ===
st.title("🚀 AI Internship Scorer + Gemini 🤖")
st.caption("Smart aggregator with LLM-powered Cover Letter Generator")

if df_jobs.empty:
    st.error("No jobs found. Run ingest scripts first.")
    st.stop()

# CV Processing
cv_text = ""
if uploaded_file:
    cv_text = engine.extract_text_from_pdf(uploaded_file)
elif manual_text:
    cv_text = manual_text

if cv_text:
    user_skills = engine.extract_skills(cv_text)
    
    with st.expander("👀 DEBUG: Parsed Skills", expanded=False):
        st.write(", ".join([f"**{s}**" for s in user_skills]))

    if st.button("🔥 Calculate Match", type="primary"):
        with st.spinner("Analyzing market..."):
            
            # Filtering
            filtered_df = df_jobs.copy()
            if selected_loc != "All Locations":
                filtered_df = filtered_df[filtered_df['Location'] == selected_loc]
            if only_remote:
                 filtered_df = filtered_df[
                     filtered_df['Location'].str.contains('Remote', case=False) | 
                     filtered_df['description'].str.contains('Remote', case=False)
                 ]
            
            if filtered_df.empty:
                st.warning("No jobs found with filters.")
            else:
                # Scoring
                descriptions = filtered_df['description'].tolist()
                scores = engine.calculate_hybrid_score(cv_text, descriptions, user_skills)
                filtered_df['Score'] = scores
                filtered_df = filtered_df.sort_values(by='Score', ascending=False).head(15)

                # Market Stats
                st.subheader("📊 Market Insights")
                all_market_skills = []
                for desc in filtered_df['description']:
                    all_market_skills.extend(engine.extract_skills(desc))
                if all_market_skills:
                    counts = Counter(all_market_skills).most_common(10)
                    market_df = pd.DataFrame(counts, columns=["Skill", "Count"])
                    st.bar_chart(market_df.set_index("Skill"))

                # Results
                st.subheader("🏆 Recommendations")
                
                for idx, row in filtered_df.iterrows():
                    missing = engine.analyze_gaps(user_skills, row['description'])
                    score = row['Score']
                    
                    if score >= 60: border_color = "🟢 HIGH"
                    elif score >= 40: border_color = "🟡 MED"
                    else: border_color = "🔴 LOW"

                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"### {row['title']}")
                            st.caption(f"**{row['company']}** | {row['Location']}")
                            st.markdown(f"**Status:** {border_color}")
                            
                            if missing:
                                st.info(f"💡 Missing: {', '.join(missing[:5])}")
                            else:
                                st.success("✅ Good match!")
                                
                            with st.expander("Show Description"):
                                st.write(row['description'])
                        
                        with c2:
                            st.metric("Score", f"{score}%")
                            st.progress(score/100)
                            
                            if row['url'] != "#":
                                st.link_button("Apply", row['url'])
                            
                            # === GEMINI BUTTON ===
                            # Мы используем уникальный ключ для popover, чтобы они не конфликтовали
                            with st.popover("🤖 Write Letter", help="Generate with Gemini AI"):
                                if not api_key:
                                    st.error("Please enter API Key in sidebar first!")
                                else:
                                    # Кнопка генерации внутри popover
                                    if st.button(f"Generate for {row['company']}", key=f"btn_{idx}"):
                                        letter = generate_cover_letter_gemini(
                                            api_key, cv_text, row['description'], row['company'], row['title']
                                        )
                                        st.text_area("Copy this:", value=letter, height=300)
else:
    st.info("👈 Upload CV to start.")