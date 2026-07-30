from classes.APIClient import APIClient
import os
import json
import logging
from dotenv import load_dotenv
import requests
from classes import OracleClient

# from typing import Union
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import asyncio

from routers import shipping
from routers import routeRequest
from routers import card
from routers import hired
from routers import shippingFuelBenefit
from routers import vehicle
from routers import movement
from routers import driver
from routers import shippingValidation
from routers import queries

from classes.SQLiteQueue import SQLiteQueue

from classes import dcn
import threading

load_dotenv() 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(title="LázaroLog")

# Endpoints Repom
app.include_router(card.router, prefix="/Repom", tags=["Card"])
app.include_router(hired.router, prefix="/Repom", tags=["Hired"])
app.include_router(vehicle.router, prefix="/Repom", tags=["Vehicle"])
app.include_router(driver.router, prefix="/Repom", tags=["Driver"])
app.include_router(routeRequest.router, prefix="/Repom", tags=["RouteRequest"])
app.include_router(shipping.router, prefix="/Repom", tags=["Shipping"])
app.include_router(shippingFuelBenefit.router, prefix="/Repom", tags=["ShippingFuelBenefit"])
app.include_router(shippingValidation.router, prefix="/Repom", tags=["ShippingValidation"])
app.include_router(movement.router, prefix="/Repom", tags=["Movement"])

# Querys WinThor
app.include_router(queries.router, prefix="/WinThor", tags=["Querys"])

@app.get("/dequeue")
async def teste_dequeue():

    # busca um registro na fila de notificações
    q = SQLiteQueue()
    record = q.dequeue()

    # consulta o registro no banco de dados
    payload = queries.query_Usuario(
        record['row_rowid'], 
        record['table_name']
    )

    # envia os dados para a API
    await driver.new_Driver(payload)

    return(q.size())


task1 = threading.Thread(target=dcn.begin(), daemon=True)


task1.start()

if __name__ == "__main__": 
    pass