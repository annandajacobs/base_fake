import sys
from config import configurar_seed
from geradores import gerar_cursos, gerar_disciplinas, gerar_estudantes, gerar_frequencia, gerar_matriculas, gerar_presenca_campus, gerar_tabela_risco
from storage import carregar_bairros, salvar_dados

def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <seed>")
        sys.exit(1)

    seed = int(sys.argv[1])
    configurar_seed(seed)

    print(f" \n Geração controlada — seed={seed} \n")

    cursos      = gerar_cursos()
    disciplinas = gerar_disciplinas()
    bairros     = carregar_bairros()

    estudantes      = gerar_estudantes(cursos, bairros)
    matriculas      = gerar_matriculas(estudantes, disciplinas)
    presenca_campus = gerar_presenca_campus(estudantes)
    frequencia = gerar_frequencia(matriculas, estudantes, presenca_campus)
    tabela_risco    = gerar_tabela_risco(estudantes, matriculas, frequencia)

    salvar_dados(seed, cursos, disciplinas, estudantes, matriculas,
                 frequencia, presenca_campus, tabela_risco)

    print(" \n Geração concluída com totalizações verificadas.")


if __name__ == "__main__":
    main()