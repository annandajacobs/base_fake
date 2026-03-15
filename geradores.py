from datetime import datetime, timedelta
import pandas as pd
from config import *
from utils import _upgrade_risco, _n_por_perc, gerar_dias_letivos, limpar_nome

def gerar_cursos():
    lista = [
        "Desenvolvimento de Sistemas",
        "Edificações",
        "Eletrônica",
        "Eletrotécnica",
        "Estradas",
        "Mecânica",
        "Química",
    ]
    return [{"id_curso": i, "nome_curso": n} for i, n in enumerate(lista, 1)]


def gerar_disciplinas():
    lista = [
        "Português", "Matemática", "História", "Geografia", "Artes",
        "Educação Física", "Química", "Física", "Biologia",
        "Filosofia", "Sociologia", "Inglês", "Espanhol",
    ]
    return [{"id_disciplina": i, "nome": n} for i, n in enumerate(lista, 1)]


def gerar_estudantes(cursos, cidade_bairros):
    """
    Gera estudantes com situação e perfil_risco definidos por cotas.
    Alunos fora de Maceió têm chance de ter perfil_risco elevado em um nível,
    simulando o impacto da distância como fator de risco de evasão.

    Campos internos (não salvos no CSV de estudantes):
        perfil_risco : "BAIXO" | "MEDIO" | "ALTO"  — só para ATIVO
    """

    cidades = list(cidade_bairros.keys())

    n_baixo = _n_por_perc(TOTAL_ESTUDANTES, PERC_RISCO_BAIXO)
    n_medio = _n_por_perc(TOTAL_ESTUDANTES, PERC_RISCO_MEDIO)
    n_alto  = TOTAL_ESTUDANTES - n_baixo - n_medio

    perfis = (
        ["BAIXO"] * n_baixo
        + ["MEDIO"] * n_medio
        + ["ALTO"]  * n_alto
    )
    random.shuffle(perfis)

    estudantes = []
    for i, perfil_risco in enumerate(perfis, start=1):

        cidade = random.choices(
            cidades,
            weights=[70 if c == "Maceió" else 1 for c in cidades],
            k=1,
        )[0]
        bairro = random.choice(cidade_bairros[cidade])

        if cidade != "Maceió" and random.random() < PROB_UPGRADE_RISCO_FORA_MACEIO:
            perfil_risco = _upgrade_risco(perfil_risco)

        estudantes.append({
            "id_estudante" : i,
            "matricula"    : fake.unique.random_number(digits=10),
            "nome"         : limpar_nome(fake.name()),
            "id_curso"     : random.choice(cursos)["id_curso"],
            "ano_ingresso" : random.randint(2022, ANO_LETIVO),
            "situacao"     : "ATIVO",
            "perfil_risco" : perfil_risco,
            "bairro"       : bairro,
            "cidade"       : cidade,
        })

    return estudantes

def gerar_matriculas(estudantes, disciplinas):
    matriculas = []
    id_md = 1

    for est in estudantes:

        disciplinas_escolhidas = random.sample(disciplinas, DISCIPLINAS_POR_ALUNO)

        for disc in disciplinas_escolhidas:
            matriculas.append({
                "id_matricula_disciplina": id_md,
                "id_estudante"           : est["id_estudante"],
                "id_disciplina"          : disc["id_disciplina"],
                "ano_letivo"             : ANO_LETIVO,
            })
            id_md += 1

    return matriculas

def gerar_presenca_campus(estudantes):
    """
    Gera um registro por estudante por dia letivo indicando se ele
    esteve presente no campus (PRESENTE | AUSENTE).

    Regras:
      - Demais perfis: probabilidade de presença baseada no perfil_risco/situação.
      - Este registro é a fonte de verdade: se AUSENTE no campus,
        o aluno NUNCA poderá estar PRESENTE em sala naquele dia.

        DESCONSIDERAR FINS DE SEMANA NA GERAÇÃO DE PRESENÇA NO CAMPUS !!!
    """

    perfil_por_est  = {e["id_estudante"]: e["perfil_risco"] for e in estudantes}

    dias_letivos = gerar_dias_letivos()

    registros    = []
    id_registro  = 1

    for est in estudantes:
        id_est   = est["id_estudante"]
        perfil   = perfil_por_est[id_est]

        if perfil == "ALTO":
            prob = PROB_CAMPUS_RISCO_ALTO
        elif perfil == "MEDIO":
            prob = PROB_CAMPUS_RISCO_MEDIO
        else:
            prob = PROB_CAMPUS_RISCO_BAIXO

        for data in dias_letivos:
            presente_campus = random.random() < prob
            registros.append({
                "id_registro_campus" : id_registro,
                "id_estudante"       : id_est,
                "data"               : data,
                "situacao"           : "PRESENTE" if presente_campus else "AUSENTE",
            })
            id_registro += 1

    print(
        f"[PRESENÇA NO CAMPUS GERADA]\n"
        f"  Total de registros : {len(registros):>8}\n"
    )

    return registros

def gerar_frequencia(matriculas, estudantes, presenca_campus):
    """
    Gera registros de presença/falta por aula e frequencia.

    Regra de consistência:
      - Se o aluno estava AUSENTE no campus naquele dia → FALTA obrigatória
        em todas as suas disciplinas naquele dia.
      - Se estava PRESENTE no campus → presença/falta definida pelo perfil_risco
        (o aluno pode ter chegado ao campus mas faltado a alguma aula).

        DESCONSIDERAR FINS DE SEMANA NA GERAÇÃO DE PRESENÇA NO CAMPUS !!!
    """
    perfil_por_est = {e["id_estudante"]: e["perfil_risco"] for e in estudantes}
    est_por_mat    = {
        m["id_matricula_disciplina"]: m["id_estudante"] for m in matriculas
    }

    campus_idx: dict[tuple, bool] = {}
    for r in presenca_campus:
        campus_idx[(r["id_estudante"], r["data"])] = (r["situacao"] == "PRESENTE")

    dias_letivos = gerar_dias_letivos()

    registros   = []
    id_registro = 1

    for matricula in matriculas:
        id_est = est_por_mat[matricula["id_matricula_disciplina"]]
        perfil = perfil_por_est.get(id_est)

        if perfil == "ALTO":
            lo, hi = FALTAS_RISCO_ALTO
        elif perfil == "MEDIO":
            lo, hi = FALTAS_RISCO_MEDIO
        else:
            lo, hi = FALTAS_RISCO_BAIXO

        faltas_alvo   = random.randint(lo, min(hi, TOTAL_AULAS))
        intencao_aula = ["FALTA"] * faltas_alvo + ["PRESENTE"] * (TOTAL_AULAS - faltas_alvo)
        random.shuffle(intencao_aula)

        for idx_aula, data in enumerate(dias_letivos):
            no_campus     = campus_idx.get((id_est, data), False)
            situacao_aula = intencao_aula[idx_aula] if no_campus else "FALTA"

            registros.append({
                "id_registro"             : id_registro,
                "id_matricula_disciplina" : matricula["id_matricula_disciplina"],
                "data_aula"               : data,
                "situacao"                : situacao_aula,
            })
            id_registro += 1

    print(f"[FREQUÊNCIA GERADA]\n  Total de registros : {len(registros):>8}\n")

    return registros

def gerar_tabela_risco(estudantes, matriculas, frequencia):
    """
    Consolida uma tabela por estudante pronta para ML.
      - features: freq_media, total_reprovacoes, total_disciplinas, cidade
      - label   : risco_evasao (ALTO | MEDIO | BAIXO)

    O perfil_risco interno (que inclui o efeito da distância) é usado para
    derivar o label, mas não é exposto como feature direta.
    """

    df_est  = pd.DataFrame(estudantes)
    df_mat  = pd.DataFrame(matriculas)
    df_freq = pd.DataFrame(frequencia)

    # Agrega frequência por matrícula
    df_resumo = df_freq.groupby("id_matricula_disciplina").agg(
        frequencia     = ("situacao", lambda x: (x == "PRESENTE").sum() / TOTAL_AULAS),
        situacao_final = ("situacao", lambda x:
            "REPROVADO" if (x == "PRESENTE").sum() / TOTAL_AULAS < 0.75 else "APROVADO"
        ),
    ).reset_index()

    df_merged = df_mat.merge(df_resumo, on="id_matricula_disciplina")
    agg = df_merged.groupby("id_estudante").agg(
        freq_media        = ("frequencia",    "mean"),
        total_reprovacoes = ("situacao_final", lambda x: (x == "REPROVADO").sum()),
        total_disciplinas = ("id_disciplina",  "count"),
    ).reset_index()

    df_final = df_est.merge(agg, on="id_estudante", how="left")
    df_final["risco_evasao"] = df_final["perfil_risco"]

    df_final["freq_media"]        = df_final["freq_media"].fillna(0).round(2)
    df_final["total_reprovacoes"] = df_final["total_reprovacoes"].fillna(0).astype(int)
    df_final["total_disciplinas"] = df_final["total_disciplinas"].fillna(0).astype(int)

    cols = [
        "id_estudante", "matricula", "nome", "id_curso",
        "ano_ingresso", "bairro", "cidade",
        "freq_media", "total_reprovacoes", "total_disciplinas",
        "risco_evasao",
    ]

    df_saida = df_final[cols]

    dist = df_saida["risco_evasao"].value_counts()
    print(
        f"[TABELA DE RISCO — totalizações]\n"
        f"{dist.to_string()}\n"
        f"  → Taxa de ALTO risco : {dist.get('ALTO', 0)/len(df_saida):.1%}\n"
    )

    return df_saida