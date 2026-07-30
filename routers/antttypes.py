from typing import Any, Annotated, Dict
from fastapi import APIRouter, Depends, HTTPException, status
import json
import logging

# Importações locais
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger
from auth.Auth import get_current_active_user


router = APIRouter(prefix="/ANTTTypes", tags=["ANTTTypes"])

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def log_response(data: Any) -> None:
    AppLogger().add(
        "INFO",
        f"Resposta da API: {json.dumps(data, indent=2, ensure_ascii=False)}"
    )

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/LoadTypes") 
async def get_ANTTTypes(
    response: Annotated[dict, Depends(get_current_active_user)]
): 
    """
    """
    client = APIClient() 
    endpoint_get=f"{router.prefix}/LoadTypes" 

    response = client.get(endpoint=endpoint_get) 

    # if not response: 
    #     raise HTTPException( 
    #         status_code=status.HTTP_502_BAD_GATEWAY,
    #         detail="Falha ao consultar os tipo de cargas permitidos pela ANTT.",
    #     )

    # log_response(response) 
    return response