#!/usr/bin/env python
"""
Gera:
  - research_metrics.json  -> visão agregada da pesquisa (por squad)
  - research_data_glmm.csv -> base tabular (uma linha por issue/aluno/página)

Entrada esperada (no diretório raiz do repo):
  - metrics-squad-*.json       (métricas de HTML por squad)
  - css-report-squad-*.json    (métricas de CSS por squad, opcional)

Extra:
  - Busca issues via GitHub API para preencher:
      student_id, sprint, semana, copilot_usage

Uso:
    python scripts/analyze_metrics.py

Dependências:
    pip install pandas requests
"""

import csv
import glob
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import requests

# Caminhos básicos
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GLMM_CSV_PATH = os.path.join(ROOT_DIR, "research_data_glmm.csv")
RESEARCH_JSON_PATH = os.path.join(ROOT_DIR, "research_metrics.json")

# Ajuste aqui se o repositório tiver outro owner/name
REPO_OWNER = "CInUFPE-2025-IA-EDU"
REPO_NAME = "FICR-IAEDU1A"

# Token deve vir do ambiente (em GitHub Actions, como secret GITHUB_TOKEN)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


# ---------- UTILIDADES BÁSICAS ----------

def load_json_safe(path: str) -> Any:
    """Carrega JSON ou retorna None se arquivo não existir/estiver vazio/for inválido."""
    if not os.path.exists(path):
        return None
    if os.path.getsize(path) == 0:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def discover_css_fields(css_data: Dict[str, Any]) -> Set[str]:
    """
    Dado o JSON de CSS, descobre as chaves de métricas em nível de página,
    para criar colunas dinâmicas no CSV (ex: file_size_css, css_rules, etc.).
    """
    fields: Set[str] = set()
    if not css_data:
        return fields

    # Duas estruturas possíveis:
    # 1) {"pages": {"home": {...}, ...}}
    # 2) {"home": {...}, ...}
    pages = css_data.get("pages", css_data)
    if not isinstance(pages, dict):
        return fields

    for _, metrics in pages.items():
        if isinstance(metrics, dict):
            fields.update(metrics.keys())

    return fields


# ---------- GITHUB ISSUES ----------

def fetch_all_issues() -> List[Dict[str, Any]]:
    """
    Busca todas as issues (abertas e fechadas) do repositório via GitHub API.
    Usa paginação até esgotar.
    """
    if not GITHUB_TOKEN:
        print("[WARN] GITHUB_TOKEN não definido. "
              "As colunas student_id, sprint, semana, copilot_usage ficarão vazias.")
        return []

    issues: List[Dict[str, Any]] = []
    page = 1
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    while True:
        url = (
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
            f"?state=all&per_page=100&page={page}"
        )
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"[WARN] Falha ao buscar issues: {resp.status_code} {resp.text}")
            break

        batch = resp.json()
        if not batch:
            break

        # Filtra PRs (que vêm no mesmo endpoint)
        only_issues = [item for item in batch if "pull_request" not in item]
        issues.extend(only_issues)
        page += 1

    print(f"[INFO] {len(issues)} issues carregadas da API do GitHub.")
    return issues


def parse_issue_metadata(issue: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extrai de uma issue:
      - squad (label: squad-A, squad-B, ...)
      - page (label: home, sobre, contato, projetos, etc.)
      - sprint (label: sprint-1, sprint-2, ...)
      - semana (label: SEM1, SEM2, SEM3, SEM4)
      - copilot_usage (label: SEM_IA ou COM_IA)
      - student_id (label tipo A01, A25, etc.)

    Retorna None se não achar squad OU page.
    """
    labels = [lbl["name"] for lbl in issue.get("labels", [])]

    # Squad
    squad_label = next((l for l in labels if l.startswith("squad-")), None)

    # Página
    PAGE_LABELS = {
        "home",
        "sobre",
        "contato",
        "projetos",
        "habilidades",
        "servicos",
        "depoimentos",
        "case-de-sucesso",
    }
    page_label = next((l for l in labels if l in PAGE_LABELS), None)

    if not squad_label or not page_label:
        return None

    # Semana = somente SEM1, SEM2, SEM3, SEM4 (evita confusão com SEM_IA)
    semana_label = next(
        (l for l in labels if re.fullmatch(r"SEM[1-4]", l.upper())),
        "",
    )

    # Sprint
    sprint_label = next((l for l in labels if l.startswith("sprint-")), "")

    # Copilot usage
    if "COM_IA" in labels:
        copilot_usage = "COM_IA"
    elif "SEM_IA" in labels:
        copilot_usage = "SEM_IA"
    else:
        copilot_usage = ""

    # Student ID ex. A25, A01 etc.
    student_id_label = next(
        (l for l in labels if re.fullmatch(r"[A-Z]\d{2}", l)),
        "",
    )

    return {
        "squad": squad_label,
        "page": page_label,
        "sprint": sprint_label,
        "semana": semana_label,
        "copilot_usage": copilot_usage,
        "student_id": student_id_label,
    }


# ---------- RESEARCH METRICS JSON ----------

def build_research_metrics_struct(
    squads_pages_metrics: Dict[str, Dict[str, Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Monta o dicionário base do research_metrics.json, usando
    métricas reais de HTML (html_errors por squad, etc.).
    """
    data: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "research_metrics": {},
        "squads": {},
    }

    data["research_metrics"] = {
        "total_students": 36,  # fixa por enquanto
        "total_squads": len(squads_pages_metrics.keys()),
        "experiment_duration_weeks": 4,
        "technologies": ["HTML5", "CSS3"],
        "variables": {
            "independent": "GitHub Copilot usage",
            "dependent": ["code_quality", "productivity", "engagement"],
        },
    }

    for squad_name, pages_dict in squads_pages_metrics.items():
        total_html_errors = sum(
            p.get("html_errors", 0) for p in pages_dict.values()
        )
        data["squads"][squad_name] = {
            "members": {
                "html": [],
                "css": [],
            },
            "pages": pages_dict,  # já vem com metrics por página
            "metrics": {
                "html_validation_errors": total_html_errors,
                "commits_count": 0,      # pode ser preenchido depois
                "completion_rate": 0,    # idem
            },
            "experiment_group": "TODO",  # COM_IA / SEM_IA, vindo das labels depois
        }

    return data


# ---------- MAIN ----------

def main() -> None:
    # 1) Localizar todos os arquivos metrics-squad-*.json (HTML)
    metrics_files = sorted(
        glob.glob(os.path.join(ROOT_DIR, "metrics-squad-*.json"))
    )

    if not metrics_files:
        print("[analyze_metrics] Nenhum metrics-squad-*.json encontrado. "
              "Gerando arquivos vazios.")
        with open(GLMM_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "squad",
                    "page",
                    "html_errors",
                    "html_warnings",
                    "file_size_html",
                    "student_id",
                    "sprint",
                    "semana",
                    "copilot_usage",
                ]
            )
        minimal = {
            "timestamp": datetime.now().isoformat(),
            "research_metrics": {},
            "squads": {},
        }
        with open(RESEARCH_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(minimal, f, indent=2, ensure_ascii=False)
        return

    # 2) Descobrir campos de CSS globais (para criar colunas dinâmicas)
    css_fields_global: Set[str] = set()

    for metrics_path in metrics_files:
        base = os.path.basename(metrics_path)
        # metrics-squad-A.json -> squad-A -> A
        try:
            squad_name = os.path.splitext(base)[0].replace("metrics-", "")
            squad_letter = squad_name.split("-")[-1]
        except Exception:
            squad_letter = "UNKNOWN"

        css_report_path = os.path.join(
            ROOT_DIR, f"css-report-squad-{squad_letter}.json"
        )
        css_data = load_json_safe(css_report_path)
        if css_data:
            css_fields_global |= discover_css_fields(css_data)

    css_fields_sorted: List[str] = sorted(css_fields_global)

    # 3) Montar dicionário {squad: {page: {...metrics...}}} com HTML+CSS
    squads_pages_metrics: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for metrics_path in metrics_files:
        with open(metrics_path, "r", encoding="utf-8") as f:
            html_data = json.load(f)

        squad_name = html_data.get("squad", "squad-UNKNOWN")
        pages_html = html_data.get("pages", {})

        if squad_name not in squads_pages_metrics:
            squads_pages_metrics[squad_name] = {}

        # Achar CSS correspondente
        base = os.path.basename(metrics_path)
        try:
            squad_name_from_file = os.path.splitext(base)[0].replace("metrics-", "")
            squad_letter = squad_name_from_file.split("-")[-1]
        except Exception:
            squad_letter = "UNKNOWN"

        css_report_path = os.path.join(
            ROOT_DIR, f"css-report-squad-{squad_letter}.json"
        )
        css_data = load_json_safe(css_report_path)

        css_pages: Dict[str, Dict[str, Any]] = {}
        if css_data:
            css_pages_raw = css_data.get("pages", css_data)
            if isinstance(css_pages_raw, dict):
                css_pages = {
                    page_name: metrics
                    for page_name, metrics in css_pages_raw.items()
                    if isinstance(metrics, dict)
                }

        for page_name, page_metrics in pages_html.items():
            html_errors = page_metrics.get("html_errors", 0)
            html_warnings = page_metrics.get("html_warnings", 0)
            file_size_html = page_metrics.get("file_size_html", 0)

            merged_metrics = {
                "html_errors": html_errors,
                "html_warnings": html_warnings,
                "file_size_html": file_size_html,
            }

            css_for_page = css_pages.get(page_name, {})
            if isinstance(css_for_page, dict):
                for key in css_fields_sorted:
                    merged_metrics[key] = css_for_page.get(key, "")

            squads_pages_metrics[squad_name][page_name] = merged_metrics

    # 4) Gerar research_metrics.json com os dados agregados
    research_data = build_research_metrics_struct(squads_pages_metrics)
    with open(RESEARCH_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(research_data, f, indent=2, ensure_ascii=False)

    # 5) Buscar issues e montar linhas da base GLMM
    issues = fetch_all_issues()
    rows_for_csv: List[Dict[str, Any]] = []

    if issues:
        for issue in issues:
            meta = parse_issue_metadata(issue)
            if not meta:
                continue

            squad = meta["squad"]       # ex: squad-A
            page = meta["page"]         # ex: home

            metrics_for_page = squads_pages_metrics.get(squad, {}).get(page, {})

            row: Dict[str, Any] = {
                "squad": squad,
                "page": page,
                "html_errors": metrics_for_page.get("html_errors", 0),
                "html_warnings": metrics_for_page.get("html_warnings", 0),
                "file_size_html": metrics_for_page.get("file_size_html", 0),
                "student_id": meta["student_id"],
                "sprint": meta["sprint"],
                "semana": meta["semana"],
                "copilot_usage": meta["copilot_usage"],
            }

            # Campos dinâmicos de CSS
            for key in css_fields_sorted:
                row[key] = metrics_for_page.get(key, "")

            rows_for_csv.append(row)
    else:
        # Fallback: sem issues ou sem token -> uma linha por página,
        # com campos de aluno/semana/copilot vazios.
        for squad, pages in squads_pages_metrics.items():
            for page_name, metrics_for_page in pages.items():
                row = {
                    "squad": squad,
                    "page": page_name,
                    "html_errors": metrics_for_page.get("html_errors", 0),
                    "html_warnings": metrics_for_page.get("html_warnings", 0),
                    "file_size_html": metrics_for_page.get("file_size_html", 0),
                    "student_id": "",
                    "sprint": "",
                    "semana": "",
                    "copilot_usage": "",
                }
                for key in css_fields_sorted:
                    row[key] = metrics_for_page.get(key, "")
                rows_for_csv.append(row)

    # 6) Escrever research_data_glmm.csv
    base_fields = [
        "squad",
        "page",
        "html_errors",
        "html_warnings",
        "file_size_html",
        "student_id",
        "sprint",
        "semana",
        "copilot_usage",
    ]
    css_fields = css_fields_sorted
    fieldnames = base_fields + css_fields

    df = pd.DataFrame(rows_for_csv, columns=fieldnames)
    df.to_csv(GLMM_CSV_PATH, index=False, encoding="utf-8")

    print(
        f"[analyze_metrics] Gerado {GLMM_CSV_PATH} com {len(df)} linhas "
        f"e {len(fieldnames)} colunas."
    )
    print(
        f"[analyze_metrics] Gerado {RESEARCH_JSON_PATH} com "
        f"{len(squads_pages_metrics.keys())} squads."
    )


if __name__ == "__main__":
    main()

