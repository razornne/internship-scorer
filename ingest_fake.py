import pandas as pd
import random

def generate_mock_jobs():
    print("⚠️ API не отвечает, генерируем синтетические данные для Праги...")

    # Базы для генерации
    companies = ["Avast", "JetBrains", "Kiwi.com", "Productboard", "Pure Storage", "Oracle", "Microsoft", "Seznam.cz", "Rohlik Group", "Barclays"]
    titles_junior = ["Junior Python Developer", "Intern Data Analyst", "Junior Software Engineer", "Python Intern", "Entry-level Data Scientist", "Junior Backend Developer"]
    titles_senior = ["Senior Python Developer", "Lead Data Scientist", "Senior Software Engineer", "Team Lead", "Principal Engineer"]
    
    # Шаблоны описаний (с ключевыми словами)
    desc_templates = [
        "We are looking for a {role} to join our team in Prague. You will work with {stack}. Requirements: Basic knowledge of {stack}, Git, and English. Great opportunity for students.",
        "Join our fast-growing startup as a {role}. Stack: {stack}. We offer flexible hours and remote options.",
        "Hiring a {role}! If you know {stack} and want to learn more, apply now. Mentorship program available.",
        "Requires 5+ years of experience in {stack}. Leading a team of developers.", # Ловушка для фильтра
        "Looking for a passionate {role}. Must have experience with {stack}, Docker, and CI/CD."
    ]

    tech_stacks = ["Python, SQL, Pandas", "Java, Spring Boot", "Python, Django, React", "Data Analysis, SQL, Tableau", "Machine Learning, PyTorch, Python"]

    jobs = []

    # 1. Генерируем 15 идеальных JUNIOR вакансий
    for _ in range(15):
        stack = random.choice(tech_stacks)
        title = random.choice(titles_junior)
        desc = random.choice(desc_templates[:3]).format(role=title, stack=stack)
        
        jobs.append({
            "title": title,
            "company": random.choice(companies),
            "description": desc,
            "Location": random.choice(["Prague (Czechia)", "Remote / Prague"]),
            "url": "https://www.startupjobs.cz/en",
            "source": "Mock Data"
        })

    # 2. Генерируем 5 SENIOR вакансий (чтобы проверить работу фильтров Anti-Senior)
    for _ in range(5):
        stack = random.choice(tech_stacks)
        title = random.choice(titles_senior)
        desc = "We need a Senior expert with 5+ years of experience. High salary."
        
        jobs.append({
            "title": title,
            "company": random.choice(companies),
            "description": desc,
            "Location": "Prague (Czechia)",
            "url": "#",
            "source": "Mock Data"
        })

    # 3. Генерируем 3 "Фейковых Джуна" (Junior title, но 3+ years experience) - проверка Smart Filter
    for _ in range(3):
        jobs.append({
            "title": "Junior Python Developer",
            "company": "Bad Corp",
            "description": "Looking for a Junior dev. Must have 4+ years of commercial experience in Python.",
            "Location": "Prague (Czechia)",
            "url": "#",
            "source": "Mock Data"
        })

    # Сохраняем
    df = pd.DataFrame(jobs)
    df.to_csv("live_jobs.csv", index=False)
    print(f"✅ УСПЕХ! Сгенерировано {len(df)} вакансий в 'live_jobs.csv'.")
    print("   - Из них настоящих Junior: ~15")
    print("   - Ловушек (Senior/Fake): ~8 (они должны исчезнуть в приложении)")
    print("🚀 Запускай: streamlit run app.py")

if __name__ == "__main__":
    generate_mock_jobs()