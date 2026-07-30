import io
import pandas as pd
from typing import Any, Dict, List
from fastapi import APIRouter, Security, HTTPException, status, Query, Body
from fastapi.responses import StreamingResponse
from classes.Logger import Logger as AppLogger
from classes.db_queries import load_query, queryAll2_Execute
from auth.Auth import User, get_current_user

router = APIRouter(
    prefix="/Financeiro", 
    tags=["Financeiro"]
)


@router.get("/1203-extrato-cliente")
def query_1203_Extrato_Cliente(
    # current_user: Annotated[None, Depends(get_current_active_user)],
    DATA_INICIAL: str = None,
    DATA_FINAL: str = None,
    # CODCLI = None,
    ):
    """ """

    CODCLI = None
    sql = "queries/1203-consulta-clientes.sql"
    bind_variables = {
        "DATA_INICIAL": DATA_INICIAL,
        "DATA_FINAL": DATA_FINAL,
        "CODCLI": CODCLI
    }
    query = load_query(sql)
    result = queryAll2_Execute(query, bind_variables)

    return result


@router.get("/1203-extrato-cliente/download")
def download_1203_Extrato_Cliente(
    # current_user: Annotated[None, Depends(get_current_active_user)],
    DATA_INICIAL: str = None,
    DATA_FINAL: str = None,
    # CODCLI = None,
    ):
    """Exemplo de Cliente: 118018"""

    CODCLI = None
    sql = "queries/1203-consulta-clientes.sql"
    bind_variables = {
        "DATA_INICIAL": DATA_INICIAL,
        "DATA_FINAL": DATA_FINAL,
        "CODCLI": CODCLI
    }
    query = load_query(sql)
    dados = queryAll2_Execute(query, bind_variables)

    # 2. Converte para DataFrame do pandas
    return download_tabela(dados, filename="1203_Extrato_Cliente")


@router.get("/export_risco_zero/download")
def export_risco_zero(
    # current_user: Annotated[None, Depends(get_current_active_user)],
    CODFILIAL = None,
    DTEMISSAO_INICIAL: str = None,
    DTEMISSAO_FINAL: str = None,
    ):
    """Exemplo de Cliente: 118018"""

    sql = "queries/export-risco-zero.sql"
    bind_variables = {
        "CODFILIAL": CODFILIAL,
        "DTEMISSAO_INICIAL": DTEMISSAO_INICIAL,
        "DTEMISSAO_FINAL": DTEMISSAO_FINAL
    }
    query = load_query(sql)
    dados = queryAll2_Execute(query, bind_variables)

    # 2. Converte para DataFrame do pandas
    return download_tabela(dados, filename="export_risco_zero")


# @router.get("/download-tabela")
def download_tabela(dados, filename="tabela_dados"):
    """Em teste!"""
    # 1. Dados que você quer colocar na tabela
    # dados = [
    #     {"id": 1, "nome": "Ana", "cargo": "Engenheira"},
    #     {"id": 2, "nome": "Bruno", "cargo": "Desenvolvedor"},
    # ]
    
    # 2. Converte para DataFrame do pandas
    df = pd.DataFrame(dados)
    
    # 3. Escreve o DataFrame em um buffer em memória (Excel)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    buffer.seek(0)
    
    # 4. Retorna o arquivo com o cabeçalho para download
    nome_arquivo = f"{filename}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{nome_arquivo}"'}
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )