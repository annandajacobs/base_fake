import os
import sys
import random
import re
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta


fake = Faker("pt_BR")

TOTAL_ESTUDANTES = 5000
TOTAL_AULAS = 60
ANO_LETIVO = 2026

def configurar_seed(seed):
    random.seed(seed)
    Faker.seed(seed)


def limpar_nome(nome):
    padrao = r'^(sr|sra|srta|Dr|Dra)\.?\s+'
    nome_limpo = re.sub(padrao, '', nome, flags=re.IGNORECASE)
    return nome_limpo.strip()


# CURSOS
def gerar_cursos():

    lista_cursos = [
        "Desenvolvimento de Sistemas",
        "Edificações",
        "Eletrônica",
        "Eletrotécnica",
        "Estradas",
        "Mecânica",
        "Química"
    ]

    cursos = [
        {"id_curso": i, "nome_curso": nome}
        for i, nome in enumerate(lista_cursos, start=1)
    ]

    return cursos


# DISCIPLINAS
def gerar_disciplinas():

    lista_disciplinas = [
        "Português",
        "Matemática",
        "História",
        "Geografia",
        "Artes",
        "Educação Física",
        "Química",
        "Física",
        "Biologia",
        "Filosofia",
        "Sociologia",
        "Inglês",
        "Espanhol"
    ]

    disciplinas = [
        {"id_disciplina": i, "nome": nome}
        for i, nome in enumerate(lista_disciplinas, start=1)
    ]

    return disciplinas


# BAIRROS
def carregar_bairros():

    df = pd.read_excel("recursos/bairros.xlsx")

    cidade_bairros = (
        df.groupby("NM_DIST")["NM_BAIRRO"]
        .apply(list)
        .to_dict()
    )

    return cidade_bairros



# ESTUDANTES
def gerar_estudantes(cursos, cidade_bairros):

    cidades = list(cidade_bairros.keys())
    estudantes = []

    for i in range(1, TOTAL_ESTUDANTES + 1):

        cidade = random.choices(
            cidades,
            weights=[70 if c == "Maceió" else 1 for c in cidades],
            k=1
        )[0]

        bairro = random.choice(cidade_bairros[cidade])

        situacao = random.choices(
            ["ATIVO", "TRANCADO", "EVADIDO"],
            weights=[80, 10, 10],
            k=1
        )[0]

        estudantes.append({
            "id_estudante": i,
            "matricula": fake.unique.random_number(digits=10),
            "nome": limpar_nome(fake.name()),
            "id_curso": random.choice(cursos)["id_curso"],
            "ano_ingresso": random.randint(2022, ANO_LETIVO),
            "situacao": situacao,
            "bairro": bairro,
            "cidade": cidade,
        })

    return estudantes



# MATRÍCULAS
def gerar_matriculas(estudantes, disciplinas):

    matriculas = []
    id_md = 1

    for estudante in estudantes:

        if estudante["situacao"] != "ATIVO":
            continue

        disciplinas_escolhidas = random.sample(disciplinas, 3)

        for disc in disciplinas_escolhidas:

            matriculas.append({
                "id_matricula_disciplina": id_md,
                "id_estudante": estudante["id_estudante"],
                "id_disciplina": disc["id_disciplina"],
                "ano_letivo": ANO_LETIVO
            })

            id_md += 1

    return matriculas


# FREQUÊNCIA
def gerar_frequencia(matriculas):

    registros = []
    resumo_faltas = []

    data_inicio = datetime(ANO_LETIVO, 2, 1)

    id_registro = 1

    for matricula in matriculas:

        perfil = random.choices(
            ["ALTA", "MEDIA", "BAIXA"],
            weights=[60, 30, 10],
            k=1
        )[0]

        if perfil == "ALTA":
            faltas = random.randint(0, 5)
        elif perfil == "MEDIA":
            faltas = random.randint(6, 15)
        else:
            faltas = random.randint(16, 40)

        presencas = TOTAL_AULAS - faltas

        situacoes = ["FALTA"] * faltas + ["PRESENTE"] * presencas
        random.shuffle(situacoes)

        for aula in range(TOTAL_AULAS):

            data = data_inicio + timedelta(days=aula * 2)

            registros.append({
                "id_registro": id_registro,
                "id_matricula_disciplina": matricula["id_matricula_disciplina"],
                "data_aula": data,
                "situacao": situacoes[aula]
            })

            id_registro += 1

        frequencia = presencas / TOTAL_AULAS

        if frequencia < 0.75:
            situacao_final = "REPROVADO"
        else:
            situacao_final = random.choices(
                ["APROVADO", "REPROVADO"],
                weights=[90, 10],
                k=1
            )[0]

        resumo_faltas.append({
            "id_matricula_disciplina": matricula["id_matricula_disciplina"],
            "faltas_totais": faltas,
            "frequencia": round(frequencia, 2),
            "situacao_final": situacao_final
        })

    return registros, resumo_faltas


def salvar_dados(seed, cursos, disciplinas, estudantes, matriculas, frequencia, resumo):

    pasta = f"dados/seed_{seed}"
    os.makedirs(pasta, exist_ok=True)

    pd.DataFrame(cursos).to_csv(f"{pasta}/cursos.csv", index=False)
    pd.DataFrame(disciplinas).to_csv(f"{pasta}/disciplinas.csv", index=False)
    pd.DataFrame(estudantes).to_csv(f"{pasta}/estudantes.csv", index=False)
    pd.DataFrame(matriculas).to_csv(f"{pasta}/matriculas.csv", index=False)
    pd.DataFrame(frequencia).to_csv(f"{pasta}/frequencia.csv", index=False)
    pd.DataFrame(resumo).to_csv(f"{pasta}/resumo_frequencia.csv", index=False)


def main():

    seed = int(sys.argv[1])
    configurar_seed(seed)

    cursos = gerar_cursos()
    disciplinas = gerar_disciplinas()
    bairros = carregar_bairros()

    estudantes = gerar_estudantes(cursos, bairros)
    matriculas = gerar_matriculas(estudantes, disciplinas)

    frequencia, resumo = gerar_frequencia(matriculas)

    salvar_dados(seed, cursos, disciplinas, estudantes, matriculas, frequencia, resumo)


if __name__ == "__main__":
    main()