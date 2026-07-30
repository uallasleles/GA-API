import dataclasses
from dataclasses import field


@dataclasses.dataclass
class VehiclePersonalInformation:
    VehiclePersonalInformation_Name: str

@dataclasses.dataclass
class VehiclePessoaJuridica:
    NomeFantasia: str

@dataclasses.dataclass
class BrazilianSettings(VehiclePessoaJuridica):
    Rntrc: str

@dataclasses.dataclass
class VehicleOwner(BrazilianSettings, VehiclePersonalInformation):
    VehicleOwner_Country: str
    VehicleOwner_NationalId: str
    VehicleOwner_Type: str

@dataclasses.dataclass
class Vehicle(VehicleOwner):
    Vehicle_Country: str
    Vehicle_LicensePlate: str
    VehicleClassification: str
    VehicleCategory: str
    VehicleAxles: str
    Vehicle_Type: str