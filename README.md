````markdown
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

## 🛠 Tech Stack
* **Language:** Python 3.10+
* **Frontend:** Streamlit
* **ML & NLP:** PyTorch, Sentence-Transformers (`all-MiniLM-L6-v2`), Scikit-learn
* **Data Processing:** Pandas, NumPy
* **Visualization:** Plotly
* **Data Ingestion:** Requests, BeautifulSoup4

## 🚀 How to Run Locally

### 1. Clone the repository
```bash
git clone [https://github.com/YOUR_USERNAME/internship-scorer.git](https://github.com/YOUR_USERNAME/internship-scorer.git)
cd internship-scorer
````

### 2\. Create a virtual environment & install dependencies

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

### 3\. Get Data (Optional)

The app comes with a fallback dataset, but you can generate fresh mock data or fetch live data:

```bash
# Generate fresh mock data (Prague context)
python ingest_fake.py
```

*(Or use `ingest.py` if you have a RapidAPI key)*

### 4\. Run the App

```bash
streamlit run app.py
```

## 📂 Project Structure

  * `app.py`: Main Streamlit interface and visualization logic.
  * `core.py`: The "Brain". Contains ML model, PDF parsing, scoring logic, and filters.
  * `ingest_fake.py`: Generates realistic mock data for testing/demo purposes.
  * `ingest.py`: Script for fetching real data via JSearch API.
  * `live_jobs.csv`: The current database of jobs.

-----

*Created by Mykyta Bulatnikov*
