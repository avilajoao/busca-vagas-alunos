import requests
import json
import re
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# Grupos de tecnologias correlatas
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

# Filtro estrito e primordial para LATAM / Brasil
PRIMORDIAL_LATAM_KEYWORDS = [
    "latam", "latin america", "latinamerica", "south america", 
    "brazil", "brasil"
]

HISTORY_FILE = "historico_vagas.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            return {url: date for url, date in data.items() if date >= cutoff}
    except Exception as e:
        print(f"Aviso ao carregar histórico: {e}")
        return {}

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")

def is_strict_latam(text_to_check):
    """Valida se a vaga é estritamente destinada para LATAM/Brasil"""
    text_lower = text_to_check.lower()
    return any(kw in text_lower for kw in PRIMORDIAL_LATAM_KEYWORDS)

def is_within_24h(pub_date):
    """Verifica se a data de publicação foi nas últimas 24 horas"""
    if not pub_date:
        return True
    now = datetime.now(timezone.utc)
    if pub_date.tzinfo is None:
        pub_date = pub_date.replace(tzinfo=timezone.utc)
    return (now - pub_date) <= timedelta(hours=24)

def fetch_jobicy():
    jobs = []
    url = "https://jobicy.com/api/v2/remote-jobs?count=50"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("jobs", []):
                # Validar data de até 24h
                pub_str = item.get("pubDate", "")
                pub_date = None
                if pub_str:
                    try:
                        pub_date = datetime.strptime(pub_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    except ValueError:
                        pass
                
                if not is_within_24h(pub_date):
                    continue

                geo = item.get("jobGeo", "")
                desc = item.get("jobDescription", "")
                title = item.get("jobTitle", "")
                full_text = f"{geo} {desc} {title}"
                
                # Validação primordial para LATAM
                if is_strict_latam(full_text):
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
                    created_at = item.get("created_at")
                    pub_date = None
                    if created_at:
                        try:
                            pub_date = datetime.fromtimestamp(created_at, tz=timezone.utc)
                        except Exception:
                            pass
                    
                    if not is_within_24h(pub_date):
                        continue

                    desc = item.get("description", "")
                    title = item.get("title", "")
                    location = item.get("location", "")
                    full_text = f"{desc} {title} {location}"
                    
                    # Validação primordial para LATAM
                    if is_strict_latam(full_text):
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
                pub_node = item.find('pubDate')
                pub_date = None
                if pub_node is not None and pub_node.text:
                    try:
                        pub_date = parsedate_to_datetime(pub_node.text)
                    except Exception:
                        pass
                
                if not is_within_24h(pub_date):
                    continue

                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                full_text = f"{title} {desc}"
                
                # Validação primordial para LATAM
                if is_strict_latam(full_text):
                    jobs.append({
                        "title": title,
                        "url": link,
                        "description": desc
                    })
    except Exception as e:
        print(f"Erro WeWorkRemotely: {e}")
    return jobs

def main():
    print("Iniciando busca com filtro estrito e primordial para LATAM (últimas 24h)...")
    
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
        
        if job_url in global_used_urls:
            continue
            
        text_corp = f"{job['title']} {job['description']}".lower()
        
        for group_name, keywords in STACK_GROUPS.items():
            if len(categorized_jobs[group_name]) >= 4:
                continue
            
            if any(kw in text_corp for kw in keywords):
                categorized_jobs[group_name].append({
                    "title": job['title'],
                    "url": job_url
                })
                global_used_urls.add(job_url)
                history[job_url] = today_key
                break

    today_str = datetime.now().strftime("%d/%m/%Y")
    md_content = f"**Hello Guys!**\n"
    md_content += f"Segue nossa lista de vagas exclusivas LATAM das últimas 24h! ({today_str})\n\n"
    
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
        md_content += "Nenhuma vaga estritamente LATAM publicada nas últimas 24h para estas stacks.\n"

    with open("VAGAS_DO_DIA.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    save_history(history)
    print(f"Sucesso! {total_found} vagas estritamente LATAM encontradas.")

if __name__ == "__main__":
    main()
