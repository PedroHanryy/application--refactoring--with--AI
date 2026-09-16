#!/usr/bin/env python
import os
import json
import subprocess
import sys
from datetime import datetime


def run_html_validate(html_path: str) -> dict:
    """
    Executa html-validate e retorna contagem de erros/avisos.

    Usa a opção correta: --formatter json
    e considera a saída JSON mesmo quando o processo retorna código != 0.
    """
    metrics = {
        "html_errors": 0,
        "html_warnings": 0,
    }

    cmd = f"html-validate --formatter json {html_path}"
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
        )

        output = (result.stdout or "").strip()

        # Se não houve saída, loga o erro e retorna métrica zerada
        if not output:
            if result.stderr:
                print(f"[WARN] Erro ao validar {html_path}: {result.stderr}")
            return metrics

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            print(f"[WARN] Saída não JSON ao validar {html_path}")
            return metrics

        # html-validate com formatter json normalmente retorna:
        # { "results": [ { "messages": [ ... ] } ] }
        messages = []

        if isinstance(data, list):
            # fallback, caso a CLI retorne lista diretamente
            messages = data
        elif isinstance(data, dict):
            results = data.get("results", [])
            if isinstance(results, list):
                for res in results:
                    msgs = res.get("messages", [])
                    if isinstance(msgs, list):
                        messages.extend(msgs)

        for msg in messages:
            sev = msg.get("severity")
            # versões antigas podem usar número, novas usam string
            if sev == 2 or sev == "error":
                metrics["html_errors"] += 1
            elif sev == 1 or sev == "warning":
                metrics["html_warnings"] += 1

    except Exception as e:
        print(f"[EXCEPTION] Falha ao rodar html-validate em {html_path}: {e}")

    return metrics


def analyze_page(squad_path: str, html_file: str) -> dict:
    metrics = {
        "html_errors": 0,
        "html_warnings": 0,
        "file_size_html": 0,
    }

    html_path = os.path.join(squad_path, html_file)
    if os.path.exists(html_path):
        # tamanho do arquivo HTML
        metrics["file_size_html"] = os.path.getsize(html_path)

        # validação sintática com html-validate
        hv_metrics = run_html_validate(html_path)
        metrics.update(hv_metrics)

    return metrics


def analyze_squad(squad_path: str) -> dict:
    data = {
        "squad": os.path.basename(squad_path),
        "timestamp": datetime.now().isoformat(),
        "pages": {},
    }

    if not os.path.isdir(squad_path):
        print(f"[WARN] Pasta não encontrada: {squad_path}")
        return data

    for f in os.listdir(squad_path):
        if f.endswith(".html"):
            page_name = f.replace(".html", "")
            data["pages"][page_name] = analyze_page(squad_path, f)

    return data


def main():
    if len(sys.argv) != 2:
        print("Uso: python scripts/analyze_squad.py squads/squad-X")
        sys.exit(1)

    squad_path = sys.argv[1]
    metrics = analyze_squad(squad_path)

    squad_name = os.path.basename(squad_path)
    out_file = f"metrics-{squad_name}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(f"📊 Métricas salvas em {out_file}")


if __name__ == "__main__":
    main()
