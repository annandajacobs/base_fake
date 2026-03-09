import sys
import pandas as pd

SEED = int(sys.argv[1])

pasta = f"../dados/seed_{SEED}"

# carrega dados
estudantes = pd.read_csv(f"{pasta}/estudantes.csv")
matriculas = pd.read_csv(f"{pasta}/matriculas.csv")
frequencia = pd.read_csv(f"{pasta}/frequencia.csv")
disciplinas = pd.read_csv(f"{pasta}/disciplinas.csv")
resumo = pd.read_csv(f"{pasta}/resumo_frequencia.csv")

print(f"\nAnalisando dataset da seed {SEED}\n")


# estudantes
print("Total de estudantes:")
print(len(estudantes))

print("\nSituação dos estudantes:")
print(estudantes["situacao"].value_counts())

print("\nAlunos por curso:")
print(estudantes["id_curso"].value_counts())

print("\nAlunos por cidade:")
print(estudantes["cidade"].value_counts())


# matriculas
print("\nTotal de matrículas em disciplinas:")
print(len(matriculas))

mat_est = matriculas.merge(estudantes, on="id_estudante")

print("\nMatrículas por curso:")
print(mat_est["id_curso"].value_counts())


# faltas e frequencia
print("\nMédia de faltas por matrícula:")
print(resumo["faltas_totais"].mean())

print("\nMediana de faltas por matrícula:")
print(resumo["faltas_totais"].median())

faltas_por_aluno = (
    matriculas
    .merge(resumo, on="id_matricula_disciplina")
    .groupby("id_estudante")["faltas_totais"]
    .sum()
)

print("\nMediana de faltas por aluno:")
print(faltas_por_aluno.median())


print("\nDistribuição de presença:")
print(frequencia["situacao"].value_counts())


# situação final
print("\nSituação final nas disciplinas:")
print(resumo["situacao_final"].value_counts())


# disciplinas
mat_disc = matriculas.merge(disciplinas, on="id_disciplina")

print("\nDisciplinas mais cursadas:")
print(mat_disc["nome"].value_counts().head(10))


# relação faltas x reprovação
reprovados = resumo[resumo["situacao_final"] == "REPROVADO"]

print("\nMédia de faltas dos reprovados:")
print(reprovados["faltas_totais"].mean())

print("\nMédia de faltas dos aprovados:")
print(resumo[resumo["situacao_final"] == "APROVADO"]["faltas_totais"].mean())