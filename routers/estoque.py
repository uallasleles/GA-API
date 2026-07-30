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


@router.get(
    path="/Indice-de-Conclusao-de-Bonus", 
    summary="KPI DE ÍNDICE DE CONCLUSÃO DE BÔNUS.",
    description="Calcular a volumetria de bônus por status e extrair o índice percentual de eficiência/vazão de recebimento do CD."
)
def r1106_GA01_Indice_de_Conclusao_de_Bonus(
    # current_user: User = Security(get_current_user, scopes=["estoque:read"]),
    codfilial: str = None, 
    dt_inicio: str = None, 
    dt_fim: str = None
):
    """OBJETIVO: Calcular a volumetria de bônus por status (Fechados, Pendentes, Cancelados) e extrair o índice percentual de eficiência/vazão de recebimento do CD."""
    script = "queries/1106_ga_01_Indice_de_Conclusao_de_Bonus.sql"
    query = load_query(script)
    bind_variables = {"CODFILIAL": codfilial, "DT_INICIO": dt_inicio, "DT_FIM": dt_fim}
    result = queryAll2_Execute(query, bind_variables)
    return result