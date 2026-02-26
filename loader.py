"""
loader.py — Lê o mock_sigaa_ifal.json e entrega um DataFrame pronto
====================================================================
Use em app.py:
    from loader import carregar_dados
    df, df_turmas = carregar_dados()
"""

import json
import pandas as pd
from pathlib import Path


def carregar_dados(caminho_json: str = "mock_sigaa_ifal.json"):
    """
    Lê o JSON mock da API SIGAA e retorna dois DataFrames:

    df_alunos  → 1 linha por aluno, com resumo consolidado
    df_turmas  → 1 linha por aluno × disciplina (detalhe por componente)
    """
    path = Path(caminho_json)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path.resolve()}")

    with open(path, encoding="utf-8") as f:
        payload = json.load(f)

    # ─── Filtra somente TECNICO_INTEGRADO ─────────────────────────────────
    discentes = [
        d for d in payload["discentes"]
        if d["nivel_ensino"] == "TECNICO_INTEGRADO"
    ]

    # ─── DataFrame de alunos (resumo) ─────────────────────────────────────
    linhas_alunos = []
    for d in discentes:
        r = d["resumo"]
        linhas_alunos.append({
            "id_discente":             d["id_discente"],
            "matricula":               d["matricula"],
            "nome":                    d["nome"],
            "nivel_ensino":            d["nivel_ensino"],
            "curso":                   d["curso"],
            "campus":                  d["campus"],
            "ano_letivo":              d["ano_letivo"],
            "turno":                   d["turno"],
            "situacao":                d["situacao"],
            "periodo_letivo":          d["periodo_letivo"],
            "frequencia_media_%":      r["frequencia_media_geral"],
            "nota_media":              r["nota_media_geral"],
            "total_disciplinas":       r["total_disciplinas"],
            "disc_abaixo_75pct":       r["disciplinas_abaixo_75pct"],
            "disc_reprovadas":         r["disciplinas_reprovadas"],
            "disciplina_critica":      r["disciplina_critica"]["nome"],
            "nota_disciplina_critica": r["disciplina_critica"]["nota"],
            "freq_disciplina_critica": r["disciplina_critica"]["frequencia"],
        })

    df_alunos = pd.DataFrame(linhas_alunos)

    # ── Score de risco (baseline explicável — substituir por Regressão Logística)
    df_alunos["score_risco"] = (
        (100 - df_alunos["frequencia_media_%"]) * 0.50
        + (10  - df_alunos["nota_media"])        * 0.30
        + df_alunos["disc_reprovadas"]           * 3.00
        + df_alunos["disc_abaixo_75pct"]         * 2.00
    ).clip(0, 100).round(1)

    def nivel(score):
        if score >= 60: return "🔴 Alto"
        if score >= 35: return "🟡 Médio"
        return "🟢 Baixo"

    df_alunos["nivel_risco"] = df_alunos["score_risco"].apply(nivel)

    # ─── DataFrame de turmas (detalhe por disciplina) ──────────────────────
    linhas_turmas = []
    for d in discentes:
        for t in d["turmas"]:
            linhas_turmas.append({
                "id_discente":         d["id_discente"],
                "matricula":           d["matricula"],
                "nome_aluno":          d["nome"],
                "curso":               d["curso"],
                "ano_letivo":          d["ano_letivo"],
                "id_turma":            t["id_turma"],
                "codigo_componente":   t["codigo_componente"],
                "nome_componente":     t["nome_componente"],
                "carga_horaria":       t["carga_horaria_total"],
                "total_aulas":         t["frequencia"]["total_aulas"],
                "total_faltas":        t["frequencia"]["total_faltas"],
                "total_presencas":     t["frequencia"]["total_presencas"],
                "frequencia_%":        t["frequencia"]["percentual_frequencia"],
                "nota_unidade_1":      t["notas"]["unidade_1"],
                "nota_unidade_2":      t["notas"]["unidade_2"],
                "nota_unidade_3":      t["notas"]["unidade_3"],
                "media_final":         t["notas"]["media_final"],
                "situacao_componente": t["notas"]["situacao"],
                "alerta_frequencia":   t["frequencia"]["percentual_frequencia"] < 75,
            })

    df_turmas = pd.DataFrame(linhas_turmas)

    return df_alunos, df_turmas


# ─── Teste rápido quando executado diretamente ────────────────────────────────
if __name__ == "__main__":
    df_a, df_t = carregar_dados()

    print("=" * 55)
    print(f"  ALUNOS     : {len(df_a)} registros")
    print(f"  TURMAS     : {len(df_t)} registros")
    print(f"  Risco Alto : {(df_a['nivel_risco'] == '🔴 Alto').sum()} alunos")
    print(f"  Risco Médio: {(df_a['nivel_risco'] == '🟡 Médio').sum()} alunos")
    print(f"  Risco Baixo: {(df_a['nivel_risco'] == '🟢 Baixo').sum()} alunos")
    print("=" * 55)
    print()
    print("── Alunos (primeiros 5) ──")
    print(df_a[["nome", "curso", "frequencia_media_%",
                "nota_media", "disc_reprovadas", "nivel_risco"]].head().to_string(index=False))
    print()
    print("── Turmas com frequência abaixo de 75% ──")
    alertas = df_t[df_t["alerta_frequencia"]][
        ["nome_aluno", "nome_componente", "frequencia_%", "media_final"]
    ].sort_values("frequencia_%")
    print(alertas.to_string(index=False))
