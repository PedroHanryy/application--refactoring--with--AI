import pandas as pd
import requests
import os
import time

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = 'CinUFPE-2025-IA-EDU'
REPO_NAME = 'FICR-IAEDU1A'

SPRINT_PLANNING = {
    "Home": 1, "Sobre": 1,
    "Contato": 2, "Projetos": 2,
    "Habilidades": 3, "Serviços": 3,
    "Depoimentos": 4, "Case de Sucesso": 4,
}

PAGE_SLUG = {
    "Home": "home",
    "Sobre": "sobre",
    "Contato": "contato",
    "Projetos": "projetos",
    "Habilidades": "habilidades",
    "Serviços": "servicos",
    "Depoimentos": "depoimentos",
    "Case de Sucesso": "case-de-sucesso",
}


def create_github_issue(row):
    page = row["Página"]
    sprint = SPRINT_PLANNING.get(page, 1)
    slug = PAGE_SLUG.get(page, page.lower().replace(" ", "-"))

    body = (
        "## 🎯 Detalhes da Task\n"
        f"- Squad: {row['Squad']}\n"
        f"- Página: {page}\n"
        f"- Tipo: {row['Tipo']}\n"
        f"- Responsável: {row['Assignee']}\n"
        f"- Sprint: {sprint}\n\n"
        "## 📝 Descrição\n"
        f"{row['Descrição']}\n\n"
        "## ✅ Critérios de Aceitação\n"
        "- [ ] Código validado (html-validate)\n"
        "- [ ] Layout responsivo mobile/desktop\n"
        "- [ ] Semântica HTML5 adequada\n"
        "- [ ] Commits realizados na pasta do squad\n"
        "- [ ] Página funcional no navegador\n\n"
        "## 🛠️ Requisitos Técnicos\n"
        "- HTML5 semântico\n"
        "- CSS responsivo (Flexbox/Grid)\n"
        "- Imagens com alt text\n"
        "- Código limpo e organizado\n\n"
        "## 📁 Estrutura de Arquivos esperada\n"
        f"- squads/squad-{row['Squad']}/{slug}.html\n"
        f"- squads/squad-{row['Squad']}/styles/{slug}.css\n\n"
        f"**Prazo:** Semana {sprint}\n"
    )

    labels = [
        row["Squad"],
        row["Tipo"],
        f"sprint-{sprint}",
        page,
        "programação",
        "html-css",
    ]

    data = {
        "title": row["Título"],
        "body": body,
        "assignees": [row["Assignee"]],
        "labels": labels,
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    response = requests.post(url, json=data, headers=headers)
    return response


def main():
    if not GITHUB_TOKEN:
        raise SystemExit("GITHUB_TOKEN não definido. Use export GITHUB_TOKEN=...")

    excel_file = "assignments.xlsx"
    if not os.path.exists(excel_file):
        raise SystemExit(f"Arquivo {excel_file} não encontrado na raiz do projeto.")

    df = pd.read_excel(excel_file)
    print(f"🎯 Lendo {len(df)} linhas de assignments em {excel_file}")

    ok = 0
    fail = 0

    for idx, row in df.iterrows():
        print(f"➡️ ({idx+1}/{len(df)}) Criando issue: {row['Título']}")
        resp = create_github_issue(row)
        if resp.status_code == 201:
            issue = resp.json()
            print(f"   ✅ Criada: #{issue['number']} - {issue['title']}")
            ok += 1
        else:
            print(f"   ❌ Erro: {resp.status_code} - {resp.text}")
            fail += 1
        time.sleep(1.2)

    print("\n📊 RESULTADO FINAL")
    print(f"   ✅ Sucesso: {ok}")
    print(f"   ❌ Falha:   {fail}")


if __name__ == "__main__":
    main()
