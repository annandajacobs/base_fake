import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


# CONFIG
st.set_page_config(page_title="Análise Educacional", layout="wide")

st.title("Análise de Frequência e Desempenho Acadêmico")

# apenas seeds existentes
seed = st.sidebar.selectbox(
    "Selecione o dataset (seed)",
    [10, 42, 99],
    index=2
)

pasta = f"../dados/seed_{seed}"


# CARREGAR DADOS
@st.cache_data
def carregar_dados(seed):

    pasta = f"../dados/seed_{seed}"

    estudantes = pd.read_csv(f"{pasta}/estudantes.csv")
    matriculas = pd.read_csv(f"{pasta}/matriculas.csv")
    frequencia = pd.read_csv(f"{pasta}/frequencia.csv")
    disciplinas = pd.read_csv(f"{pasta}/disciplinas.csv")
    resumo = pd.read_csv(f"{pasta}/resumo_frequencia.csv")
    cursos = pd.read_csv(f"{pasta}/cursos.csv")

    return estudantes, matriculas, frequencia, disciplinas, resumo, cursos


estudantes, matriculas, frequencia, disciplinas, resumo, cursos  = carregar_dados(seed)

mat_est = matriculas.merge(estudantes, on="id_estudante")
mat_disc = matriculas.merge(disciplinas, on="id_disciplina")
mat_res = matriculas.merge(resumo, on="id_matricula_disciplina")


# MÉTRICAS GERAIS
st.header("Métricas gerais")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Estudantes", len(estudantes))
col2.metric("Matrículas", len(matriculas))
col3.metric("Média de faltas", round(resumo["faltas_totais"].mean(), 2))
col4.metric(
    "Taxa reprovação",
    round((resumo["situacao_final"] == "REPROVADO").mean() * 100, 2)
)


# SITUAÇÃO DOS ESTUDANTES
st.header("Situação dos estudantes")

st.bar_chart(estudantes["situacao"].value_counts())


# HISTOGRAMA DE FALTAS
st.header("Distribuição de faltas por matrícula")

fig, ax = plt.subplots(figsize=(5, 3))

ax.hist(resumo["faltas_totais"], bins=20)

ax.set_xlabel("Faltas")
ax.set_ylabel("Quantidade")

st.pyplot(fig)


# FALTAS POR CURSO
st.header("Média de faltas por curso")

faltas_curso = mat_est.merge(resumo, on="id_matricula_disciplina")
faltas_curso = faltas_curso.groupby("id_curso")["faltas_totais"].mean()

fig, ax = plt.subplots(figsize=(5, 3))

faltas_curso.plot(kind="bar", ax=ax)

ax.set_ylabel("Média de faltas")

st.pyplot(fig)


# FALTAS POR DISCIPLINA
st.header("Faltas por disciplina")

faltas_disc = mat_disc.merge(resumo, on="id_matricula_disciplina")
faltas_disc = (
    faltas_disc
    .groupby("nome")["faltas_totais"]
    .mean()
    .sort_values(ascending=False)
)

fig, ax = plt.subplots(figsize=(6, 3))

faltas_disc.head(10).plot(kind="bar", ax=ax)

ax.set_ylabel("Média de faltas")

st.pyplot(fig)


# REPROVAÇÃO POR DISCIPLINA
st.header("Reprovação por disciplina")

rep_disc = mat_disc.merge(resumo, on="id_matricula_disciplina")

rep_disc = rep_disc.groupby("nome")["situacao_final"].apply(
    lambda x: (x == "REPROVADO").mean()
)

fig, ax = plt.subplots(figsize=(6, 3))

rep_disc.sort_values(ascending=False).head(10).plot(kind="bar", ax=ax)

ax.set_ylabel("Taxa reprovação")

st.pyplot(fig)


# FALTAS POR ALUNO
st.header("Distribuição de faltas por aluno")

faltas_aluno = mat_res.groupby("id_estudante")["faltas_totais"].sum()

fig, ax = plt.subplots(figsize=(5, 3))

ax.hist(faltas_aluno, bins=20)

ax.set_xlabel("Total de faltas por aluno")

st.pyplot(fig)


# ALUNOS EM RISCO
st.header("Alunos em risco acadêmico")

limite = st.slider("Limite de faltas", 0, 100, 20)

risco = faltas_aluno[faltas_aluno > limite]

st.metric("Alunos em risco", len(risco))


## top 20
st.header("Top 20 alunos com maior risco de evasão")

dados_risco = mat_est.merge(resumo, on="id_matricula_disciplina")

risco_df = dados_risco.groupby("id_estudante").agg(
    disciplinas=("id_disciplina", "count"),
    total_faltas=("faltas_totais", "sum"),
    reprovacoes=("situacao_final", lambda x: (x == "REPROVADO").sum())
).reset_index()

risco_df["faltas_media"] = risco_df["total_faltas"] / risco_df["disciplinas"]

risco_df["score_risco"] = (
    (risco_df["reprovacoes"] / risco_df["disciplinas"]) * 60 +
    (risco_df["faltas_media"] / 60) * 40
)

risco_df["score_risco"] = risco_df["score_risco"].round(2)

risco_df = risco_df.merge(
    estudantes[["id_estudante", "nome", "id_curso"]],
    on="id_estudante"
)

risco_df = risco_df.merge(
    cursos[["id_curso", "nome_curso"]],
    on="id_curso"
)

top_risco = risco_df.sort_values(
    "score_risco",
    ascending=False
).head(20)

tabela_final = top_risco[
    [
        "id_estudante",
        "nome",
        "nome_curso",
        "reprovacoes",
        "faltas_media",
        "score_risco"
    ]
]

st.dataframe(
    tabela_final,
    column_config={
        "score_risco": st.column_config.ProgressColumn(
            "Score de risco (%)",
            min_value=0,
            max_value=100
        )
    }
)

# TABELA EXPLORATÓRIA
st.header("Tabela de dados")

st.dataframe(resumo.head(100))