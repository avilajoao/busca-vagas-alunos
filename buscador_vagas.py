import requests
import json
import re
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Grupos de tecnologias correlatas (unidas por categoria)
STACK_GROUPS = {
    "Node.js / Express / NestJS": ["node", "express", "nestjs"],
    "React / Next.js / React Native": ["react", "next.js", "nextjs", "react native"],
    "TypeScript / JavaScript": ["typescript", "javascript"],
    "Vue.js / Nuxt": ["vue", "nuxt"],
    "Angular": ["angular"],
    "Java / Spring Boot": ["java", "spring boot", "springboot"],
    "C# / .NET": ["c#", ".net", "dotnet"],
    "Python / Django / FastAPI": ["python", "django", "fastapi", "flask"],
    "PHP / Laravel": ["php", "laravel"],
    "Go": ["golang", "go "],
    "Ruby on Rails": ["ruby", "rails"],
    "Bancos de Dados (SQL / NoSQL)": ["postgresql", "postgres", "mysql", "mongodb"],
    "DevOps & Nuvem (Docker / AWS / K8s)": ["docker", "aws", "kubernetes", "k8s"]
}

VALID_LOCATION_KEYWORDS = [
    "latam", "latin america", "brazil", "brasil", "south america", 
    "worldwide", "anywhere in the world", "global"
]

HISTORY_FILE = "historico_vagas.json"

def load_history():
    """Carrega o histórico de URLs enviadas nos últimos 30 dias"""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Limpa histórico com mais de 30 dias
            cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            return {url: date for url, date in data.items() if date >= cutoff}
    except Exception as e:
        print(f"Aviso ao carregar histórico: {e}")
        return {}

def save_history(history):
    """Salva o histórico atualizado de URLs"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")

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

def fetch_weworkremotely():
    jobs = []
    url = "https://weworkremotely.com/remote-jobs.rss"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall('./channel/item'):
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                full_text = f"{title} {desc}"
                
                if is_valid_location(full_text):
                    jobs.append({
                        "title": title,
                        "url": link,
                        "description": desc
                    })
    except Exception as e:
        print(f"Erro WeWorkRemotely: {e}")
    return jobs

def main():
    print("Iniciando busca de vagas sem repetição...")
    
    history = load_history()
    today_key = datetime.now().strftime("%Y-%m-%d")
    
    all_jobs = []
    all_jobs.extend(fetch_jobicy())
    all_jobs.extend(fetch_arbeitnow())
    all_jobs.extend(fetch_weworkremotely())
    
    categorized_jobs = {group: [] for group in STACK_GROUPS}
    global_used_urls = set(history.keys())
    
    for job in all_jobs:
        job_url = job['url']
        
        # Ignora vagas já enviadas anteriormente
        if job_url in global_used_urls:
            continue
            
        text_corp = f"{job['title']} {job['description']}".lower()
        
        for group_name, keywords in STACK_GROUPS.items():
            if len(categorized_jobs[group_name]) >= 4:
                continue
            
            # Checa se a vaga combina com alguma palavra-chave do grupo
            if any(kw in text_corp for kw in keywords):
                categorized_jobs[group_name].append({
                    "title": job['title'],
                    "url": job_url
                })
                global_used_urls.add(job_url)
                history[job_url] = today_key
                break  # Evita atribuir a mesma vaga a múltiplos grupos

    today_str = datetime.now().strftime("%d/%m/%Y")
    md_content = f"**Hello Guys!**\n"
    md_content += f"Segue nossa lista de vagas de hoje! ({today_str})\n\n"
    
    total_found = 0
    for group_name, jobs in categorized_jobs.items():
        if not jobs:
            continue
        total_found += len(jobs)
        md_content += f"--- {group_name.upper()} ---\n\n"
        for job in jobs:
            md_content += f"**{job['title']}**\n"
            md_content += f"{job['url']}\n\n"

    if total_found == 0:
        md_content += "Nenhuma vaga nova encontrada hoje.\n"

    with open("VAGAS_DO_DIA.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    save_history(history)
    print(f"Sucesso! {total_found} vagas inéditas organizadas.")

if __name__ == "__main__":
    main()
