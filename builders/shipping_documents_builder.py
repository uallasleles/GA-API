from typing import Any, Dict
from fastapi import HTTPException, status

# Importações locais
from classes.utils import load_Template, limpar_numero
from routers.queries import query_Viagem_Documentos


def build_insert_payload(documents: Dict[str, Any]) -> Dict[str, Any]:
# def build_insert_payload(rowid: str) -> Dict[str, Any]:
    """Constrói o payload para uma nova Emissão de Contrato."""

    # payload = load_Template("templates/Shipping/shippings.json")
    payload = {}
    # print(f"=> RowID: {shippings["ROWID"]}")

    # documents = query_Viagem_Documentos(rowid)
    # print(documents)

    try:
        # 16. Documento Fiscal
        payload.update(
            {"Documents": documents}
        )

        # for i, doc in enumerate(documents):
        #     payload[i]["Documents"][0]["BranchCode"] = doc["BRANCHCODE"]
        #     # Tipo de Documento: [1-CTE | 2-NFe | 3-NFSe | 4-CRT | 5-OCC | 6-Romaneio | 14-MDFe]
        #     payload[i]["Documents"][0]["DocumentType"] = doc["DOCUMENTTYPE"]
        #     payload[i]["Documents"][0]["Series"] = doc["SERIES"]
        #     payload[i]["Documents"][0]["Number"] = doc["NUMBER"]
        #     payload[i]["Documents"][0]["EletronicKey"] = doc["ELETRONICKEY"]
        #     payload[i]["Documents"][0]["CheckDocument"] = doc["CHECKDOCUMENT"]
            
        #     payload[i]["Documents"][0]["DocumentCheckLists"][0]["Id"] = doc["DOCUMENTCHECKLISTS_ID"]
        #     payload[i]["Documents"][0]["DocumentCheckLists"][0]["PaymentBlock"] = doc["DOCUMENTCHECKLISTS_PAYMENTBLOCK"]
            
        #     payload[i]["Documents"][0]["DeliveryLocationType"] = doc["DELIVERYLOCATIONTYPE"]
 
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return payload