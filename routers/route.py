from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
import json

# Importações locais
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger
from classes.db_queries import update_viagem_repom2


router = APIRouter(prefix="/Route", tags=["Route"])

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

@router.get("/ByTraceIdentifier/{traceIdentifier}/{vehicleAxles}") 
async def get_Route_By_TraceIdentifier(traceIdentifier, vehicleAxles): 
    """
    """
    client = APIClient() 
    endpoint_get=f"/Route/ByTraceIdentifier/{traceIdentifier}/{vehicleAxles}" 

    response = client.get(endpoint=endpoint_get) 

    if not response: 
        raise HTTPException( 
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao consultar rota por Identificador de Trajeto na API externa",
        ) 

    update_viagem_repom2(response) 

    # log_response(response) 
    return response


@router.get("/ByRouteCode/{traceCode}/{routeCode}/{vehicleAxles}")
async def get_Route_By_RouteCode(traceCode, routeCode, vehicleAxles):
    """
    """
    client = APIClient()
    endpoint_get=f"/Route/ByRouteCode/{traceCode}/{routeCode}/{vehicleAxles}"

    response = client.get(endpoint=endpoint_get)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao consultar rota por Código de Rota na API externa",
        )

    log_response(response)
    return response