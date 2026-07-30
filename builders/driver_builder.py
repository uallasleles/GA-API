from typing import Any, Dict
from fastapi import HTTPException, status

# Importações locais
from classes.utils import load_Template, limpar_numero
from classes.db_queries import query_Motorista


def build_insert_payload(row_id: str):
    """Constrói o payload de motorista a partir do template base."""

    try:
        payload = query_Motorista(row_id)

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return payload

def build_update_payload(national_id: str) -> Dict[str, Any]:
    """Constrói o payload para atualizar um motorista existente."""
    payload = load_Template("templates/Driver/driverPut.json")
    driver = query_Motorista(national_id)

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motorista não encontrado",
    )

    try:
        payload.update({
            "DriverLicenseNumber": driver["DRIVERLICENSENUMBER"],
        })

        address = payload["Address"]
        address.update({
            "Street": driver["ADDRESS_STREET"],
            "Number": driver["ADDRESS_NUMBER"],
            "Complement": driver["ADDRESS_COMPLEMENT"],
            "Neighborhood": driver["ADDRESS_NEIGHBORHOOD"],
            "ZipCode": driver["ADDRESS_ZIPCODE"],
        })

        phone = payload["Phones"][0]
        phone.update({
            "AreaCode": driver["PHONES_0_AREACODE"],
            "Number": driver["PHONES_0_NUMBER"],
            "Preferential": driver["PHONES_0_PREFERENTIAL"],
            "TypeId": driver["PHONES_0_TYPEID"],
        })

        personal = payload["DriverPersonalInformation"]
        personal.update({
            "BirthDate": driver["DRIVERPERSONALINFORMATION_BIRTHDATE"],
            "Name": driver["DRIVERPERSONALINFORMATION_NAME"],
            "Gender": driver["DRIVERPERSONALINFORMATION_GENDER"],
        })

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return payload