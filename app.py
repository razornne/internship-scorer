import streamlit as st
import pandas as pd
import plotly.express as px
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
st.sidebar.title("👨‍💻 Твой профиль")
uploaded_file = st.sidebar.file_uploader("Загрузи CV (PDF)", type="pdf")
manual_text = st.sidebar.text_area("Или вставь текст вручную:", height=150)

st.sidebar.divider()
st.sidebar.subheader("🌍 Фильтры")
if not df_jobs.empty:
    locations = ["All Locations"] + sorted(df_jobs['Location'].astype(str).unique().tolist())
    selected_loc = st.sidebar.selectbox("Город", locations)
    only_remote = st.sidebar.checkbox("Только удаленка")
else:
    st.sidebar.error("База вакансий пуста!")

# === MAIN ===
st.title("🚀 AI Internship Scorer")

if df_jobs.empty:
    st.error("Нет вакансий. Запусти сначала `python ingest_fake.py` (для теста) или `ingest.py` (реальные данные).")
    st.stop()

# Чтение резюме
cv_text = ""
if uploaded_file:
    cv_text = engine.extract_text_from_pdf(uploaded_file)
elif manual_text:
    cv_text = manual_text

if cv_text:
    # Ищем навыки
    user_skills = engine.extract_skills(cv_text)
    
    # === БЛОК ПРОВЕРКИ (DEBUG) ===
    with st.expander("👀 ПРОВЕРКА: Что AI нашел в резюме?", expanded=True):
        if user_skills:
            st.success(f"Найдено {len(user_skills)} навыков.")
            st.write(", ".join([f"**{s}**" for s in user_skills]))
        else:
            st.error("⚠️ Навыки не найдены! Проверь, что текст резюме на английском и содержит ключевые слова.")
            st.text("Текст, который видит робот (первые 300 символов):")
            st.caption(cv_text[:300] + "...")

    if st.button("🔥 Оценить шансы", type="primary"):
        with st.spinner("Анализируем рынок..."):
            
            # Фильтрация
            filtered_df = df_jobs.copy()
            if selected_loc != "All Locations":
                filtered_df = filtered_df[filtered_df['Location'] == selected_loc]
            if only_remote:
                 filtered_df = filtered_df[
                     filtered_df['Location'].str.contains('Remote', case=False) | 
                     filtered_df['description'].str.contains('Remote', case=False)
                 ]
            
            if filtered_df.empty:
                st.warning("Вакансии не найдены по фильтрам.")
            else:
                # Скоринг
                descriptions = filtered_df['description'].tolist()
                scores = engine.calculate_hybrid_score(cv_text, descriptions, user_skills)
                filtered_df['Score'] = scores
                filtered_df = filtered_df.sort_values(by='Score', ascending=False).head(15)

                # === АНАЛИЗ РЫНКА (ПРОСТОЙ) ===
                st.subheader("📊 Топ-10 навыков в этих вакансиях")
                all_market_skills = []
                for desc in filtered_df['description']:
                    all_market_skills.extend(engine.extract_skills(desc))
                
                if all_market_skills:
                    counts = Counter(all_market_skills).most_common(10)
                    market_df = pd.DataFrame(counts, columns=["Skill", "Count"])
                    # Простой бар-чарт (работает стабильнее паутинки)
                    st.bar_chart(market_df.set_index("Skill"))

                # === СПИСОК ВАКАНСИЙ ===
                st.subheader("🏆 Твои персональные рекомендации")
                
                for idx, row in filtered_df.iterrows():
                    missing = engine.analyze_gaps(user_skills, row['description'])
                    score = row['Score']
                    
                    if score >= 60: border_color = "🟢 HIGH CHANCE"
                    elif score >= 40: border_color = "🟡 MEDIUM CHANCE"
                    else: border_color = "🔴 LOW CHANCE"

                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"### {row['title']}")
                            st.caption(f"**{row['company']}** | {row['Location']}")
                            st.markdown(f"**Статус:** {border_color}")
                            
                            if missing:
                                st.info(f"💡 **Подтянуть:** {', '.join(missing[:5])}")
                            else:
                                st.success("✅ Твой стек полностью подходит!")
                                
                            with st.expander("Описание"):
                                st.write(row['description'])
                        
                        with c2:
                            st.metric("Совпадение", f"{score}%")
                            st.progress(score/100)
                            if row['url'] and row['url'] != "#":
                                st.link_button("Apply Now", row['url'])
else:
    st.info("👈 Загрузи резюме слева, чтобы начать.")