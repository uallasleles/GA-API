from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
import json

# Importações locais
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger
from builders.movement_builder import build_insert_payload, build_update_payload

router = APIRouter(prefix="/Movement", tags=["Movement"])

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

@router.get("/GetMovement")
async def get_Movement():
    """
    Consulta de movimentos

    Nesta chamada é necessário informar apenas a versão do sistema.
    """
    endpoint="/Movement/GetMovement"
    client = APIClient()
    
    data = client.get(endpoint=f"{endpoint}")
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimento não encontrado",
        )

    log_response(data)
    return data

@router.post("/MovementRegistration")
async def send_Movement(movement: Dict[str, Any]):
    """
    Envio de Movimentos
    
    Através desta chamada é possível incluir débitos e créditos após a emissão do contrato. 
    O status deste contrato precisa estar: Em trânsito ou pendente.

    O movimento desejado será cadastrado, no portal do cliente, pelo usuário administrador.
    Não há limites de cadastros, ou seja, o cliente poderá incluir quantos movimentos desejar.

    OBS: Este método adiciona um movimento de acréscimo ou decréscimo na viagem.
    """
    client = APIClient() 
    payload = build_insert_payload(movement)
    endpoint = "/Movement/MovementRegistration"

    response = client.post(endpoint=endpoint, json_body=payload)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao criar movimento na API externa",
        )

    log_response(response)
    return response

@router.post("/sync")
async def sync_vehicle(moviment: Dict[str, Any]):
    """
    Sincroniza um vehicle - cria se não existir, atualiza se existir.
    """
    client = APIClient()
    
    # Parâmetros
    license=moviment["LICENSEPLATE"]

    endpoint_get="/Movement/GetMovement"
    endpoint_post="/Movement/MovementRegistration"
    endpoint_put="/Movement/MovementRegistration"
    
    record_data=moviment
    record_id=license
    
    # 1. Verifica se o movimento já existe
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
        payload = build_insert_payload(record_data)
        response = client.post(endpoint=endpoint_post, json_body=payload)
    else:
        payload = build_update_payload(record_id)
        response = client.put(endpoint=endpoint_put, json_body=payload)
    
    log_response(response)
    return response