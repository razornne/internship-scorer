import streamlit as st
import pandas as pd
from collections import Counter
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
uploaded_file = st.sidebar.file_uploader("Upload CV (PDF)", type="pdf")
manual_text = st.sidebar.text_area("Or paste text manually:", height=150)

st.sidebar.divider()
st.sidebar.subheader("🌍 Filters")

if not df_jobs.empty:
    # Ensure locations are strings and handle potential mixed types
    unique_locs = sorted(df_jobs['Location'].astype(str).unique().tolist())
    locations = ["All Locations"] + unique_locs
    selected_loc = st.sidebar.selectbox("Location", locations)
    only_remote = st.sidebar.checkbox("Remote only")
else:
    st.sidebar.error("Job database is empty!")

# === MAIN ===
st.title("🚀 AI Internship Scorer")
st.caption("Smart job aggregator & analyzer for Junior positions")

if df_jobs.empty:
    st.error("No jobs found. Please run `python ingest_fake.py` (for demo) or `python ingest.py` (for real data).")
    st.stop()

# CV Processing
cv_text = ""
if uploaded_file:
    cv_text = engine.extract_text_from_pdf(uploaded_file)
elif manual_text:
    cv_text = manual_text

if cv_text:
    # Extract Skills
    user_skills = engine.extract_skills(cv_text)
    
    # === DEBUG BLOCK ===
    with st.expander("👀 DEBUG: What did AI find in your CV?", expanded=True):
        if user_skills:
            st.success(f"Found {len(user_skills)} skills.")
            st.write(", ".join([f"**{s}**" for s in user_skills]))
        else:
            st.error("⚠️ No skills found! Make sure your CV is in English and contains standard tech keywords.")
            st.text("Raw text preview (first 300 chars):")
            st.caption(cv_text[:300] + "...")

    # Action Button
    if st.button("🔥 Calculate Match", type="primary"):
        with st.spinner("Analyzing the market..."):
            
            # Filtering
            filtered_df = df_jobs.copy()
            
            if selected_loc != "All Locations":
                filtered_df = filtered_df[filtered_df['Location'] == selected_loc]
            
            if only_remote:
                 # Filter by 'Remote' in Location OR Description
                 filtered_df = filtered_df[
                     filtered_df['Location'].str.contains('Remote', case=False) | 
                     filtered_df['description'].str.contains('Remote', case=False)
                 ]
            
            if filtered_df.empty:
                st.warning("No jobs found with current filters.")
            else:
                # Scoring
                descriptions = filtered_df['description'].tolist()
                scores = engine.calculate_hybrid_score(cv_text, descriptions, user_skills)
                filtered_df['Score'] = scores
                
                # Sort and pick top 15
                filtered_df = filtered_df.sort_values(by='Score', ascending=False).head(15)

                # === MARKET ANALYSIS ===
                st.subheader("📊 Top 10 Requested Skills (in this selection)")
                all_market_skills = []
                for desc in filtered_df['description']:
                    all_market_skills.extend(engine.extract_skills(desc))
                
                if all_market_skills:
                    counts = Counter(all_market_skills).most_common(10)
                    market_df = pd.DataFrame(counts, columns=["Skill", "Count"])
                    st.bar_chart(market_df.set_index("Skill"))

                # === JOB LIST ===
                st.subheader("🏆 Your Personal Recommendations")
                
                for idx, row in filtered_df.iterrows():
                    missing = engine.analyze_gaps(user_skills, row['description'])
                    score = row['Score']
                    
                    # Status Logic
                    if score >= 60: border_color = "🟢 HIGH CHANCE"
                    elif score >= 40: border_color = "🟡 MEDIUM CHANCE"
                    else: border_color = "🔴 LOW CHANCE"

                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"### {row['title']}")
                            st.caption(f"**{row['company']}** | {row['Location']}")
                            st.markdown(f"**Status:** {border_color}")
                            
                            if missing:
                                st.info(f"💡 **Missing Skills:** {', '.join(missing[:5])}")
                            else:
                                st.success("✅ Perfect Stack Match!")
                                
                            with st.expander("Show Description"):
                                st.write(row['description'])
                        
                        with c2:
                            st.metric("Match Score", f"{score}%")
                            st.progress(score/100)
                            if row['url'] and row['url'] != "#":
                                st.link_button("Apply Now", row['url'])
else:
    st.info("👈 Upload your CV on the left to start.")