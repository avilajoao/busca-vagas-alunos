import requests
import json
import re
from datetime import datetime

# Lista de stacks/tecnologias baseada na planilha dos seus alunos
STACKS = [
    # Fullstack & Backend JavaScript / TypeScript
    "Node.js", "TypeScript", "NestJS", "Express",
    # Frontend & Mobile
    "React", "Next.js", "Vue.js", "Angular", "React Native",
    # Backend & Frameworks
    "Java", "Spring Boot", "C#", ".NET", "Python", "Django", "FastAPI", "PHP", "Laravel", "Go", "Ruby on Rails",
    # Bancos de Dados
    "PostgreSQL", "MySQL", "MongoDB",
    # DevOps & Infra
    "Docker", "AWS", "Kubernetes"
]

# Palavras-chave indicativas de LATAM / Remote Worldwide
LATAM_KEYWORDS = [
    "latam", "latin america", "brazil", "brasil", "south america", 
    "anywhere in the world", "worldwide", "global", "remote worldwide"
]

def check_is_latam(text_to_check):
    text_lower = text_to_check.lower()
    for kw in LATAM_KEYWORDS:
        if kw in text_lower:
            return True
    return False

def extract_english_requirement(description):
    if not description:
        return "Não especificado na descrição"
    
    # Procura sentenças ou linhas contendo a palavra english
    lines = re.split(r'[\n\.\!\?]', description)
    matched_lines = []
    for line in lines:
        if "english" in line.lower():
            clean_line = line.strip()
            if len(clean_line) > 10 and len(clean_line) < 200:
                matched_lines.append(clean_line)
    
    if matched_lines:
        return " | ".join(matched_lines[:2])
    return "Menciona inglês na descrição / Avaliação manual recomendada"

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
                full_text = f"{geo} {desc} {item.get('jobTitle', '')}"
                
                # Se for LATAM / Worldwide
                if check_is_latam(full_text) or not geo or "Worldwide" in geo:
                    jobs.append({
                        "title": item.get("jobTitle"),
                        "company": item.get("companyName"),
                        "url": item.get("url"),
                        "source": "Jobicy",
                        "description": desc,
                        "location": geo or "Worldwide/LATAM"
                    })
    except Exception as e:
        print(f"Erro ao buscar Jobicy: {e}")
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
                    full_text = f"{desc} {title} {item.get('location', '')}"
                    
                    if check_is_latam(full_text) or "remote" in item.get("location", "").lower():
                        jobs.append({
                            "title": title,
                            "company": item.get("company_name"),
                            "url": item.get("url"),
                            "source": "Arbeitnow",
                            "description": desc,
                            "location": item.get("location", "Remote")
                        })
    except Exception as e:
        print(f"Erro ao buscar Arbeitnow: {e}")
    return jobs

def main():
    print("Iniciando busca de vagas diárias para LATAM...")
    
    all_jobs = []
    all_jobs.extend(fetch_jobicy())
    all_jobs.extend(fetch_arbeitnow())
    
    print(f"Total de vagas brutas encontradas: {len(all_jobs)}")
    
    # Organizar por stack
    categorized_jobs = {stack: [] for stack in STACKS}
    
    for job in all_jobs:
        text_corp = f"{job['title']} {job['description']}".lower()
        
        for stack in STACKS:
            # Verifica se já temos 4 vagas para esta stack
            if len(categorized_jobs[stack]) >= 4:
                continue
            
            # Normalização simples para busca
            stack_search = stack.lower()
            if stack_search in text_corp:
                # Extrai nivel/mencao de ingles
                eng_req = extract_english_requirement(job['description'])
                
                # Evita duplicados na mesma stack
                if not any(j['url'] == job['url'] for j in categorized_jobs[stack]):
                    categorized_jobs[stack].append({
                        "title": job['title'],
                        "company": job['company'],
                        "url": job['url'],
                        "source": job['source'],
                        "english": eng_req,
                        "location": job['location']
                    })

    # Gerar Relatório em Markdown
    today_str = datetime.now().strftime("%d/%m/%Y")
    md_content = f"# 🚀 Vagas Remotas LATAM - {today_str}\n\n"
    md_content += "_Lista diária de vagas remotas para alunos com nível de inglês A1 a C2_\n\n"
    
    total_found = 0
    for stack, jobs in categorized_jobs.items():
        if not jobs:
            continue
        
        total_found += len(jobs)
        md_content += f"## 📌 Stack: {stack}\n\n"
        for idx, job in enumerate(jobs, 1):
            md_content += f"### {idx}. {job['title']} @ {job['company']}\n"
            md_content += f"- **Plataforma:** {job['source']}\n"
            md_content += f"- **Localização:** {job['location']}\n"
            md_content += f"- **Requisito de Inglês (Trecho):** {job['english']}\n"
            md_content += f"- **Link de Candidatura:** [Aplicar para Vaga]({job['url']})\n\n"
        md_content += "---\n\n"

    if total_found == 0:
        md_content += "Nenhuma vaga correspondente encontrada nas fontes públicas hoje.\n"

    with open("VAGAS_DO_DIA.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Relatório gerado com sucesso! Total de vagas categorizadas: {total_found}")

if __name__ == "__main__":
    main()
