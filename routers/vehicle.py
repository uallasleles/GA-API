from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
import json

# Importações locais
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger
from builders.vehicle_builder import build_insert_payload, build_update_payload
from classes.db_queries import query_Execute, queryAll_Execute, load_query, _prepare_bind, row_to_jsonable

router = APIRouter(prefix="/Vehicle", tags=["Vehicle"])

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

@router.get("/ByDocument/{license}")
async def get_vehicle(license: str, country: int = 55):
    """
    Consulta um veículo pelo documento (placa).  
    Exemplos:  
        - Placa: JMA5093  
        - RowID: AAAXU8AARAAAAlMAAB  
    """
    endpoint = f"/Vehicle/ByDocument/{country}/{license}"
    client = APIClient()

    data = client.get(endpoint=endpoint)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Veículo não encontrado",
        )

    log_response(data)
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data

@router.post("/")
async def create_vehicle(row_id = None, license_plate = None, vehicle_id = None):
    """Cria um novo veículo na API externa."""
    
    client = APIClient()

    # consulta
    query = load_query("queries/veiculo_json.sql")
    bind_variables = {"row_id": row_id, "license_plate": license_plate, "vehicle_id": vehicle_id}
    payload = query_Execute(query, bind_variables)

    response = client.post(endpoint="/Vehicle", json=payload)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao criar veículo na API externa",
        )

    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return response

@router.post("/sync/")
async def sync_vehicle(
    # vehicle: Dict[str, Any], 
    row_id = None, 
    license_plate = None, 
    vehicle_id = None):
    """
    Sincroniza um vehicle - cria se não existir, atualiza se existir.
    """
    country = 55

    # consulta
    # if not vehicle:
    query = load_query("queries/veiculo_json.sql")
    bind_variables = {"row_id": row_id, "license_plate": license_plate, "vehicle_id": vehicle_id}
    payload = query_Execute(query, bind_variables)
    # print(payload)

    # payload = vehicle

    if not license_plate: 
        license_plate = payload["LicensePlate"]
    
    client = APIClient()
    endpoint_get=f"/Vehicle/ByDocument/{country}/{license_plate}"
    endpoint_post="/Vehicle"
    endpoint_put=f"/Vehicle/{country}/{license_plate}"

    # 1. Verifica se o veículo já existe
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
        # payload = build_insert_payload(record_data)
        print(method)
        response = client.post(endpoint=endpoint_post, json=payload)
        print(response)
    else:
        # payload = build_update_payload(record_id)
        print(method)
        response = client.put(endpoint=endpoint_put, json=payload)
        print(response)
    
    log_response(response)

    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return response