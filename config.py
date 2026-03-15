import random
from faker import Faker
import numpy as np

fake = Faker("pt_BR")

TOTAL_ESTUDANTES        = 5_000
TOTAL_AULAS             = 80
DISCIPLINAS_POR_ALUNO   = 5
ANO_LETIVO              = 2026

PERC_RISCO_BAIXO  = 0.50
PERC_RISCO_MEDIO  = 0.30
PERC_RISCO_ALTO   = 0.20

NOTAS_RISCO_BAIXO = (7.0, 10.0)
NOTAS_RISCO_MEDIO = (5.0, 7.0)
NOTAS_RISCO_ALTO  = (0.0, 5.0)
NOTA_LIMIAR_RISCO = 5.0

FALTAS_RISCO_BAIXO  = (0,  5)
FALTAS_RISCO_MEDIO  = (6,  14)
FALTAS_RISCO_ALTO   = (15, 20) 

PROB_CAMPUS_RISCO_BAIXO  = 0.95
PROB_CAMPUS_RISCO_MEDIO  = 0.85
PROB_CAMPUS_RISCO_ALTO   = 0.70

PROB_UPGRADE_RISCO_FORA_MACEIO = 0.35

def configurar_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)
