from typing import Any, Dict, List
from fastapi import HTTPException, status

# Importações locais
# from classes.utils import load_Template
from classes.db_queries import (
    query_Viagem
)


def build_insert_payload(row_id):
    """Constrói o payload para uma nova Emissão de Contrato."""
    # template = load_Template("templates/Shipping/shippings.json")

    # viagem_documentos = query_Viagem_Documentos(viagem["ROWID"])
    # viagem_motoristas = query_Viagem_Motoristas(viagem["NUMTRANSACAO"])
    # viagem_veiculos = query_Viagem_Veiculos(viagem["NUMTRANSACAO"])

    try:
        viagem = query_Viagem(row_id)
    #     # Atualiza o primeiro elemento do template (assumindo array com um elemento)
    #     template[0].update({
    #         # 1. Código único de registro para o Contrato / Viagem
    #         "Identifier": viagem["IDENTIFIER"],
    #         "Country": viagem["COUNTRY"],
            
    #         # 2. Contratado
    #         "HiredCountry": viagem["COUNTRY"],
    #         "HiredNationalId": viagem["HIREDNATIONALID"],
    #         "OperationIdentifier": viagem["OPERATIONIDENTIFIER"],
            
    #         # 3. Cartão Frete e Cartão Vale-Pedágio
    #         "CardNumber": viagem["CARDNUMBER"],
    #         "VPRCardNumber": viagem["VPRCARDNUMBER"],

    #         # 4. TraceCode e RouteCode
    #         "BrazilianRouteTraceCode": viagem["BRAZILIANROUTETRACECODE"],
    #         "BrazilianRouteRouteCode": viagem["BRAZILIANROUTEROUTECODE"],
            
    #         # 5. Data de emissão
    #         "IssueDate": viagem["ISSUEDATE"],
            
    #         # 6. Valores do frete
    #         "TotalFreightValue": viagem["TOTALFREIGHTVALUE"],
    #         "TotalLoadWeight": viagem["TOTALLOADWEIGHT"],
    #         "TotalLoadValue": viagem["TOTALLOADVALUE"],
            
    #         # Adiantamento e filial
    #         "AdvanceMoneyValue": viagem["ADVANCEMONEYVALUE"],
    #         "BranchCode": viagem["BRANCHCODE"],
            
    #         # 7. NCM da mercadoria
    #         "LoadBrazilianNCM": viagem["LOADBRAZILIANNCM"],
            
    #         # 8. Código ANTT
    #         "LoadBrazilianANTTCodeType": viagem["LOADBRAZILIANANTTCODETYPE"],
            
    #         # 9. Códigos IBGE
    #         "BrazilianIBGECodeSource": viagem["BRAZILIANIBGECODESOURCE"],
    #         "BrazilianIBGECodeDestination": viagem["BRAZILIANIBGECODEDESTINATION"],
            
    #         # 10. CEPs origem/destino
    #         "BrazilianCEPSource": viagem["BRAZILIANCEPSOURCE"],
    #         "BrazilianCEPDestination": viagem["BRAZILIANCEPDESTINATION"],
            
    #         # 11. Distância percorrida
    #         "TravelledDistance": viagem["TRAVELLEDDISTANCE"],

    #         # 12. Motoristas
    #         "Drivers": viagem_motoristas.get("Drivers", []),
            
    #         # 13. Documentos Fiscais
    #         "Documents": viagem_documentos.get("Documents", []),
            
    #         # 14. Veículos
    #         "Vehicles": viagem_veiculos.get("Vehicles", []),

    #         # 15. Tipo de processamento do frete
    #         "ProcessingShippingType": viagem["PROCESSINGSHIPPINGTYPE"],

    #         # 16. Tipo de terceirização
    #         "Outsourcing": viagem["OUTSOURCING"],

    #         # Indicadores de Quebra
    #         "BillingBreak": viagem["BILLINGBREAK"],
    #         "ToleranceBreak": viagem["TOLERANCEBREAK"],
    #         "FreightBreak": viagem["FREIGHTBREAK"],

    #         # CIOT TAC – AGREGADO
    #         "CIOTShippingType": viagem["CIOTSHIPPINGTYPE"],
    #         "ExistingContractId": viagem["EXISTINGCONTRACTID"],
            
    #         # Cliente de transporte
    #         "TransportationCustomer": viagem["TRANSPORTATIONCUSTOMER"],

    #         # Tipo de documento
    #         "DigitalDocument": viagem["DIGITALDOCUMENT"],
    #         "PhysicalDocument": viagem["PHYSICALDOCUMENT"],

    #         # Observações
    #         "GeneralObservation": viagem["GENERALOBSERVATION"],

    #         # Subcontratação
    #         "SubcontractorID": viagem["SUBCONTRACTORID"],
    #         "SubcontractorAdvancePercentage": viagem["SUBCONTRACTORADVANCEPERCENTAGE"],
    #         "SubcontractorFinalBalancePercentage": viagem["SUBCONTRACTORFINALBALANCEPERCENTAGE"],

    #         # Custo Mínimo de Frete
    #         "MinimumFreightCost": {
    #             "DistanceTravel": viagem["MINIMUMFREIGHTCOST_DISTANCE_TRAVEL"],
    #             "EmptyReturn": viagem["MINIMUMFREIGHTCOST_EMPTYRETURN"],
    #             "HighPerformanceTransport": viagem["MINIMUMFREIGHTCOST_HIGHPERFORMANCETRANSPORT"],
    #         },
    #     })

    #     # Campos opcionais (mantidos como None se não existirem)
    #     optional_fields = [
    #         "AccountingAdjustments",
    #         "ShippingReceiver", 
    #         "Taxes",
    #         "ShippingFuel",
    #     ]
        
    #     for field in optional_fields:
    #         if field not in template[0]:
    #             template[0][field] = None

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo obrigatório ausente: {exc}",
        )

    return viagem