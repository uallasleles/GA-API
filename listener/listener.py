import time
import oracledb

# from listener.oracle_utils import get_oracle_connection
from classes import OracleClient
from listener.tables import TABLES_TO_MONITOR
from shared.queue import celery_app

registered = True

def callback(message):
    global registered

    if not message.registered:
        print("A assinatura do Oracle foi encerrada.")
        registered = False
        return

    for table in message.tables:
        table_name = table.name.upper()
        print(f"\n=== Evento em {table_name} ===")

        for row in table.rows or []:
            payload = {
                "table": table_name,
                "operation": row.operation,
                "rowid": row.rowid
            }

            celery_app.send_task(
                "worker.tasks.route_event",
                args=[payload]
            )

        print("============================\n")

def main():
    # conn = get_oracle_connection(events=True)
    conn = OracleClient.MyConnection_With_Events()

    sub = conn.subscribe(
        callback=callback,
        timeout=3600,
        qos=oracledb.SUBSCR_QOS_ROWIDS,
        client_initiated=True,
    )

    # Registrar cada tabela
    for table_name in TABLES_TO_MONITOR:
        sub.registerquery(f"SELECT * FROM {table_name}")
        print(f"Tabela registrada para DCN → {table_name}")

    print("\nListener DCN iniciado.\n")

    while registered:
        time.sleep(5)

if __name__ == "__main__":
    main()