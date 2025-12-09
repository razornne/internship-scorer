import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
import pdfplumber
import re
import os

TECH_KEYWORDS = [
    "python", "java", "c++", "c#", ".net", "javascript", "typescript", "html", "css", "sql", "nosql", "r", "bash", "go", "golang", "scala", "kotlin", "php", "ruby", "rust", "swift",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "scikit-learn", "sklearn", "tensorflow", "keras", 
    "pytorch", "nlp", "opencv", "llm", "huggingface", "transformers", "xgboost", "lightgbm", "statistics", "probability",
    "power bi", "tableau", "looker", "excel", "dax", "alteryx", "etl", "data mining", "data warehousing",
    "spark", "pyspark", "hadoop", "kafka", "hive", "airflow", "databricks", "snowflake", "bigquery", "redshift",
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi", "spring boot", "asp.net", "rest api", "graphql",
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "linux", "unix", "jenkins", "gitlab ci", "github actions", "terraform", "ansible",
    "git", "github", "gitlab", "jira", "confluence", "bitbucket",
    "agile", "scrum", "kanban", "english", "teamwork", "communication", "problem solving", "oop", "algorithms", "data structures"
]

class ScorerEngine:
    def __init__(self):
        print("Loading ML model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded.")

    def extract_text_from_pdf(self, uploaded_file):
        try:
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: text += t + "\n"
            return text
        except Exception as e:
            return f"Error: {e}"

    def extract_skills(self, text):
        if not text: return []
        text_lower = " " + text.lower() + " "
        found = []
        clean_text = re.sub(r'[^a-z0-9+#]', ' ', text_lower)
        for skill in TECH_KEYWORDS:
            if skill in ['c++', 'c#', '.net']:
                if f" {skill} " in clean_text: found.append(skill)
            else:
                if re.search(r'\b' + re.escape(skill) + r'\b', clean_text): found.append(skill)
        return list(set(found))

    def calculate_hybrid_score(self, cv_text, job_descriptions, cv_skills):
        cv_emb = self.model.encode(cv_text, convert_to_tensor=True)
        job_embs = self.model.encode(job_descriptions, convert_to_tensor=True)
        semantic_scores = util.cos_sim(cv_emb, job_embs)[0].tolist()
        
        final_scores = []
        for i, desc in enumerate(job_descriptions):
            job_skills = self.extract_skills(desc)
            if not job_skills:
                keyword_match = semantic_scores[i]
            else:
                common = set(cv_skills).intersection(set(job_skills))
                keyword_match = len(common) / len(job_skills)
            
            hybrid = (semantic_scores[i] * 0.6) + (keyword_match * 0.4)
            final_scores.append(round(hybrid * 100, 1))
        return final_scores

    def analyze_gaps(self, cv_skills, job_text):
        job_skills = set(self.extract_skills(job_text))
        return list(job_skills - set(cv_skills))

# === ЛОГИКА "ДЕТЕКТОРА ЛОВУШЕК" ===
def tag_jobs(df):
    """
    Вместо удаления, мы помечаем плохие вакансии статусом.
    """
    df['filter_status'] = 'Active' # По умолчанию все хорошие
    
    # 1. Помечаем Senior позиции
    senior_keywords = ['senior', 'sr.', 'lead', 'principal', 'manager', 'head', 'director', 'iii', 'iv']
    pattern = '|'.join(senior_keywords)
    mask_senior = df['title'].str.lower().str.contains(pattern, case=False)
    df.loc[mask_senior, 'filter_status'] = '⛔ Senior Role'

    # 2. Помечаем Fake Juniors (3+ years experience)
    high_exp_pattern = r'([3-9]|\d{2,})\+?\s*-?\s*years?'
    def is_fake(desc):
        return bool(re.search(high_exp_pattern, str(desc).lower()))
    
    mask_fake = df['description'].apply(is_fake)
    # Помечаем только если это еще не Senior (чтобы не перезаписать)
    df.loc[mask_fake & (df['filter_status'] == 'Active'), 'filter_status'] = '⚠️ Fake Junior (3+ years exp)'
    
    return df

def load_real_db():
    df = pd.DataFrame()
    if os.path.exists("live_jobs.csv"):
        try: df = pd.read_csv("live_jobs.csv")
        except: pass
        
    if df.empty: return pd.DataFrame()

    df = df.dropna(subset=['description', 'title'])
    
    # Применяем разметку (Тэгирование)
    df = tag_jobs(df)
    
    print(f"✅ Loaded {len(df)} jobs. Traps identified.")
    return df