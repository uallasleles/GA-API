import csv
import io
from datetime import date, datetime, timedelta, timezone
import pandas as pd
from typing import Any, Dict, List, Literal
from fastapi import APIRouter, Security, HTTPException, status, Query, Body
from fastapi.responses import StreamingResponse
from classes.Logger import Logger as AppLogger
from classes.db_queries import load_query, queryAll2_Execute
from auth.Auth import User, get_current_user

router = APIRouter(
    prefix="/Financeiro",
    tags=["Financeiro"]
)

BRASILIA_TZ = timezone(timedelta(hours=-3))


def _to_br_date_str(valor: date | None) -> str | None:
    """Converte um date (vindo do seletor de calendário) para o formato DD/MM/YYYY esperado pelas queries."""
    return valor.strftime("%d/%m/%Y") if valor else None


@router.get("/1203-extrato-cliente")
def query_1203_Extrato_Cliente(
    # current_user: Annotated[None, Depends(get_current_active_user)],
    DATA_INICIAL: date = Query(None, description="Data inicial do período (última compra válida). Formato ISO 8601.", examples=["2026-08-01"]),
    DATA_FINAL: date = Query(None, description="Data final do período (última compra válida). Formato ISO 8601.", examples=["2026-08-10"]),
    # CODCLI = None,
    ):
    """ """

    CODCLI = None
    sql = "queries/1203-consulta-clientes.sql"
    bind_variables = {
        "DATA_INICIAL": _to_br_date_str(DATA_INICIAL),
        "DATA_FINAL": _to_br_date_str(DATA_FINAL),
        "CODCLI": CODCLI
    }
    query = load_query(sql)
    result = queryAll2_Execute(query, bind_variables)

    return result


@router.get("/1203-extrato-cliente/download")
def download_1203_Extrato_Cliente(
    # current_user: Annotated[None, Depends(get_current_active_user)],
    DATA_INICIAL: date = Query(None, description="Data inicial do período (última compra válida). Formato ISO 8601.", examples=["2026-08-01"]),
    DATA_FINAL: date = Query(None, description="Data final do período (última compra válida). Formato ISO 8601.", examples=["2026-08-10"]),
    # CODCLI = None,
    ):
    """Exemplo de Cliente: 118018"""

    CODCLI = None
    sql = "queries/1203-consulta-clientes.sql"
    bind_variables = {
        "DATA_INICIAL": _to_br_date_str(DATA_INICIAL),
        "DATA_FINAL": _to_br_date_str(DATA_FINAL),
        "CODCLI": CODCLI
    }
    query = load_query(sql)
    dados = queryAll2_Execute(query, bind_variables)

    # 2. Converte para DataFrame do pandas
    return download_tabela(dados, filename="1203_Extrato_Cliente")


@router.get("/export_risco_zero/download")
def export_risco_zero(
    # current_user: Annotated[None, Depends(get_current_active_user)],
    CODFILIAL: str = Query("Cód. da Filial", description="Código da filial (CODFILIAL) no WinThor. Se omitido, retorna títulos de todas as filiais.", examples=["1"]),
    DTEMISSAO_INICIAL: date = Query("Data de Emissão Inicial", description="Data inicial de emissão do título.", examples=["2026-08-01"]),  # noqa: B008
    DTEMISSAO_FINAL: date = Query("Data de Emissão Final", description="Data final de emissão do título.", examples=["2026-08-10"]),  # noqa: B008
    formato: Literal["xlsx", "csv"] = Query("xlsx", description="Formato do arquivo exportado: xlsx (padrão) ou csv (aspas duplas, separador ';', decimal ',').", examples=["xlsx"]),
    ):
    """
    FINALIDADE ..:  Extração de dados de Contas a Receber para exportação ao BigQuery da Risco Zero (gestão de dados, análise de crédito e avaliação de risco de inadimplência).   
    ORIGEM ......:  WinThor (PCPREST - títulos de cobrança / PCCLIENT - cadastro de clientes)   
    LAYOUT ......:  cnpjparceiro (STRING) | cnpj (STRING) | telefone (STRING) | dtalancto (DATE) | numdocumento (STRING) | valor (FLOAT) | dtacompensacao (DATE) | dtavencimento (DATE)   
    """

    sql = "queries/export-risco-zero.sql"
    bind_variables = {
        "CODFILIAL": CODFILIAL,
        "DTEMISSAO_INICIAL": _to_br_date_str(DTEMISSAO_INICIAL),
        "DTEMISSAO_FINAL": _to_br_date_str(DTEMISSAO_FINAL)
    }
    query = load_query(sql)
    dados = queryAll2_Execute(query, bind_variables)

    cnpj = _extract_column(dados, "cnpjparceiro") or "sem-cnpj"
    timestamp = datetime.now(BRASILIA_TZ).strftime("%Y%m%d_%H%M%S")

    return download_tabela(
        dados,
        filename=f"{cnpj}_{timestamp}",
        formato=formato,
        csv_quote_all=True,
        csv_decimal=",",
    )


def _extract_column(dados, column_name):
    """Pega o valor de uma coluna na primeira linha, sem depender da caixa (Oracle costuma retornar em maiúsculas)."""
    if not dados:
        return None
    primeira_linha = dados[0]
    return next(
        (valor for chave, valor in primeira_linha.items() if chave.lower() == column_name.lower()),
        None,
    )


# @router.get("/download-tabela")
def download_tabela(
    dados,
    filename="tabela_dados",
    formato: Literal["xlsx", "csv"] = "xlsx",
    csv_quote_all: bool = False,
    csv_decimal: str = ".",
):
    """Em teste!"""
    # 1. Dados que você quer colocar na tabela
    # dados = [
    #     {"id": 1, "nome": "Ana", "cargo": "Engenheira"},
    #     {"id": 2, "nome": "Bruno", "cargo": "Desenvolvedor"},
    # ]

    # 2. Converte para DataFrame do pandas
    df = pd.DataFrame(dados)

    # 3. Escreve o DataFrame em um buffer em memória
    buffer = io.BytesIO()
    if formato == "csv":
        # separador ";" e BOM utf-8 para abrir corretamente no Excel em português
        csv_text = df.to_csv(
            index=False,
            sep=";",
            decimal=csv_decimal,
            quoting=csv.QUOTE_ALL if csv_quote_all else csv.QUOTE_MINIMAL,
        )
        buffer.write(csv_text.encode("utf-8-sig"))
        media_type = "text/csv"
    else:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Dados")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    buffer.seek(0)

    # 4. Retorna o arquivo com o cabeçalho para download
    nome_arquivo = f"{filename}.{formato}"
    headers = {"Content-Disposition": f'attachment; filename="{nome_arquivo}"'}

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers=headers
    )