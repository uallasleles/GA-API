import io
from datetime import datetime, timedelta, timezone
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, Security, UploadFile, status
from fastapi.responses import StreamingResponse

from auth.Auth import get_current_user
from classes.db_queries import bulk_update_Execute, load_query, queryAll2_Execute

router = APIRouter(
    prefix="/Frete",
    tags=["Frete"]
)

BRASILIA_TZ = timezone(timedelta(hours=-3))

CHAVE_COLUNAS = ["CODTRANSPORTE", "CODPRACAORIGEM", "CODPRACADESTINO", "CODTIPOVEICULO"]
VALOR_COLUNAS = ["VLINICIO", "VLFINAL"]
COLUNAS_OBRIGATORIAS = CHAVE_COLUNAS + VALOR_COLUNAS


@router.get("/tabela-de-frete/export")
def export_tabela_de_frete(
    current_user: Annotated[None, Security(get_current_user, scopes=["frete:read"])],
    CODTRANSPORTE: str = Query(None, description="Código do transporte (contrato). Se omitido, considera todos.", examples=["1"]),
    CODTRANSPORTADORA: str = Query(None, description="Código da transportadora (CODFORNEC).", examples=["12086"]),
    TIPOTRANSPORTE: str = Query(None, description="Tipo de transporte, conforme cadastro WinThor.", examples=["1"]),
    CODTIPOVEICULO: str = Query(None, description="Código do tipo de veículo.", examples=["1"]),
):
    """
    Exporta a tabela de frete (rotina 982 - Cadastro de Figura de Frete) como planilha .xlsx.
    A mesma planilha, com VLINICIO/VLFINAL editados, pode ser reenviada em
    POST /Frete/tabela-de-frete/import para atualizar os valores.
    """
    sql = "queries/export-tabela-de-frete.sql"
    bind_variables = {
        "CODTRANSPORTE": CODTRANSPORTE,
        "CODTRANSPORTADORA": CODTRANSPORTADORA,
        "TIPOTRANSPORTE": TIPOTRANSPORTE,
        "CODTIPOVEICULO": CODTIPOVEICULO,
    }
    query = load_query(sql)
    dados = queryAll2_Execute(query, bind_variables)

    df = pd.DataFrame(dados)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="TabelaDeFrete")
    buffer.seek(0)

    timestamp = datetime.now(BRASILIA_TZ).strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"tabela_de_frete_{timestamp}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{nome_arquivo}"'}

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.post("/tabela-de-frete/import")
def import_tabela_de_frete(
    current_user: Annotated[None, Security(get_current_user, scopes=["frete:write"])],
    file: UploadFile = File(..., description="Planilha .xlsx no mesmo formato do export (colunas CODTRANSPORTE, CODPRACAORIGEM, CODPRACADESTINO, CODTIPOVEICULO, VLINICIO, VLFINAL)."),
):
    """
    Atualiza VLINICIO/VLFINAL da tabela de frete a partir de uma planilha
    .xlsx (mesmo template gerado por GET /Frete/tabela-de-frete/export).

    As demais colunas da planilha (transportadora, praças, vigência etc.)
    são só referência e são ignoradas na importação. O casamento de cada
    linha com o registro a atualizar usa a chave CODTRANSPORTE +
    CODPRACAORIGEM + CODPRACADESTINO + CODTIPOVEICULO.

    Importação best-effort: linhas inválidas ou não encontradas são
    reportadas em "erros", sem impedir a atualização das demais.
    """
    try:
        df = pd.read_excel(file.file)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Não foi possível ler o arquivo como .xlsx: {exc}")

    df.columns = [str(coluna).strip().upper() for coluna in df.columns]

    faltando = [coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in df.columns]
    if faltando:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Colunas obrigatórias ausentes na planilha: {', '.join(faltando)}",
        )

    rows = []
    erros_leitura = []
    for indice, linha in df.iterrows():
        numero_linha = indice + 2  # linha 1 da planilha é o cabeçalho
        try:
            rows.append({
                "CODTRANSPORTE": int(linha["CODTRANSPORTE"]),
                "CODPRACAORIGEM": int(linha["CODPRACAORIGEM"]),
                "CODPRACADESTINO": int(linha["CODPRACADESTINO"]),
                "CODTIPOVEICULO": int(linha["CODTIPOVEICULO"]),
                "VLINICIO": float(linha["VLINICIO"]),
                "VLFINAL": float(linha["VLFINAL"]),
            })
        except (TypeError, ValueError):
            erros_leitura.append({"linha": numero_linha, "erro": "Chave ou valor inválido/ausente nessa linha."})

    resultado = bulk_update_Execute(load_query("queries/update-tabela-de-frete.sql"), rows) if rows else {
        "atualizados": 0,
        "nao_encontrados": 0,
        "erros": [],
    }
    resultado["erros"] = erros_leitura + resultado["erros"]

    return resultado
