# 🚀 AI Internship Scorer

**An intelligent career assistant for students and juniors in IT.**
It aggregates real-time jobs, filters out "fake" entry-level roles, and calculates your hiring chances using Machine Learning.

🔗 **Live Demo:** [Open App](https://internship-scorer-qz938xauxqfprc9b3cuq6b.streamlit.app/)

---

## 🎯 The Problem
Finding a true entry-level job is broken:
* **Noise:** Job boards are flooded with "Junior" roles requiring 3+ years of experience.
* **Mismatch:** Simple keyword search misses opportunities where skills are described differently.
* **Uncertainty:** It's hard to know exactly which skills you are missing for a specific role.

## 💡 The Solution
This app acts as a smart filter between you and the job market. It uses **Hybrid Search** (Vectors + Keywords) to provide a transparent match score.

### Key Features
* **🕵️‍♂️ Live Data Aggregation:** Scrapes real jobs (focused on Prague/Remote) via JSearch API or local scrapers.
* **🧠 AI Hybrid Matching:** Combines `sentence-transformers` (Semantic Search) with hard keyword matching for high accuracy.
* **🛡️ Smart Filters:**
    * **Anti-Senior:** Automatically removes Lead, Senior, and Manager roles.
    * **Fake Junior Detector:** Scans descriptions for "3+ years experience" requirements and flags/removes them.
* **📊 Actionable Analytics:**
    * **Traffic Light System:** 🟢 Apply Now / 🟡 Learning Gap / 🔴 Low Chance.
    * **Skill-Gap Analysis:** Identifies exactly which skills you need to learn.
    * **Market Insights:** Visualizes top requested skills in the current job pool.
* **📝 AI Cover Letter Generator:** Generates personalized cover letters tailored to your resume and the specific job description using Google Gemini API.

## 🛠 Tech Stack
* **Language:** Python 3.10+
* **Frontend:** Streamlit
* **ML & NLP:** PyTorch, Sentence-Transformers (`all-MiniLM-L6-v2`), Scikit-learn
* **LLM:** Google Gemini API (2.0 Flash / 1.5 Pro)
* **Data Processing:** Pandas, NumPy
* **Visualization:** Plotly
* **Data Ingestion:** Requests, BeautifulSoup4

---
*Created by Nikita*
