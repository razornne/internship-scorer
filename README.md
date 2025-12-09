# AI Internship Scorer

A practical career tool for students and junior engineers.

**Live Demo:** [Open App](https://internship-scorer.streamlit.app/)


## Problem

Entry-level job search is inefficient. Most "junior" listings require years of experience, keyword search misses relevant roles, and candidates have no clear visibility into their actual skill gaps.

## Solution

A hybrid-search scoring system that evaluates job compatibility using semantic embeddings and explicit keyword requirements. The app serves as a transparent filter on top of the job market.

## Features

**Live Aggregation**  
Pulls real job postings (Prague/Remote) via JSearch API or local scrapers.

**Hybrid AI Matching**  
Combines sentence-transformer embeddings with keyword matching for stable, interpretable results.

**Filtering Logic**  
- Removes senior/lead/manager roles by pattern detection.  
- Flags “fake junior” postings that demand multi-year experience.

**Scoring & Insights**  
- Traffic-light score: strong fit / partial fit / low fit.  
- Skill-gap extraction: highlights missing competencies.  
- Market insights: skill frequency, trends, and distributions.

## Tech Stack

- Python 3.10+  
- Streamlit  
- PyTorch, Sentence-Transformers, scikit-learn  
- Pandas, NumPy  
- Plotly  
- Requests, BeautifulSoup4

## Running Locally

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/internship-scorer.git
cd internship-scorer
````

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

Optional: generate data or fetch fresh listings:

```bash
python ingest_fake.py         # mock Prague dataset
# or
python ingest.py              # requires RapidAPI key
```

Start the app:

```bash
streamlit run app.py
```

## Project Structure

* `app.py` — Streamlit UI and visualizations
* `core.py` — ML models, scoring logic, filtering pipeline
* `ingest_fake.py` — mock job generator
* `ingest.py` — live data ingestion
* `live_jobs.csv` — current job dataset

---

Created by Mykyta Bulatnikov
---

