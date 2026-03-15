import re
from config import ANO_LETIVO, TOTAL_AULAS
from datetime import datetime, timedelta

def limpar_nome(nome: str) -> str:
    padrao = r'^(sr|sra|srta|Dr|Dra)\.?\s+'
    return re.sub(padrao, '', nome, flags=re.IGNORECASE).strip()

def gerar_dias_letivos() -> list:
    dias = []
    data = datetime(ANO_LETIVO, 2, 1)
    while len(dias) < TOTAL_AULAS:
        if data.weekday() < 5:
            dias.append(data)
        data += timedelta(days=1)
    return dias

def _n_por_perc(total: int, perc: float) -> int:
    return round(total * perc)

def _upgrade_risco(perfil: str) -> str:
    """Sobe um nível de risco: BAIXO→MEDIO, MEDIO→ALTO, ALTO→ALTO."""
    return {"BAIXO": "MEDIO", "MEDIO": "ALTO", "ALTO": "ALTO"}.get(perfil, perfil)
