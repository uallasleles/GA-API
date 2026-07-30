from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
import json

# Importações locais
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger
from classes.db_queries import query_Execute, update_Execute, load_query
# from auth import get_current_active_user


router = APIRouter(prefix="/Hired", tags=["Hired"])

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

@router.get("/ByName/{name}")
async def get_hired_by_name(name: str):
    """Consulta um contratado pelo nome."""
    client = APIClient()
    data = client.get(endpoint=f"/Hired/ByName/{name}")

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratado não encontrado",
        )

    log_response(data)
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data

@router.get("/ByDocument/{country}/{nationalid}")
async def get_hired_by_document(nationalid: str, country: int = 55):
    """Consulta um contratado pelo documento."""
    client = APIClient()
    data = client.get(endpoint=f"{router.prefix}/ByDocument/{country}/{nationalid}")

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratado não encontrado",
        )

    log_response(data)
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data

@router.post("/")
async def create_hired(
    row_id: str = None, 
    national_id = None, 
    hired_id = None
    ):
    """Cria um novo contratado na API externa."""

    sql = "queries/prestador_json.sql"
    bind_variables = {
        "row_id": row_id, 
        "national_id": national_id, 
        "hired_id": hired_id
    }

    query = load_query(sql)
    hired = query_Execute(query, bind_variables)

    client = APIClient()
    response = client.post(endpoint=f"{router.prefix}", json=hired)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao criar contratado na API externa",
        )

    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return response

@router.put("/put/")
async def update_hired(
    hired: Dict[str, Any], 
    row_id: str = None, 
    national_id = None, 
    hired_id = None, 
    country: str = "55"
    ):
    """Atualiza dados de um contratado já cadastrado."""

    if hired.get("NATIONALID") is None:
        sql_path = "queries/prestador_json_update.sql"
        bind_variables = {
            "row_id": row_id, 
            "national_id": national_id, 
            "hired_id": hired_id
        }
        query = load_query(sql_path)
        hired = query_Execute(query, bind_variables)
        print(hired)

    payload = hired
    endpoint = f"{router.prefix}/{country}/{national_id}"
    print(endpoint)

    client = APIClient()
    response = client.put(endpoint=endpoint, json=payload)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao atualizar contratado na API externa",
        )

    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return response

@router.post("/sync/")
async def sync_hired(
    national_id = None, 
    hired_id = None, 
    hired: Dict[str, Any] = None, 
    row_id = None, 
    country: str = "55"
    ):
    """Sincroniza um contratado - cria se não existir, atualiza se existir."""

    client = APIClient()
    # Parâmetros
    if row_id:
        sql_path = "queries/prestador_json.sql"
        query = load_query(sql_path) 
        bind_variables = { 
            "row_id": row_id, 
            "national_id": national_id, 
            "hired_id": hired_id 
        } 
        hired = query_Execute(query, bind_variables) 
        national_id = hired["NationalId"]

    endpoint_get=f"/Hired/ByDocument/{country}/{national_id}"
    endpoint_post="/Hired"
    endpoint_put=f"/Hired/{country}/{national_id}"
    
    #existing_get = client.get(endpoint=endpoint_get)
    #method = "PUT" if existing_get else "POST"
    
    # 1. Verifica se o contratado já existe
    try:
        # Tenta buscar o contratado pelo NationalId ou outro identificador único
        #   existing_hired = client.get(endpoint=f"/Hired/ByNationalId/{national_id}")
        # Ou conforme sua API oferecer endpoints de consulta
        existing_get = client.get(endpoint=endpoint_get)
        
        method = "PUT" if existing_get else "POST"
        
    except HTTPException as e:
        if e.status_code == 404:
            method = "POST"
        else:
            raise

    if hired.get("Email") is None:
        sql_path = "queries/prestador_json.sql" if method == "POST" else "queries/prestador_json_update.sql" 
        query = load_query(sql_path) 
        bind_variables = { 
            "row_id": row_id, 
            "national_id": national_id, 
            "hired_id": hired_id 
        } 
        hired = query_Execute(query, bind_variables) 
        print(hired) 
    
    # 2. Executa a operação apropriada
    if method == "POST":
        # payload = build_insert_payload(record_data)
        response = client.post(endpoint=endpoint_post, json=hired)
    else:
        # payload = build_update_payload(record_id)
        response = client.put(endpoint=endpoint_put, json=hired)
    
    log_response(response)
    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return response