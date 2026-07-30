from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status
import json

# Importações locais
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger
from classes.utils import limpar_numero
from classes.db_queries import query_Motorista

router = APIRouter(prefix="/Driver", tags=["Driver"])

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

@router.get("/ByDocument/")
async def get_driver_by_document(nationalId: str, country: int = 55):
    """Consulta um motorista pelo documento."""
    client = APIClient()
    endpoint = f"{router.prefix}/ByDocument/{country}/{nationalId}"

    result = client.get(endpoint=endpoint)
    
    return result

@router.get("/ByName/{name}")
async def get_driver_by_name(name: str):
    """Consulta um motorista pelo nome."""
    client = APIClient()
    data = client.get(endpoint=f"{router.prefix}/ByName/{name}")

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motorista não encontrado",
        )

    log_response(data)
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data

@router.post("/")
async def create_driver(row_id = None, national_id: str = None, enrollment = None):
    """
    Cria um novo motorista na API externa.
    """
    national_id = limpar_numero(national_id)
    payload = query_Motorista(row_id, national_id, enrollment)
    
    client = APIClient()
    endpoint = f"{router.prefix}"

    response = client.post(endpoint=endpoint, json=payload)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao criar motorista na API externa",
        )

    #log_response(response)
    
    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return response

@router.post("/sync")
async def sync_driver(row_id = None, national_id: str = None, enrollment = None, country: int = 55):
    """
    Sincroniza um Motorista - cria se não existir, atualiza se existir.
    """
    client = APIClient()
    
    national_id = limpar_numero(national_id)
    
    payload = query_Motorista(row_id, national_id, enrollment)

    endpoint_get  = f"{router.prefix}/ByDocument/{country}/{national_id}"
    endpoint_post = f"{router.prefix}"
    endpoint_put  = f"{router.prefix}/{country}/{national_id}"
    
    record_data=payload
    
    try:
        existing_get = client.get(endpoint=endpoint_get)
        method = "PUT" if existing_get else "POST"
    except HTTPException as e:
        if e.status_code == 404:
            method = "POST"
        else:
            raise
    
    # 2. Executa a operação apropriada
    if method == "POST":
        payload = record_data
        response = client.post(endpoint=endpoint_post, json=payload)
    else:
        payload = record_data
        response = client.put(endpoint=endpoint_put, json=payload)
    
    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return response