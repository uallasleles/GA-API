from typing import Any, Dict
from fastapi import HTTPException, status

# Importações locais
from classes.utils import load_Template, limpar_numero
from classes.db_queries import query_Prestador


def build_insert_payload(rowid: str):
    """Constrói o payload de criação do contratado."""

    try:
        payload = query_Prestador(rowid)
        # template.update({
        #     "Country": hired["COUNTRY"],
        #     "HiredType": hired["HIREDTYPE"],
        #     "NationalId": hired["NATIONALID"],
        #     "Email": hired["EMAIL"],
        #     "FuelVoucherPercentage": hired["FUELVOUCHERPERCENTAGE"],
        # })

        # phone = template["Phones"][0]
        # phone.update({
        #     "AreaCode": hired["PHONES_0_AREACODE"],
        #     "Number": limpar_numero(hired["PHONES_0_NUMBER"]),
        #     "Preferential": hired["PHONES_0_PREFERENTIAL"],
        #     "TypeId": hired["PHONES_0_TYPEID"],
        # })

        # brazil = template["BrazilianSettings"]
        # brazil["RNTRC"] = hired["BRAZILIANSETTINGS_RNTRC"].zfill(9)

        # brazil["HiredPessoaFisica"].update({
        #     "INSS": hired["BRAZILIANSETTINGS_HIREDPESSOAFISICA_INSS"],
        #     "RG": hired["BRAZILIANSETTINGS_HIREDPESSOAFISICA_RG"],
        # })

        # brazil["HiredPessoaJuridica"].update({
        #     "InscricaoEstadual": hired["BRAZILIANSETTINGS_HIREDPESSOAJURIDICA_INSCRICAOESTADUAL"],
        #     "InscricaoMunicipal": hired["BRAZILIANSETTINGS_HIREDPESSOAJURIDICA_INSCRICAOMUNICIPAL"],
        #     "NomeFantasia": hired["BRAZILIANSETTINGS_HIREDPESSOAJURIDICA_NOMEFANTASIA"],
        #     "OptanteSimplesNacional": hired["BRAZILIANSETTINGS_HIREDPESSOAJURIDICA_OPTANTESIMPLESNACIONAL"],
        # })

        # address = template["Address"]
        # address.update({
        #     "Street": hired["ADDRESS_STREET"],
        #     "Number": hired["ADDRESS_NUMBER"],
        #     "Complement": hired["ADDRESS_COMPLEMENT"],
        #     "Neighborhood": hired["ADDRESS_NEIGHBORHOOD"],
        #     "ZipCode": hired["ADDRESS_ZIPCODE"],
        # })

        # template["CompanyInformation"]["CompanyName"] = hired[
        #     "COMPANYINFORMATION_COMPANYNAME"
        # ]

        # personal = template["HiredPersonalInformation"]
        # personal.update({
        #     "Name": hired["HIREDPERSONALINFORMATION_NAME"],
        #     "BirthDate": hired["HIREDPERSONALINFORMATION_BIRTHDATE"],
        #     "LegalDependents": hired["HIREDPERSONALINFORMATION_LEGALDEPENDENTS"],
        #     "Gender": hired["HIREDPERSONALINFORMATION_GENDER"],
        # })

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return payload

def build_update_payload(national_id: str) -> Dict[str, Any]:
    """Constrói o payload de atualização do contratado."""
    template = load_Template("templates/Hired/hiredPut.json")
    hired = query_Prestador(national_id)

    if not hired:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prestador não encontrado",
        )

    try:
        phone = template["Phones"][0]
        phone.update({
            "AreaCode": hired["PHONES_0_AREACODE"],
            "Number": limpar_numero(hired["PHONES_0_NUMBER"]),
            "Preferential": hired["PHONES_0_PREFERENTIAL"],
            "TypeId": hired["PHONES_0_TYPEID"],
        })

        brazil = template["BrazilianSettings"]
        brazil["RNTRC"] = hired["BRAZILIANSETTINGS_RNTRC"].zfill(9)

        brazil["HiredPessoaFisica"].update({
            "INSS": hired["BRAZILIANSETTINGS_HIREDPESSOAFISICA_INSS"],
            "RG": hired["BRAZILIANSETTINGS_HIREDPESSOAFISICA_RG"],
        })

        brazil["HiredPessoaJuridica"].update({
            "InscricaoEstadual": hired["BRAZILIANSETTINGS_HIREDPESSOAJURIDICA_INSCRICAOESTADUAL"],
            "InscricaoMunicipal": hired["BRAZILIANSETTINGS_HIREDPESSOAJURIDICA_INSCRICAOMUNICIPAL"],
            "NomeFantasia": hired["BRAZILIANSETTINGS_HIREDPESSOAJURIDICA_NOMEFANTASIA"],
            "OptanteSimplesNacional": hired["BRAZILIANSETTINGS_HIREDPESSOAJURIDICA_OPTANTESIMPLESNACIONAL"],
        })

        address = template["Address"]
        address.update({
            "Street": hired["ADDRESS_STREET"],
            "Number": hired["ADDRESS_NUMBER"],
            "Complement": hired["ADDRESS_COMPLEMENT"],
            "Neighborhood": hired["ADDRESS_NEIGHBORHOOD"],
            "ZipCode": hired["ADDRESS_ZIPCODE"],
        })

        template["CompanyInformation"]["CompanyName"] = hired[
            "COMPANYINFORMATION_COMPANYNAME"
        ]

        personal = template["HiredPersonalInformation"]
        personal.update({
            "Name": hired["HIREDPERSONALINFORMATION_NAME"],
            "BirthDate": hired["HIREDPERSONALINFORMATION_BIRTHDATE"],
            "LegalDependents": hired["HIREDPERSONALINFORMATION_LEGALDEPENDENTS"],
            "Gender": hired["HIREDPERSONALINFORMATION_GENDER"],
        })

        template["Email"] = hired["EMAIL"]
        template["FuelVoucherPercentage"] = hired["FUELVOUCHERPERCENTAGE"]

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return template