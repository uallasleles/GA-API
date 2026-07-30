from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status, Query, Body
import json
from classes.APIClient import APIClient
from classes.Logger import Logger as AppLogger
import requests
from classes.db_queries import update_Execute, load_query, query_Viagem

router = APIRouter(prefix="/Shipping", tags=["Shipping"])

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

# GET =======================================================================

@router.get("/ByCIOT/{ciot}")
async def get_Shipping_By_CIOT(ciot):
    """
    Este método retorna informações de envio da busca por seu CIOT.
    """
    
    endpoint=f"{router.prefix}/ByCIOT/{ciot}"
    
    client = APIClient()
    try:
        data = client.get(endpoint=endpoint)
        # AppLogger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        # AppLogger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)

@router.get("/DocumentCheckLists")
async def get_Shipping_Document_Check_Lists():
    """
    Este método retorna remessas com status específico no período determinado.
    """
    
    endpoint=f"{router.prefix}/DocumentCheckLists"
    
    client = APIClient()
    try:
        data = client.get(endpoint=endpoint)
        AppLogger.info(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return(data)
    except requests.exceptions.RequestException as e:
        AppLogger.error(f"Ocorreu um erro na requisição: {e}")
        return(data)

@router.get("/ByShipping/{shippingId}")
async def get_Shipping_By_Shipping(shippingId: str):

    endpoint=f"{router.prefix}/ByShipping/{shippingId}"

    client = APIClient()
    data = client.get(endpoint=endpoint)

    # if data["Response"]["StatusCode"] == 200:
    #     num_transacao = data["Result"]["Identifier"]
    #     print(num_transacao)
    #     await update_CIOT(num_transacao)
        
    return(data)

@router.get("/ByIdentifier/{identifier}")
def get_Shipping_By_Identifier(identifier):
    
    endpoint=f"{router.prefix}/ByIdentifier/{identifier}"
    
    client = APIClient()
    data = client.get(endpoint=endpoint)

    try:
        response = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        response = data

    return response

# TODO: 05) get /Shipping/DownloadShippingFile/{shippingID}
# GetFile

# TODO: 06) get /Shipping/ShippingConfirmation/{shippingId}
# Retrieves a shipping confirmation.

# TODO: 07) get /Shipping/FuelConsume/ByShipping/{shippingId}
# Get shippings with fuel consume by Shipping Id

# TODO: 08) get /Shipping/StatusProcessing/ByIdentifier/{identifier}
# Retrieves a list of shippings by client code

# TODO: 09) get /Shipping/ByStatus/{dataInicial}/{dataFinal}/{status}
# Retrieves a shipping by status.
# /ByStatus/:dataInicial/:dataFinal/: status

@router.get("/ByStatus/{dataInicial}/{dataFinal}/{status}")
async def get_ByStatus_Status(dataInicial, dataFinal, status: str):

    endpoint=f"{router.prefix}/ByStatus/{dataInicial}/{dataFinal}/{status}"
    
    client = APIClient()
    data = client.get(endpoint=endpoint)

    return(data)

# TODO: 10) get /Shipping/StatusProcessing/ByOperationKey/{operationKey}
# Retrieves a status processing by operationKey

@router.get("/StatusProcessing/ByOperationKey/{operationKey}")
async def get_StatusProcessing_ByOperationKey(operationKey: str):
    """
    Recupera um processamento de status por chave de operação.
    """
    
    endpoint=f"{router.prefix}/StatusProcessing/ByOperationKey/{operationKey}"
    
    client = APIClient()
    data = client.get(endpoint=endpoint)

    try:
        response = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        response = data
    
    return response


# TODO: 11) get /Shipping/ByTaxRecalculation/Pending/{initialDate}/{finalDate}
# Get shippings with fuel consume between dates

@router.get("/ByStatus/{dataInicial}/{dataFinal}")
async def get_Shipping_By_Status(dataInicial, dataFinal):
    """
    Este método retorna remessas com vários status no período determinado.
    """    
    endpoint=f"{router.prefix}/ByStatus/{dataInicial}/{dataFinal}"
    
    client = APIClient()
    data = client.get(endpoint=endpoint)

    return(data)


# POST ======================================================================

PAYLOAD_EXAMPLE = [{"additionalProp1": {}}]

@router.post("/")
async def new_Shipping(
    num_transacao: str = Query(default=None), 
    nummdfe: str = Query(default=None),
    row_id: str = Query(default=None),
    payload: List[Dict[str, Any]] = Body(default=None), 
    ):

    if not payload or payload == PAYLOAD_EXAMPLE:
        payload = query_Viagem(num_transacao, nummdfe, row_id)

        # Garante que o retorno é uma lista de dicts válida
        if not payload or not isinstance(payload, list) or not isinstance(payload[0], dict):
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum registro encontrado para num_transacao={num_transacao}"
            )

        num_transacao = payload[0].get("Identifier")

        vehicles = payload[0].get("Vehicles")

        # Verifique se vehicles não é None antes de montar o payload
        if not vehicles or len(vehicles) == 0: 
            raise ValueError("A lista de veículos não pode ser vazia ou nula.")

        print(json.dumps(payload))

    print(f"payload: {payload}")
    print(f"Recebida requisição Shipping - num_transacao={num_transacao}")

    client = APIClient()
    r = client.post(endpoint=f"{router.prefix}", json=payload)

    try:
        response = json.loads(r)
    except (json.JSONDecodeError, TypeError):
        response = r 
    
    print(response)

    # Depois (seguro)
    if response is None:
        raise HTTPException(status_code=502, detail="Sem resposta da API Repom.")

    status_code = response.get("Response", {}).get("StatusCode")

    if status_code == 201:
        operation_key = response["Response"]["Message"].split(": ")[1]

        if operation_key:
            query = load_query("queries/update_MDFe_OperationKey.sql")
            bind_variables = {"num_transacao": num_transacao, "operation_key": operation_key}
            result_query = update_Execute(query, bind_variables)
            print(result_query)

            await update_CIOT(num_transacao)

    elif status_code == 404:
        raise HTTPException(status_code=404, detail=f"Shipping não encontrado na Repom: {num_transacao}")

    else:
        error_msg = (
            response.get("Response", {}).get("Message")
            or response.get("ExceptionMessage")
            or "Erro desconhecido"
        )
        raise HTTPException(status_code=502, detail=f"Erro na API Repom: {error_msg}")

    return response


# TODO: 14) post /Shipping/CIOTAggregate/CancelCIOT
# Cancel Operation Transport. 
@router.post("/CIOTAggregate/CancelCIOT")
async def Cancel_CIOT(ciot):
    payload = {
        "TransportOperationIdentifierCode": ciot,
        "Reason": "string"
    }
    client = APIClient()
    result = client.post(endpoint=f"{router.prefix}/Shipping/CIOTAggregate/CancelCIOT", json=payload)

    return result

# TODO: 15) post /Shipping/CIOTAggregate/ClosingCIOT
# Closing Operation Transport.


# PATCH =====================================================================

# TODO: 16) patch /Shipping/AddTaxes
# Creates tax movements on the shipping by Shipping ID

# TODO: 17) patch /Shipping/Cancel/{id}
# Cancel shipping

# TODO: 18) patch /Shipping/Interruption/{id}
# Interruption Shipping

# TODO: 19) patch /Shipping/alterSubcontractor

# TODO: 20) patch /Shipping/AddTaxesByIdentifier
# Creates tax movements on the shipping by Identifier

# TODO: 21) patch /Shipping/lockUnlock/{shippingId}
# Lock or unlock a shipping

# TODO: 22) patch /Shipping/AddDocument/{shippingId}
# Add Shipping document

# TODO: 23) patch /Shipping/AddMovement/{shippingId}
# Add Shipping movement

# TODO: 24) patch /Shipping/CIOTAggregate/ShippingRectification
# Shipping Rectification.

# TODO: 25) patch /Shipping/AdvanceFreightBalanceByIdentifier/{identifier}
# Add Advance Freight Balance By identifier

# TODO: 26) patch /Shipping/AdvanceFreightBalanceByShippingId/{shippingId}
# Add Advance Freight Balance

@router.get("/obter_CIOT")
def obter_CIOT(num_transacao=None):
    # 39739
    # get_StatusProcessing_ByOperationKey(operationKey='')
    shipping = get_Shipping_By_Identifier(num_transacao) 
    num_ciot = shipping["Result"]["CIOT"] 

    return num_ciot 

@router.get("/atualizar_CIOT") 
async def update_CIOT(num_transacao: str):
    shipping = get_Shipping_By_Identifier(num_transacao)
    print(shipping)

    status_code = shipping.get("Response", {}).get("StatusCode")

    if status_code != 200:
        error_msg = shipping.get("Response", {}).get("Message", "Erro desconhecido")
        raise HTTPException(
            status_code=502,
            detail=f"update_CIOT: Shipping não encontrado na Repom ({status_code}) - {error_msg}"
        )

    result = shipping.get("Result", {})
    shipping_id = result.get("ShippingId", 0)

    if shipping_id > 0:
        cpf_cnpj = result.get("HiredNationalId")
        num_ciot = result.get("CIOT")
        print(f"update_CIOT - num_transacao: {num_transacao}; cpf_cnpj: {cpf_cnpj}; num_ciot: {num_ciot}.")

        bind_variables = {"num_transacao": num_transacao, "cpf_cnpj": cpf_cnpj, "num_ciot": num_ciot}
        query = load_query("queries/update_MDFe_CIOT.sql")
        result_update = update_Execute(query=query, bind_variables=bind_variables)
        print(f"update_CIOT - result_update: {result_update}")
        return result_update

    return None