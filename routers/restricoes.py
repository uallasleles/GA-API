import json
import logging
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, HTTPException, Security, UploadFile, status
from fastapi.responses import Response

from auth.Auth import User, get_current_user
from classes import restricao_venda as regras
from classes import restricao_venda_db as banco
from classes import restricao_venda_scripts as scripts

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/Vendas/restricoes",
    tags=["Restrições de venda"],
)

SCOPE = "restricao:read"
MAX_BYTES = 5 * 1024 * 1024
BRASILIA_TZ = timezone(timedelta(hours=-3))


class Formato(str, Enum):
    json = "json"
    zip = "zip"


@router.post("/simular", summary="Simula restrições de cliente x prazo (rotina 391), sem gravar nada")
def simular_restricoes(
    current_user: Annotated[User, Security(get_current_user, scopes=[SCOPE])],
    file: UploadFile = File(..., description="Planilha .xlsx ou .csv com a coluna CODCLI (ou 'CÓDIGO DO CLIENTE') e, "
                                             "opcionalmente, CODPLPAG (ou 'CÓDIGO PRAZO', ex.: '2, 13, 14')."),
    motivo: str = Form(..., description="Motivo gravado na restrição (até 50 caracteres)."),
    prazos: Optional[str] = Form(None, description="Prazos aplicados a todos os clientes, ex.: '2,13,14'. "
                                                   "Se informado, substitui a coluna de prazos da planilha."),
    origem: str = Form("O", description="O=Todas (padrão), T, B, R, C, F ou W."),
    somente_ativos: bool = Form(False, description="Deixa de fora os clientes inativos."),
    formato: Formato = Form(Formato.json, description="'json' = análise; 'zip' = scripts SQL + análise."),
):
    """
    Confere a planilha contra o banco (somente leitura) e devolve: o que seria
    inserido, o que já está coberto, clientes inexistentes, inativos ou
    bloqueados, uso dos prazos em 12 meses e outros prazos parcelados.

    Com `formato=zip`, devolve também os scripts para execução manual
    (pré-conferência, teste com um cliente, inclusão, conferência e reversão).
    **Este endpoint não grava nada no Oracle.**
    """
    conteudo = file.file.read(MAX_BYTES + 1)
    if len(conteudo) > MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Arquivo maior que 5 MB.")
    try:
        motivo_ok = regras.normalizar_motivo(motivo)
        origem_ok = regras.normalizar_origem(origem)
        padrao = regras.lista_de_codigos(prazos, "Prazo")
        planilha = regras.ler_planilha(os.path.basename(file.filename or ""), conteudo, padrao)
    except regras.ErroEntrada as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"mensagem": "Entrada inválida.", "problemas": exc.problemas},
        )

    pares = planilha["pares"]
    try:
        dados = banco.coletar(sorted({c for c, _ in pares}), sorted({p for _, p in pares}))
    except Exception as exc:
        logger.exception("Restrições: falha ao consultar o Oracle")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Não foi possível consultar o Oracle ({type(exc).__name__}).",
        )

    resultado = regras.analisar(pares, origem_ok, motivo_ok, dados, somente_ativos)
    resultado["arquivo"] = {"linhas_lidas": planilha["linhas_lidas"], "combinacoes_repetidas": planilha["pares_repetidos"]}
    logger.info("Restrições: simulação usuario=%s combinacoes=%s a_inserir=%s",
                current_user.username, len(pares), resultado["resumo"]["combinacoes_a_inserir"])

    if formato == Formato.json:
        return resultado

    if not resultado["a_inserir"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"mensagem": "Não há nada a inserir, então não há scripts. Use formato=json para ver a análise.",
                    "resumo": resultado["resumo"], "alertas": resultado["alertas"]},
        )
    arquivos = scripts.gerar_arquivos(resultado)
    arquivos["analise.json"] = json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
    nome = f"restricoes_{datetime.now(BRASILIA_TZ):%Y%m%d_%H%M%S}.zip"
    return Response(
        content=scripts.gerar_zip(arquivos),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
