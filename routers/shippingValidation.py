from fastapi import APIRouter
import logging
from classes.APIClient import APIClient
import requests
import json
from classes.utils import load_Template

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ShippingValidation/ByVehicles/{vehicles}")
async def get_Shipping_Validation_By_Vehicles(vehicles):
    """
    Validação    
    Esta consulta realiza a validação se o veículo apontado possui cadastro na REPOM e se o
    mesmo está com a documentação dentro do prazo de validade.
    """
    endpoint="/ShippingValidation/ByVehicles/{vehicles}"
    client = APIClient()
    
    try:
        data = client.get(endpoint=f"{endpoint}")
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)
    
@router.get("/ShippingValidation/ByVehiclesTag/{vehicles}")
async def get_Shipping_Validation_By_Vehicles_Tag(vehicles):
    """
    Validação    
    Esta consulta realiza a validação se o veículo apontado possui cadastro na REPOM e se o
    mesmo está com a documentação dentro do prazo de validade.
    """
    endpoint="/ShippingValidation/ByVehiclesTag/{vehicles}"
    client = APIClient()
    
    try:
        data = client.get(endpoint=f"{endpoint}")
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)

@router.get("/ShippingValidation/ByHiredDocument/{country}/{document}")
async def get_Shipping_Validation_By_Hired_Document(country, document):
    """
    Esta consulta valida se o prestador está válido na ANTT, 
    bem como a RNTRC como transportador, pode ser consultado por CPF ou CNPJ.
    """

    endpoint="/ShippingValidation/ByHiredDocument/{country}/{document}"
 
    client = APIClient()
    try:
        data = client.get(endpoint=f"{endpoint}")
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)

@router.get("/ShippingValidation/ByCardNumberHiredDocument/{cardnumber}/{country}/{document}")
async def get_Shipping_Validation_By_Card_Number_Hired_Document(cardnumber, country, document):
    """
    Esta consulta valida os dados do cartão do prestador/motorista, 
    bem como a situação antes da emissão
    """
    endpoint="/ShippingValidation/ByCardNumberHiredDocument/{cardnumber}/{country}/{document}"
    client = APIClient()
    
    try:
        data = client.get(endpoint=f"{endpoint}")
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)
