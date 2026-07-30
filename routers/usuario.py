from fastapi import APIRouter
import logging
from classes.APIClient import APIClient
import requests
import json
from classes.utils import load_Template
from classes.utils import limpar_numero_telefone
from classes.db_queries import query_Prestador

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/Hired/ByName/{name}")
async def get_Hired(name):
    """
    Docstring para get_Hired
    
    :param name: Descrição
    """
    
    endpoint="/Hired/ByName"
    
    # TODO: encapsular este bloco
    client = APIClient()
    try:
        data = client.get(endpoint=f"{endpoint}/{name}")
        # logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        # logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)
    
@router.post("/Hired/{usuario}")
async def new_Hired(usuario):
    endpoint="/User"

    payload = usuario
    
    client = APIClient() 
    response = client.post(endpoint=endpoint, json=payload)
    if response:
        logger.info(f"✅ Resposta da API: {response}") 