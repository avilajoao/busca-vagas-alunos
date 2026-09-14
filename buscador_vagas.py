import requests
import json
import re
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

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
                
                if is_strict_latam(full_text):
                    jobs.append({
                        "title": title,
                        "url": item.get("url")
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
                    
                    if is_strict_latam(full_text):
                        jobs.append({
                            "title": title,
                            "url": item.get("url")
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
                
                if is_strict_latam(full_text):
                    jobs.append({
                        "title": title,
                        "url": link
                    })
    except Exception as e:
        print(f"Erro WeWorkRemotely: {e}")
    return jobs

def main():
    print("Buscando vagas LATAM nas últimas 24h (formato direto de lista)...")
    
    history = load_history()
    today_key = datetime.now().strftime("%Y-%m-%d")
    
    all_jobs = []
    all_jobs.extend(fetch_jobicy())
    all_jobs.extend(fetch_arbeitnow())
    all_jobs.extend(fetch_weworkremotely())
    
    global_used_urls = set(history.keys())
    valid_unique_jobs = []
    
    for job in all_jobs:
        job_url = job['url']
        if job_url not in global_used_urls:
            valid_unique_jobs.append(job)
            global_used_urls.add(job_url)
            history[job_url] = today_key

    today_str = datetime.now().strftime("%d/%m/%Y")
    md_content = f"**Hello Guys!**\n"
    md_content += f"Segue nossa lista de vagas de hoje! ({today_str})\n\n"
    
    if valid_unique_jobs:
        for job in valid_unique_jobs:
            md_content += f"{job['title']}\n"
            md_content += f"{job['url']}\n\n"
    else:
        md_content += "Nenhuma vaga nova publicada nas últimas 24h.\n"

    with open("VAGAS_DO_DIA.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    save_history(history)
    print(f"Sucesso! {len(valid_unique_jobs)} vagas listadas no formato simplificado.")

if __name__ == "__main__":
    main()
