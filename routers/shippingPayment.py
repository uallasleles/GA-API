

from fastapi import APIRouter
import logging
from classes.APIClient import APIClient
import requests
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

# TODO: get /ShippingPayment/DownloadPaymentFile/{shippingID}
# Reshipping document

# TODO: post /ShippingPayment
# Shipping payment

# TODO: patch /ShippingPayment/Cancel/{shippingID}
# Shipping payment cancel

# TODO: patch /ShippingPayment/DocumentLost/{shippingID}
# Lost document

# TODO: patch /ShippingPayment/DocumentReship/{shippingID}
# Reshipping document

# TODO: patch /ShippingPayment/DocumentDelivered/{shippingID}
# Delivered document

# TODO: patch /ShippingPayment/DocumentDismissed/{shippingID}
# Dismisses document