from typing import Any, Dict, List
from fastapi import HTTPException, status

# Importações locais
from classes.utils import load_Template
from classes.db_queries import query_Rota


# def build_insert_payload(route_request: Dict[str, Any]) -> Dict[str, Any]:
def build_insert_payload(id: str):
    """Constrói o payload para inserir uma nova rota."""
    # template = load_Template("templates/RouteRequestAutomatic/RouteRequestAutomatic.json")

    try:
        rota = query_Rota(id)
        # template.update({
        #     "OriginPostalCode": route_request["ORIGINPOSTALCODE"],
        #     "DestinyPostalCode": route_request["DESTINYPOSTALCODE"],
        #     "BranchCode": route_request["BRANCHCODE"],
        #     "RoundTrip": route_request["ROUNDTRIP"],
        #     "TraceIdentifier": route_request["TRACEIDENTIFIER"],
        # })

        # # Remove campos não utilizados
        # template.pop("OriginLongitude", None)
        # template.pop("OriginLatitude", None)
        # template.pop("DestinyLongitude", None)
        # template.pop("DestinyLatitude", None)
        # template.pop("OriginIBGECode", None)
        # template.pop("DestinyIBGECode", None)

        # # Processa paradas de rota
        # route_stop_postalcode = route_request["ROUTESTOP_POSTALCODE"].rsplit(', ')
        # route_stop_list = [{"PostalCode": cep} for cep in route_stop_postalcode]
        # template["RouteStop"] = route_stop_list

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return rota


def build_update_payload(trace_identifier: str) -> Dict[str, Any]:
    """Constrói o payload para atualizar uma rota existente."""
    template = load_Template("templates/RouteRequestAutomatic/RouteRequestAutomatic.json")
    route = query_Rota(trace_identifier)

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rota não encontrada",
        )

    try:
        template.update({
            "OriginPostalCode": route["ORIGINPOSTALCODE"],
            "DestinyPostalCode": route["DESTINYPOSTALCODE"],
            "BranchCode": route["BRANCHCODE"],
            "RoundTrip": route["ROUNDTRIP"],
            "TraceIdentifier": route["TRACEIDENTIFIER"],
        })

        # Remove campos não utilizados (mesmo padrão do insert)
        template.pop("OriginLongitude", None)
        template.pop("OriginLatitude", None)
        template.pop("DestinyLongitude", None)
        template.pop("DestinyLatitude", None)
        template.pop("OriginIBGECode", None)
        template.pop("DestinyIBGECode", None)

        # Processa paradas de rota
        route_stop_postalcode = route["ROUTESTOP_POSTALCODE"].rsplit(', ')
        
        # Garante que RouteStop existe no template ou cria lista vazia
        if "RouteStop" not in template or not isinstance(template["RouteStop"], list):
            template["RouteStop"] = []
        
        # Atualiza ou adiciona paradas
        for i, postal_code in enumerate(route_stop_postalcode):
            if i < len(template["RouteStop"]):
                # Atualiza parada existente
                template["RouteStop"][i]["PostalCode"] = postal_code
            else:
                # Adiciona nova parada
                template["RouteStop"].append({"PostalCode": postal_code})

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return template