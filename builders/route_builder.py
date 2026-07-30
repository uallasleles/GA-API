from typing import Any, Dict
from fastapi import HTTPException, status

# Importações locais
from classes.utils import load_Template
from classes.db_queries import query_Rota


def build_insert_payload(nummdfe: str):
# def build_insert_payload(route: Dict[str, Any]) -> Dict[str, Any]:
    """Constrói o payload para consultar uma nova rota."""
    # payload = load_Template("templates/route/route.json")

    try:
        rota = query_Rota(nummdfe)
        # payload.update({
        #     "OriginPostalCode": route["ORIGINPOSTALCODE"],
        #     "DestinyPostalCode": route["DESTINYPOSTALCODE"],
        #     "BranchCode": route["BRANCHCODE"],
        #     "RoundTrip": route["ROUNDTRIP"],
        #     "TraceIdentifier": route["TRACEIDENTIFIER"],
        # })

        # del payload["OriginLongitude"]
        # del payload["OriginLatitude"]
        # del payload["DestinyLongitude"]
        # del payload["DestinyLatitude"]
        # del payload["OriginIBGECode"]
        # del payload["DestinyIBGECode"]

        # routestop_postalcode = route["ROUTESTOP_POSTALCODE"].rsplit(', ')
        # dict_list = [{"PostalCode": cep} for cep in routestop_postalcode]
        # payload.update({"RouteStop": dict_list})
        # print(payload)

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return rota

def build_update_payload(TraceIdentifier: str) -> Dict[str, Any]:
    """Constrói o payload para atualizar um veículo existente."""
    payload = load_Template("templates/routeAutomatic/routeAutomatic.json")
    route = query_Rota(TraceIdentifier)

    try:

        payload["OriginPostalCode"] = route["ORIGINPOSTALCODE"]
        # payload["OriginLongitude"] = route["ORIGINLONGITUDE"]
        # payload["OriginLatitude"] = route["ORIGINLATITUDE"]
        payload["DestinyPostalCode"] = route["DESTINYPOSTALCODE"]
        # payload["DestinyLongitude"] = route["DESTINYLONGITUDE"]
        # payload["DestinyLatitude"] = route["DESTINYLATITUDE"]

        routestop_postalcode = route["ROUTESTOP_POSTALCODE"].rsplit(', ')

        for i in range(0, routestop_postalcode):
            payload["RouteStop"][i]["PostalCode"] = routestop_postalcode[i]
            # payload["RouteStop"][0]["IBGECode"] = route["ROUTESTOP_POSTALCODE"]
            # payload["RouteStop"][0]["Latitude"] = route["ROUTESTOP_POSTALCODE"]
            # payload["RouteStop"][0]["Longitude"] = route["ROUTESTOP_POSTALCODE"]

        payload["BranchCode"] = route["BRANCHCODE"]
        # payload["OriginIBGECode"] = route["ORIGINIBGECODE"]
        # payload["DestinyIBGECode"] = route["DESTINYIBGECODE"]
        payload["RoundTrip"] = route["ROUNDTRIP"]
        payload["TraceIdentifier"] = route["TRACEIDENTIFIER"]

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return payload