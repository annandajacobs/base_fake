from faker import Faker
import random
import csv
import pandas as pd

fake = Faker("pt_BR")

lista_cursos = [
    "Desenvolvimento de Sistemas",
    "Edificações",
    "Eletrônica",
    "Eletrotécnica",
    "Estradas",
    "Mecânica",
    "Química"
]

cursos = []
for i, nome in enumerate(lista_cursos, start=1):
    cursos.append({
        "id_curso": i,
        "nome_curso": nome
    })

lista_disciplinas = [
    "Algoritmos",
    "Programação Orientada a Objetos",
    "Redes de Computadores",
    "Gestão de Projetos",
    "Banco de Dados",
    "Redes de Computadores",
    "Desenvolvimento Web",
    "Desenho Técnico (AutoCAD)",
    "Resistência dos Materiais",
    "Topografia",
    "Mecânica dos Solos",
    "Hidráulica",
    "Materiais de Construção",
    "Circuitos Elétricos",
    "Eletrônica Analógica/Digital",
    "Instalações Elétricas",
    "Automação Industrial",
    "Desenho Eletroeletrônico",
    "Metrologia",
    "Desenho Mecânico",
    "Processos de Fabricação",
    "Soldagem",
    "Elementos de Máquinas",
    "Química Analítica",
    "Química Orgânica",
    "Operações Unitárias",
    "Tratamento de Águas",
    "Laboratório de Química",
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

disciplinas = []
for i, nome in enumerate(lista_disciplinas, start=1):
    disciplinas.append({
        "id_disciplina": i,
        "nome": nome
    })


arquivo_excel = "recursos/bairros.xlsx"

df = pd.read_excel(arquivo_excel)

cidade_bairros = {}

for _, row in df.iterrows():
    cidade = row["NM_DIST"]
    bairro = row["NM_BAIRRO"]

    if cidade not in cidade_bairros:
        cidade_bairros[cidade] = []

    cidade_bairros[cidade].append(bairro)

cidades = list(cidade_bairros.keys())

estudantes = []

for i in range(1, 4001):

    cidade_escolhida = random.choices(
        cidades,
        weights=[70 if c == "Maceió" else 1 for c in cidades],
        k=1
    )[0]
    bairro_escolhido = random.choice(cidade_bairros[cidade_escolhida])

    estudantes.append({
        "id_estudante": i,
        "matricula": fake.unique.random_number(digits=10),
        "nome": fake.name(),
        "id_curso": random.choice(cursos)["id_curso"],
        "ano_ingresso": random.randint(2022, 2026),
        "situacao": random.choice(["ATIVO", "TRANCADO", "EVADIDO"]),
        "bairro": bairro_escolhido,
        "cidade": cidade_escolhida,
    })

matriculas_disciplina = []
id_md = 1

for estudante in estudantes:
    for disc in random.sample(disciplinas, 3):
        matriculas_disciplina.append({
            "id_matricula_disciplina": id_md,
            "id_estudante": estudante["id_estudante"],
            "id_disciplina": disc["id_disciplina"],
            "ano_letivo": 2026,
            "faltas_totais": random.randint(0, 20),
            "situacao": random.choice(["MATRICULADO", "APROVADO", "REPROVADO"])
        })
        id_md += 1


registro_frequencia = []
id_rf = 1

for matricula in matriculas_disciplina:
    for _ in range(15):
        registro_frequencia.append({
            "id_registro": id_rf,
            "id_matricula_disciplina": matricula["id_matricula_disciplina"],
            "data_aula": fake.date_between(start_date="-3M", end_date="today"),
            "situacao": random.choice(["PRESENTE", "FALTA"])
        })
        id_rf += 1


def salvar_csv(nome_arquivo, dados):
    with open(nome_arquivo, mode="w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=dados[0].keys())
        writer.writeheader()
        writer.writerows(dados)

salvar_csv("dados/cursos.csv", cursos)
salvar_csv("dados/disciplinas.csv", disciplinas)
salvar_csv("dados/estudantes.csv", estudantes)
salvar_csv("dados/matriculas_disciplina.csv", matriculas_disciplina)
salvar_csv("dados/registro_frequencia.csv", registro_frequencia)

print("CSV gerados com sucesso!")