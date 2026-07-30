from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
import json

# Importações locais
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger
from builders.routeRequest_builder import build_insert_payload, build_update_payload
from classes.db_queries import query_Rota, update_viagem_repom1

router = APIRouter(prefix="/RouteRequest", tags=["RouteRequest"])

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def log_response(data: Any) -> None:
    AppLogger().add(
        "INFO",
        f"Resposta da API: {json.dumps(data, indent=2, ensure_ascii=False)}"
    )

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post("/RouteRequestAutomatic/")
def new_Route_Request(payload=None, row_id=None, num_transacao=None, num_mdfe=None):
    client = APIClient()
    if not payload:
        payload = query_Rota(row_id=row_id, num_transacao=num_transacao, num_mdfe=num_mdfe)
        print(json.dumps(payload, ensure_ascii=True, indent=4))

    raw = client.post(endpoint=f"{router.prefix}/RouteRequestAutomatic", json=payload)

    try:
        response = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=502, detail=f"Resposta inválida da API Repom: {raw}")

    # Verificar status antes de atualizar o banco
    status_code = response.get("Response", {}).get("StatusCode")
    if status_code != 200:
        errors = response.get("Errors", [])
        error_msg = errors[0].get("Message") if errors else "Erro desconhecido"
        raise HTTPException(status_code=status_code or 502, detail=f"Repom: {error_msg}")

    update_viagem_repom1(response)
    return response

@router.get("/{traceIdentifier}")
async def get_Route_Request(traceIdentifier):
    """
    A consulta da rota é utilizada para o cliente ter uma previsão de quanto será o valor do vale
    pedágio. A Repom oferece algumas opções de consultas, como a consulta por CEP, código
    IBGE, código interno do cliente, e todas estas opções, retornarão a mesma informação:
    Código do roteiro, percurso e valor do pedágio por eixos utilizados.
    """

    client = APIClient()
    data = client.get(endpoint=f"/RouteRequest/{traceIdentifier}")

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rota não encontrada",
        )

    # log_response(data)

    return json.dumps(data, indent=2, ensure_ascii=False)
