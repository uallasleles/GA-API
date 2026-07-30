from typing import Any, Dict, Annotated
from fastapi import APIRouter, Body
from pydantic import BaseModel
import logging
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger
import requests
import json

router = APIRouter(prefix="/Card", tags=["Card"])

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

class Active_Cards_By_Hired(BaseModel):
    CardNumber: int
    CardType: str
    HiredNationalID: str
    HiredName: str
    DriverNationalID: str
    DriverName: str
    Status: str

@router.get("/GetActiveCardsByHired/{HiredNationalID}")
async def get_Active_Cards_By_Hired(
    HiredNationalID: str,
    Cards: Annotated[
        Active_Cards_By_Hired, 
        Body(
            examples=[
                {
                    "CardNumber": 0,
                    "CardType": "string",
                    "HiredNationalID": "string",
                    "HiredName": "string",
                    "DriverNationalID": "string",
                    "DriverName": "string",
                    "Status": "Active"
                }
            ]
        )],
    ) -> list[Active_Cards_By_Hired]:
    """
    Este método retorna todos os cartões ativos dos contratados.

    HiredNationalID: CPF/CNPJ do Contratado
    """
    endpoint = f"{router.prefix}/GetActiveCardsByHired/{HiredNationalID}"

    client = APIClient()
    try:
        data = client.get(endpoint=endpoint)
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)

@router.get("/GetActiveCardsByDriver/{DriverNationalID}")
async def get_Active_Cards_By_Driver(DriverNationalID):
    """
    Este método retorna todos os cartões ativos do motorista.

    DriverNationalID: CPF Motorista
    """
    endpoint = f"{router.prefix}/GetActiveCardsByDriver/{DriverNationalID}"

    client = APIClient()
    try:
        data = client.get(endpoint=endpoint)
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)

@router.get("/GetActiveCardsByHiredAndByDriver/{HiredNationalID}/{DriverNationalID}")
async def get_Active_Cards_By_Hired_And_By_Driver(HiredNationalID, DriverNationalID):
    """
    Este método retorna todos os cartões ativos que o contratado e o motorista possuem em comum.

    HiredNationalID: CNPJ do Contratado
    DriverNationalID: CPF do Motorista
    """
    endpoint = f"/Card/GetActiveCardsByHiredAndByDriver/{HiredNationalID}/{DriverNationalID}"

    client = APIClient()
    try:
        data = client.get(endpoint=endpoint)
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)