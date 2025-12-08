import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
import pdfplumber
import re
import os

# === EXTENDED SKILL LIST ===
TECH_KEYWORDS = [
    # Languages
    "python", "java", "c++", "c#", ".net", "javascript", "typescript", "html", "css", "sql", "nosql", "r", "bash", "go", "golang", "scala", "kotlin", "php", "ruby", "rust", "swift",
    # Data & AI
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "scikit-learn", "sklearn", "tensorflow", "keras", 
    "pytorch", "nlp", "opencv", "llm", "huggingface", "transformers", "xgboost", "lightgbm", "statistics", "probability",
    "power bi", "tableau", "looker", "excel", "dax", "alteryx", "etl", "data mining", "data warehousing",
    # Big Data
    "spark", "pyspark", "hadoop", "kafka", "hive", "airflow", "databricks", "snowflake", "bigquery", "redshift",
    # Web & Frameworks
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi", "spring boot", "asp.net", "rest api", "graphql",
    # Infrastructure & Tools
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "linux", "unix", "jenkins", "gitlab ci", "github actions", "terraform", "ansible",
    "git", "github", "gitlab", "jira", "confluence", "bitbucket",
    # Soft Skills & Concepts
    "agile", "scrum", "kanban", "english", "teamwork", "communication", "problem solving", "oop", "algorithms", "data structures"
]

class ScorerEngine:
    def __init__(self):
        print("Loading ML model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded.")

    def extract_text_from_pdf(self, uploaded_file):
        """
        Extract text using pdfplumber (better for multi-column layouts).
        """
        try:
            text = ""
            # pdfplumber.open works directly with the BytesIO object from Streamlit
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    # extract_text() handles layout analysis automatically
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Cleaning common artifacts
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"

    def extract_skills(self, text):
        """
        Smart skill extraction using word boundaries.
        """
        if not text: return []
        
        text_lower = " " + text.lower() + " "
        found = []
        
        # Replace special chars (except + and # for C++/C#) with spaces
        clean_text = re.sub(r'[^a-z0-9+#]', ' ', text_lower)
        
        for skill in TECH_KEYWORDS:
            if skill in ['c++', 'c#', '.net']:
                # For special languages, look for spaces around
                if f" {skill} " in clean_text:
                    found.append(skill)
            else:
                # Use regex word boundaries \b for standard words
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, clean_text):
                    found.append(skill)
                    
        return list(set(found))

    def calculate_hybrid_score(self, cv_text, job_descriptions, cv_skills):
        # 1. AI Semantic Score
        cv_emb = self.model.encode(cv_text, convert_to_tensor=True)
        job_embs = self.model.encode(job_descriptions, convert_to_tensor=True)
        semantic_scores = util.cos_sim(cv_emb, job_embs)[0].tolist()
        
        final_scores = []
        for i, desc in enumerate(job_descriptions):
            # 2. Keyword Match Score
            job_skills = self.extract_skills(desc)
            if not job_skills:
                keyword_match = semantic_scores[i]
            else:
                common = set(cv_skills).intersection(set(job_skills))
                keyword_match = len(common) / len(job_skills)
            
            # Weighted Average: 60% Semantic, 40% Keywords
            hybrid = (semantic_scores[i] * 0.6) + (keyword_match * 0.4)
            final_scores.append(round(hybrid * 100, 1))
        return final_scores

    def analyze_gaps(self, cv_skills, job_text):
        job_skills = set(self.extract_skills(job_text))
        user_skills = set(cv_skills)
        missing = list(job_skills - user_skills)
        return missing

# === FILTERS ===
def filter_fake_junior(df):
    # Regex to find "3+ years", "5 years", etc.
    high_exp_pattern = r'([3-9]|\d{2,})\+?\s*-?\s*years?'
    def is_fake(row):
        desc = str(row['description']).lower()
        if re.search(high_exp_pattern, desc): return True
        return False
    mask = df.apply(is_fake, axis=1)
    return df[~mask], sum(mask)

def load_real_db():
    df = pd.DataFrame()
    source_type = "unknown"
    
    # 1. Live Data
    if os.path.exists("live_jobs.csv"):
        try:
            print("🚀 Loading LIVE data...")
            df = pd.read_csv("live_jobs.csv")
            source_type = "live"
        except: pass

    # 2. Archive Data (Fallback)
    if df.empty and os.path.exists("Uncleaned_DS_jobs.csv"):
        try:
            print("⚠️ Loading ARCHIVE data...")
            df = pd.read_csv("Uncleaned_DS_jobs.csv")
            df = df.rename(columns={"Job Description": "description", "Job Title": "title", "Company Name": "company"})
            df['company'] = df['company'].apply(lambda x: x.split('\n')[0] if isinstance(x, str) else "Unknown")
            df['url'] = "#"
            df['Location'] = "Unknown"
            source_type = "archive"
        except: pass

    if df.empty: return pd.DataFrame()

    df = df.dropna(subset=['description', 'title'])
    
    # Hard Filter Senior
    senior_keywords = ['senior', 'sr.', 'lead', 'principal', 'manager', 'head', 'director', 'iii', 'iv']
    pattern = '|'.join(senior_keywords)
    df = df[~df['title'].str.lower().str.contains(pattern, case=False)]
    
    # Smart Filter
    df, deleted = filter_fake_junior(df)
    
    print(f"✅ Source: {source_type.upper()}. Loaded: {len(df)} jobs (Filtered {deleted} fake juniors).")
    
    return df