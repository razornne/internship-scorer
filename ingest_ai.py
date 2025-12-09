import google.generativeai as genai
import pandas as pd
import json
import toml
import os

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
    models = ['models/gemini-2.0-flash', 'gemini-1.5-flash']
    model = None
    
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            break
        except: continue
        
    if not model: return []
    print(f"🤖 Generating jobs with {m}...")

    prompt = """
    Generate 15 realistic job postings for Junior/Intern IT roles in Prague (Czechia).
    Output: JSON array of objects with keys: "title", "company", "description", "Location", "url" (set to "#").
    Diversity: Python, Data, React, Java, DevOps.
    Include 2 "TRAP" jobs (Junior title but 3+ years exp required).
    Return ONLY JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(e)
        return []

def save_to_csv(jobs):
    if not jobs: return
    df = pd.DataFrame(jobs)
    df["source"] = "Gemini Synthetic"
    df.to_csv("live_jobs.csv", index=False)
    print(f"🎉 Saved {len(df)} jobs to live_jobs.csv")

if __name__ == "__main__":
    key = get_api_key()
    if key: save_to_csv(generate_synthetic_jobs(key))