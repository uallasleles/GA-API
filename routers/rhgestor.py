import logging
import os
from enum import Enum
from typing import Annotated, Optional

import requests
from fastapi import APIRouter, Depends, File, HTTPException, Query, Security, UploadFile, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from auth.Auth import User, get_current_user
from auth.database import get_session
from auth.models.rhgestor import RHGestorEnvioDB
from classes import rhgestor_csv as csvlib

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/RHGestor",
    tags=["RHGestor"],
)

SCOPE = "rhgestor:importar"
BASE_URL_PADRAO = "https://apisecure.rhgestor.com.br"
TIMEOUT = 60  # segundos
MAX_BYTES = 25 * 1024 * 1024


class Layout(str, Enum):
    colaboradores = "colaboradores"
    ferias = "ferias"
    atestados = "atestados"
    financeiro = "financeiro"


class Ambiente(str, Enum):
    teste = "teste"
    producao = "producao"


def _credenciais(ambiente: Ambiente) -> tuple:
    """Lê e-mail/chave do ambiente (somente variáveis de ambiente)."""
    sufixo = ambiente.value.upper()
    email = os.getenv(f"RHGESTOR_EMAIL_{sufixo}", "").strip()
    chave = os.getenv(f"RHGESTOR_KEY_{sufixo}", "").strip()
    if not email or not chave:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Credencial do ambiente '{ambiente.value}' não configurada no servidor "
                   f"(RHGESTOR_EMAIL_{sufixo} / RHGESTOR_KEY_{sufixo}).",
        )
    return email, chave


def _base_url() -> str:
    return os.getenv("RHGESTOR_BASE_URL", BASE_URL_PADRAO).rstrip("/")


def _ler_arquivo(file: UploadFile) -> bytes:
    conteudo = file.file.read(MAX_BYTES + 1)
    if len(conteudo) > MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Arquivo maior que 25 MB.")
    if not conteudo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio.")
    return conteudo


def _converter(layout: Layout, conteudo: bytes) -> tuple:
    """Aplica as conversões (só colaboradores). Devolve (bytes, alteracoes)."""
    if layout != Layout.colaboradores:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="converter=true só existe para o layout 'colaboradores' (101).")
    try:
        return csvlib.converter_colaboradores(conteudo)
    except csvlib.ErroConversao as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"mensagem": "Conversão não realizada: corrija os erros abaixo.", "problemas": exc.problemas},
        )


@router.post("/Validar/{layout}", summary="Pré-valida um CSV sem enviá-lo à Sólides")
def validar_csv(
    current_user: Annotated[User, Security(get_current_user, scopes=[SCOPE])],
    layout: Layout,
    file: UploadFile = File(..., description="Arquivo .csv (separador ';', UTF-8)."),
    converter: bool = Query(False, description="Só colaboradores: valida o arquivo já convertido (nada é enviado nem gravado)."),
):
    """
    Confere cabeçalho, separador, UTF-8 e número de colunas. Para `colaboradores`
    (101) confere também CODIGO, datas, SEXO e tamanhos; acentos, formato de salário,
    CEP, CPF e telefone são só **alertas**. Devolve problemas com linha e campo.
    Nada é enviado à Sólides.
    """
    conteudo = _ler_arquivo(file)
    alteracoes = None
    if converter:
        conteudo, alteracoes = _converter(layout, conteudo)
    resultado = csvlib.validar(layout.value, conteudo)
    if alteracoes is not None:
        resultado["conversao"] = {"aplicada": True, "alteracoes": alteracoes}
    return resultado


@router.post("/Importar/{layout}", summary="Envia um CSV à API da Sólides (RHGestor)")
def importar_csv(
    current_user: Annotated[User, Security(get_current_user, scopes=[SCOPE])],
    session: Annotated[Session, Depends(get_session)],
    layout: Layout,
    file: UploadFile = File(..., description="Arquivo .csv a enviar, repassado sem alteração (exceto com converter=true)."),
    ambiente: Ambiente = Query(Ambiente.teste, description="'teste' (padrão) ou 'producao' (só se a credencial de produção estiver configurada)."),
    converter: bool = Query(False, description="Só colaboradores (101): aplica as conversões (CODIGO, acentos, salários) antes de enviar. Padrão: desligado."),
):
    """
    Autentica na Sólides com a credencial do ambiente escolhido (variáveis de
    ambiente do servidor) e envia o arquivo em `POST /api/fileimport`.
    A resposta da Sólides não traz contagem de linhas nem erros por linha:
    use antes `POST /RHGestor/Validar/{layout}`. Cada envio é gravado em
    `GET /RHGestor/Historico`.
    """
    codigo_layout = csvlib.LAYOUTS[layout.value][0]
    email, chave = _credenciais(ambiente)  # falha cedo, antes de ler o arquivo
    conteudo = _ler_arquivo(file)
    nome = os.path.basename(file.filename or "arquivo.csv")

    alteracoes = None
    if converter:
        conteudo, alteracoes = _converter(layout, conteudo)

    registro = RHGestorEnvioDB(
        usuario=current_user.username,
        layout=layout.value,
        codigo_layout=codigo_layout,
        ambiente=ambiente.value,
        arquivo=nome,
        tamanho_bytes=len(conteudo),
        linhas=csvlib.contar_linhas(conteudo),
        convertido=converter,
    )

    http_status: Optional[int] = None
    resposta: object = None
    sucesso = False
    mensagem = None
    try:
        base = _base_url()
        auth = requests.post(f"{base}/api/auth", json={"email": email, "key": chave}, timeout=TIMEOUT)
        token = None
        try:
            token = ((auth.json() or {}).get("Data") or {}).get("Token")
        except ValueError:
            pass
        if auth.status_code != 200 or not token:
            http_status = auth.status_code
            mensagem = "Falha na autenticação na API da Sólides (verifique as credenciais configuradas)."
            resposta = {"mensagem": mensagem}
        else:
            envio = requests.post(
                f"{base}/api/fileimport",
                headers={"Authorization": f"Bearer {token}"},
                data={"layout": codigo_layout},
                files={"file": (nome, conteudo, "text/csv")},
                timeout=TIMEOUT,
            )
            http_status = envio.status_code
            try:
                resposta = envio.json()
            except ValueError:
                resposta = {"texto": envio.text[:500]}
            if isinstance(resposta, dict):
                mensagem = resposta.get("Message") or resposta.get("message")
                status_sol = str(resposta.get("Status") or "").lower()
            else:
                status_sol = ""
            sucesso = envio.ok and status_sol == "success"
    except requests.RequestException as exc:
        mensagem = f"Erro de comunicação com a API da Sólides: {type(exc).__name__}"
        resposta = {"mensagem": mensagem}
        logger.warning("RHGestor: %s", mensagem)

    registro.http_status = http_status
    registro.sucesso = sucesso
    registro.mensagem = mensagem
    session.add(registro)
    session.commit()
    session.refresh(registro)
    logger.info("RHGestor envio id=%s usuario=%s layout=%s ambiente=%s sucesso=%s", registro.id, registro.usuario, layout.value, ambiente.value, sucesso)

    corpo = {
        "id_historico": registro.id,
        "sucesso": sucesso,
        "ambiente": ambiente.value,
        "layout": layout.value,
        "codigo_layout": codigo_layout,
        "arquivo": nome,
        "tamanho_bytes": registro.tamanho_bytes,
        "linhas": registro.linhas,
        "http_status_solides": http_status,
        "resposta_solides": resposta,
    }
    if alteracoes is not None:
        corpo["conversao"] = {"aplicada": True, "alteracoes": alteracoes}
    return JSONResponse(content=corpo, status_code=status.HTTP_200_OK if sucesso else status.HTTP_502_BAD_GATEWAY)


@router.get("/Historico", summary="Histórico de envios ao RHGestor")
def historico(
    current_user: Annotated[User, Security(get_current_user, scopes=[SCOPE])],
    session: Annotated[Session, Depends(get_session)],
    layout: Optional[Layout] = Query(None),
    ambiente: Optional[Ambiente] = Query(None),
    sucesso: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Lista os envios, do mais recente para o mais antigo."""
    consulta = select(RHGestorEnvioDB)
    if layout:
        consulta = consulta.where(RHGestorEnvioDB.layout == layout.value)
    if ambiente:
        consulta = consulta.where(RHGestorEnvioDB.ambiente == ambiente.value)
    if sucesso is not None:
        consulta = consulta.where(RHGestorEnvioDB.sucesso == sucesso)
    consulta = consulta.order_by(RHGestorEnvioDB.criado_em.desc(), RHGestorEnvioDB.id.desc()).offset(offset).limit(limit)
    return [
        {
            "id": r.id,
            "criado_em": r.criado_em.isoformat(),
            "usuario": r.usuario,
            "layout": r.layout,
            "codigo_layout": r.codigo_layout,
            "ambiente": r.ambiente,
            "arquivo": r.arquivo,
            "tamanho_bytes": r.tamanho_bytes,
            "linhas": r.linhas,
            "convertido": r.convertido,
            "http_status": r.http_status,
            "sucesso": r.sucesso,
            "mensagem": r.mensagem,
        }
        for r in session.exec(consulta).all()
    ]
