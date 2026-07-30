from typing import Any, Dict
from fastapi import HTTPException, status

# Importações locais
from classes.utils import load_Template, limpar_numero
from routers.queries import query_Viagem_Motoristas


def build_insert_payload(drivers: Dict[str, Any]) -> Dict[str, Any]:
# def build_insert_payload(rowid: str) -> Dict[str, Any]:
    """Constrói o payload para uma nova Emissão de Contrato."""

    # payload = load_Template("templates/Shipping/shippings.json")
    payload = {}
    # print(f"=> RowID: {shippings["ROWID"]}")

    # drivers = query_Viagem_Motoristas(numTransacao=drivers["NUMTRANSACAO"])

    try:

        payload["Drivers"] = drivers
 
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return payload