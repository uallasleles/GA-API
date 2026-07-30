from typing import Any, Dict
from fastapi import HTTPException, status

# Importações locais
from classes.utils import load_Template, limpar_numero
from classes.db_queries import query_Veiculo


def build_insert_payload(row_id: str):
    """Constrói o payload para inserir um novo veículo."""
    # template = load_Template("templates/Vehicle/vehicle.json")

    # print(f"teste: {rowid}")

    try:
        payload = query_Veiculo(row_id)

        # template.update({
        #     "Country": vehicle["COUNTRY"],
        #     "LicensePlate": vehicle["LICENSEPLATE"],
        #     "VehicleClassification": vehicle["VEHICLECLASSIFICATION"],
        #     "VehicleCategory": vehicle["VEHICLECATEGORY"],
        #     "VehicleAxles": vehicle["VEHICLEAXLES"],
        #     "Type": vehicle["TYPE"],
        # })

        # owner = template["VehicleOwner"]
        # owner.update({
        #     "Country": vehicle["VEHICLEOWNER_COUNTRY"],
        #     "NationalId": limpar_numero(vehicle["VEHICLEOWNER_NATIONALID"]),
        #     "Type": vehicle["VEHICLEOWNER_TYPE"],
        # })

        # owner["BrazilianSettings"]["RNTRC"] = vehicle[
        #     "VEHICLEOWNER_BRAZILIANSETTINGS_RNTRC"
        # ].zfill(9)

        # owner["BrazilianSettings"]["VehiclePessoaJuridica"][
        #     "NomeFantasia"
        # ] = vehicle[
        #     "VEHICLEOWNER_BRAZILIANSETTINGS_VEHICLEPESSOAJURIDICA_NOMEFANTASIA"
        # ]

        # owner["VehiclePersonalInformation"]["Name"] = vehicle[
        #     "VEHICLEOWNER_VEHICLEPERSONALINFORMATION_NAME"
        # ]

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return payload

def build_update_payload(license: str) -> Dict[str, Any]:
    """Constrói o payload para atualizar um veículo existente."""
    template = load_Template("templates/Vehicle/vehiclePut.json")
    vehicle = query_Veiculo(license)

    try:
        template.update({
            "VehicleClassification": vehicle["VEHICLECLASSIFICATION"],
            "VehicleCategory": vehicle["VEHICLECATEGORY"],
            "VehicleAxles": vehicle["VEHICLEAXLES"],
            "Type": vehicle["TYPE"],
        })

        owner = template["VehicleOwner"]
        owner.update({
            "Country": vehicle["VEHICLEOWNER_COUNTRY"],
            "NationalId": limpar_numero(vehicle["VEHICLEOWNER_NATIONALID"]),
            "Type": vehicle["VEHICLEOWNER_TYPE"],
        })

        owner["BrazilianSettings"]["RNTRC"] = vehicle[
            "VEHICLEOWNER_BRAZILIANSETTINGS_RNTRC"
        ].zfill(9)

        owner["BrazilianSettings"]["VehiclePessoaJuridica"][
            "NomeFantasia"
        ] = vehicle[
            "VEHICLEOWNER_BRAZILIANSETTINGS_VEHICLEPESSOAJURIDICA_NOMEFANTASIA"
        ]

        owner["VehiclePersonalInformation"]["Name"] = vehicle[
            "VEHICLEOWNER_VEHICLEPERSONALINFORMATION_NAME"
        ]

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return template