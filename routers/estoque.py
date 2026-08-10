from datetime import date
from typing import Any, Dict, List
from fastapi import APIRouter, Security, HTTPException, status, Query, Body
from classes.Logger import Logger as AppLogger
from classes.db_queries import load_query, queryAll2_Execute
from auth.Auth import User, get_current_user

router = APIRouter(
    prefix="/Estoque",
    tags=["Estoque"]
    # tags=["Módulo 11 - Adm. Interna do Estoque"]
)


def _to_query_date_str(valor: date | None) -> str | None:
    """Converte um date (ISO 8601 na entrada) para o formato DD-MM-YYYY esperado por esta query."""
    return valor.strftime("%d-%m-%Y") if valor else None


@router.get(
    path="/Indice-de-Conclusao-de-Bonus", 
    summary="KPI DE ÍNDICE DE CONCLUSÃO DE BÔNUS.",
    description="Calcular a volumetria de bônus por status e extrair o índice percentual de eficiência/vazão de recebimento do CD."
)
def r1106_GA01_Indice_de_Conclusao_de_Bonus(
    # current_user: User = Security(get_current_user, scopes=["estoque:read"]),
    codfilial: str = Query(None, description="Código da filial (CODFILIAL) no WinThor.", examples=["1"]),
    dt_inicio: date = Query(None, description="Data inicial do período de bônus. Formato ISO 8601.", examples=["2026-08-01"]),
    dt_fim: date = Query(None, description="Data final do período de bônus. Formato ISO 8601.", examples=["2026-08-10"])
):
    """OBJETIVO: Calcular a volumetria de bônus por status (Fechados, Pendentes, Cancelados) e extrair o índice percentual de eficiência/vazão de recebimento do CD."""
    script = "queries/1106_ga_01_Indice_de_Conclusao_de_Bonus.sql"
    query = load_query(script)
    bind_variables = {
        "CODFILIAL": codfilial,
        "DT_INICIO": _to_query_date_str(dt_inicio),
        "DT_FIM": _to_query_date_str(dt_fim),
    }
    result = queryAll2_Execute(query, bind_variables)
    return result