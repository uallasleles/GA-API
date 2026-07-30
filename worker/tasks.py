import requests
from celery import Celery

from worker.config import API_URL
from worker.oracle_utils import fetch_row

app = Celery("tasks")
app.config_from_object("worker.config")


@app.task(bind=True, max_retries=5)
def sync_row(self, payload):
    try:
        print(f"Processando: {payload}")

        rowid = payload["rowid"]
        data = fetch_row(rowid)

        if data is None:
            print("Registro não encontrado (possível DELETE).")
            data = {
                "rowid": rowid,
                "operation": payload["operation"],
                "deleted": True
            }

        resp = requests.post(API_URL, json=data)
        resp.raise_for_status()

        print("Enviado com sucesso:", data)

    except Exception as exc:
        print("Erro no envio, retry...")
        raise self.retry(exc=exc, countdown=10)
