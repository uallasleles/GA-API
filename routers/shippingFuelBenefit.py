from fastapi import APIRouter
import logging
from classes.APIClient import APIClient
import requests
import json
from classes.utils import load_Template
from classes.db_queries import query_VinculoCartao

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ShippingFuelBenefit", tags=["ShippingFuelBenefit"])

@router.get("/GetLinkByCardNumber/{cardNumber}")
async def get_Link_By_Card_Number(cardNumber):
    """
    Recupera vínculo FuelBenefits por número de cartão.
    cardNumber: Número do Cartão

    DriverBondResult: \n
        NationalId (string, optional)       : Documento de identificação única do motorista. (CNPJ/CPF quando no Brasil ), \n
        HiredNationalId (string, optional)  : CNPJ ou CPF do prestador, \n
        HiredName (string, optional)        : Nome do prestador, \n
        DriverName (string, optional)       : Nome do motorista, \n
        RegisterDate (string, optional)     : Data vínculo, \n
        UpdateDate (string, optional)       : Data ultima utilização, \n
        Errors (Array[Error], optional)     : Lista de Erros \n

    """
    endpoint = f"{router.prefix}/GetLinkByCardNumber/{cardNumber}"

    client = APIClient()
    try:
        data = client.get(endpoint=endpoint)
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)

# TODO: get /ShippingFuelBenefit/GetByHiredDriverNationalId/{HiredNationalID}/{DriverNationalID}
# Recupera vínculo FuelBenefits por {{HiredNationalID}, {DriverNationalID}}

@router.get("/ShippingFuelBenefit/GetByHiredDriverNationalId/{HiredNationalID}/{DriverNationalID}")
async def get_By_Hired_Driver_NationalId(HiredNationalID, DriverNationalID):
    """
    Recupera vínculo FuelBenefits por {{HiredNationalID}, {DriverNationalID}}

    HiredNationalID: CNPJ do Contratado
    DriverNationalID: CPF do Motorista
    """
    endpoint = f"/ShippingFuelBenefit/GetByHiredDriverNationalId/{HiredNationalID}/{DriverNationalID}"

    client = APIClient()
    try:
        data = client.get(endpoint=endpoint)
        logger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)

# TODO: patch /ShippingFuelBenefit/JoinHiredDriverCard
# Cria vínculo FuelBenefits 'cartão/motorista/contratado'

@router.patch("/JoinHiredDriverCard")
async def join_Hired_Driver_Card(payload = None, driverNationalId = None, enrollment = None):
    """
    Cria vínculo FuelBenefits 'cartão/motorista/contratado'. 
    
    ShippingFuelBenefitPatch: \n
        CardNumber (string, optional)       : Número do Cartão, \n
        HiredNationalID (string, optional)  : CNPJ do Contratado, \n
        DriverNationalId (string, optional) : CPF do Motorista
    
    """
    if not payload:
        payload = query_VinculoCartao(payload, driverNationalId, enrollment)

    endpoint = f"{router.prefix}/JoinHiredDriverCard"

    client = APIClient()
    result = client.patch(endpoint=endpoint, json=payload)

    return(result)