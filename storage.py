import os
import pandas as pd

def carregar_bairros():
    df = pd.read_excel("recursos/bairros.xlsx")
    return df.groupby("NM_DIST")["NM_BAIRRO"].apply(list).to_dict()

def salvar_dados(seed, cursos, disciplinas, estudantes, matriculas,
                 frequencia, presenca_campus, tabela_risco):

    pasta = f"dados/seed_{seed}"
    os.makedirs(pasta, exist_ok=True)

    df_est = pd.DataFrame(estudantes).drop(columns=["perfil_risco"])

    df_est.to_csv(f"{pasta}/estudantes.csv", index=False)
    pd.DataFrame(cursos).to_csv(f"{pasta}/cursos.csv", index=False)
    pd.DataFrame(disciplinas).to_csv(f"{pasta}/disciplinas.csv", index=False)
    pd.DataFrame(matriculas).to_csv(f"{pasta}/matriculas.csv", index=False)
    pd.DataFrame(frequencia).to_csv(f"{pasta}/frequencia.csv", index=False)
    pd.DataFrame(presenca_campus).to_csv(f"{pasta}/presenca_campus.csv", index=False)
    tabela_risco.to_csv(f"{pasta}/tabela_risco_evasao.csv", index=False)

    print(f"\n✓ Dados salvos em: {pasta}/")
    print("  Arquivos gerados:")
    for f in sorted(os.listdir(pasta)):
        tamanho = os.path.getsize(f"{pasta}/{f}") / 1024
        print(f"    {f:<40} {tamanho:>8.1f} KB")