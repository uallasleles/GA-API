from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
import json

# Importações locais
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger

router = APIRouter(prefix="/Operation", tags=["Operation"])

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

@router.get("/") 
async def get_Operation(): 
    """ """
    client = APIClient() 
    endpoint_get="/Operation" 

    response = client.get(endpoint=endpoint_get) 

    if not response: 
        raise HTTPException( 
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao consultar operações cadastradas na Repom",
        )

    # log_response(response) 
    return response