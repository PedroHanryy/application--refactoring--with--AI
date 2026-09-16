import requests
import os

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = 'CinUFPE-2025-IA-EDU'
REPO_NAME = 'FICR-IAEDU1A'

# Labels para sua pesquisa
LABELS = [
    # Squads
    {"name": "squad-A", "color": "1D76DB", "description": "Squad A"},
    {"name": "squad-B", "color": "1D76DB", "description": "Squad B"},
    {"name": "squad-C", "color": "1D76DB", "description": "Squad C"},
    {"name": "squad-D", "color": "1D76DB", "description": "Squad D"},
    {"name": "squad-E", "color": "1D76DB", "description": "Squad E"},
    {"name": "squad-F", "color": "1D76DB", "description": "Squad F"},
    {"name": "squad-G", "color": "1D76DB", "description": "Squad G"},
    {"name": "squad-H", "color": "1D76DB", "description": "Squad H"},
    {"name": "squad-I", "color": "1D76DB", "description": "Squad I"},
    
    # Tipos de Task
    {"name": "HTML", "color": "FF6B6B", "description": "Tarefa de HTML"},
    {"name": "CSS", "color": "4ECDC4", "description": "Tarefa de CSS"},
    
    # Sprints
    {"name": "sprint-1", "color": "FFE66D", "description": "Sprint 1 - Home e Sobre"},
    {"name": "sprint-2", "color": "FF9E64", "description": "Sprint 2 - Contato e Projetos"},
    {"name": "sprint-3", "color": "A78BFA", "description": "Sprint 3 - Habilidades e Serviços"},
    {"name": "sprint-4", "color": "F472B6", "description": "Sprint 4 - Depoimentos e Case"},
    
    # Páginas
    {"name": "home", "color": "BFDBFE", "description": "Página Home"},
    {"name": "sobre", "color": "BFDBFE", "description": "Página Sobre"},
    {"name": "contato", "color": "BFDBFE", "description": "Página Contato"},
    {"name": "projetos", "color": "BFDBFE", "description": "Página Projetos"},
    {"name": "habilidades", "color": "BFDBFE", "description": "Página Habilidades"},
    {"name": "servicos", "color": "BFDBFE", "description": "Página Serviços"},
    {"name": "depoimentos", "color": "BFDBFE", "description": "Página Depoimentos"},
    {"name": "case-de-sucesso", "color": "BFDBFE", "description": "Página Case de Sucesso"},
    
    # Pesquisa
    {"name": "pesquisa", "color": "10B981", "description": "Issue relacionada à pesquisa"},
    {"name": "metrica", "color": "8B5CF6", "description": "Coleta de métricas"},
    {"name": "copilot-experiment", "color": "F59E0B", "description": "Grupo com Copilot"},
    {"name": "control-group", "color": "EF4444", "description": "Grupo de controle"}
]

def create_label(label_data):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/labels'
    response = requests.post(url, json=label_data, headers=headers)
    
    if response.status_code == 201:
        print(f"✅ Label criada: {label_data['name']}")
    else:
        print(f"⚠️  Label {label_data['name']}: {response.status_code}")

def main():
    for label in LABELS:
        create_label(label)
    print("🎉 Todas as labels foram criadas!")

if __name__ == '__main__':
    main()
