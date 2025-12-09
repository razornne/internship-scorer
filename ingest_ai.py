import google.generativeai as genai
import pandas as pd
import json
import toml
import os
import time

def get_api_key():
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        try:
            data = toml.load(secrets_path)
            if "GEMINI_API_KEY" in data: return data["GEMINI_API_KEY"]
        except: pass
    return input("Gemini API Key: ").strip()

def generate_synthetic_jobs(api_key):
    genai.configure(api_key=api_key)
    # Используем модель с большим контекстом, чтобы влезло 40 вакансий
    models = ['models/gemini-2.0-flash', 'models/gemini-1.5-pro-latest', 'gemini-1.5-flash']
    model = None
    
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            break
        except: continue
        
    if not model: return []
    
    print(f"🤖 Generating 40 jobs with {model} (this may take 30-40 seconds)...")

    prompt = """
    Generate 40 realistic IT job postings for Prague (Czechia).
    Output MUST be a valid JSON array.
    
    Keys per object: "title", "company", "description", "Location", "url" (set to "#").
    
    DISTRIBUTION:
    1. Valid Junior Roles (25 jobs):
       - Python Dev, Data Analyst, Java Junior, React Dev, QA Tester, DevOps Junior.
       - Varied stacks and companies.
       
    2. "TRAP" Roles (The fake juniors) (10 jobs):
       - Title must say "Junior" or "Intern".
       - BUT Description must explicitly demand "3+ years experience", "5 years commercial experience", or "Senior level knowledge".
       - These are to test my spam filter. Make them look tricky!
       
    3. Senior Roles (5 jobs):
       - Title says "Senior", "Lead", "Manager".
    
    Format: JSON Array only. No markdown.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error: {e}")
        return []

def save_to_csv(jobs):
    if not jobs: return
    df = pd.DataFrame(jobs)
    df["source"] = "Gemini Synthetic"
    df.to_csv("live_jobs.csv", index=False)
    print(f"🎉 Saved {len(df)} jobs (including TRAPS) to live_jobs.csv")

if __name__ == "__main__":
    key = get_api_key()
    if key: save_to_csv(generate_synthetic_jobs(key))