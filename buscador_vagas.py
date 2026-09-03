import requests
import json
import re
from datetime import datetime

STACKS = [
    "Node.js", "TypeScript", "NestJS", "Express",
    "React", "Next.js", "Vue.js", "Angular", "React Native",
    "Java", "Spring Boot", "C#", ".NET", "Python", "Django", "FastAPI", "PHP", "Laravel", "Go", "Ruby on Rails",
    "PostgreSQL", "MySQL", "MongoDB",
    "Docker", "AWS", "Kubernetes"
]

VALID_LOCATION_KEYWORDS = [
    "latam", "latin america", "brazil", "brasil", "south america", 
    "worldwide", "anywhere in the world", "global"
]

def is_valid_location(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in VALID_LOCATION_KEYWORDS)

def fetch_jobicy():
    jobs = []
    url = "https://jobicy.com/api/v2/remote-jobs?count=50"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("jobs", []):
                geo = item.get("jobGeo", "")
                desc = item.get("jobDescription", "")
                title = item.get("jobTitle", "")
                full_text = f"{geo} {desc} {title}"
                
                if is_valid_location(full_text):
                    jobs.append({
                        "title": title,
                        "url": item.get("url"),
                        "description": desc
                    })
    except Exception as e:
        print(f"Erro Jobicy: {e}")
    return jobs

def fetch_arbeitnow():
    jobs = []
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                if item.get("remote", False):
                    desc = item.get("description", "")
                    title = item.get("title", "")
                    location = item.get("location", "")
                    full_text = f"{desc} {title} {location}"
                    
                    if is_valid_location(full_text):
                        jobs.append({
                            "title": title,
                            "url": item.get("url"),
                            "description": desc
                        })
    except Exception as e:
        print(f"Erro Arbeitnow: {e}")
    return jobs

def main():
    print("Iniciando busca de vagas...")
    all_jobs = []
    all_jobs.extend(fetch_jobicy())
    all_jobs.extend(fetch_arbeitnow())
    
    categorized_jobs = {stack: [] for stack in STACKS}
    
    for job in all_jobs:
        text_corp = f"{job['title']} {job['description']}".lower()
        for stack in STACKS:
            if len(categorized_jobs[stack]) >= 4:
                continue
            if stack.lower() in text_corp:
                if not any(j['url'] == job['url'] for j in categorized_jobs[stack]):
                    categorized_jobs[stack].append({
                        "title": job['title'],
                        "url": job['url']
                    })

    today_str = datetime.now().strftime("%d/%m/%Y")
    md_content = f"**Hello Guys!**\n"
    md_content += f"Segue nossa lista de vagas de hoje! ({today_str})\n\n"
    
    total_found = 0
    for stack, jobs in categorized_jobs.items():
        if not jobs:
            continue
        total_found += len(jobs)
        md_content += f"--- {stack.upper()} ---\n\n"
        for job in jobs:
            md_content += f"**{job['title']}**\n"
            md_content += f"{job['url']}\n\n"

    if total_found == 0:
        md_content += "Nenhuma vaga encontrada hoje.\n"

    with open("VAGAS_DO_DIA.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Sucesso! {total_found} vagas geradas.")

if __name__ == "__main__":
    main()
