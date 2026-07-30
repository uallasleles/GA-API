import time
import os
from classes import SQLiteQueue
from classes import OracleClient
from listener.tables import TABLES_TO_MONITOR
# from listener.tables import QUERIES_TO_MONITOR
from data.filters import FILTERS_TO_NOTIFICATIONS
import logging
from classes.countdown import countdown
from dotenv import load_dotenv

load_dotenv()
DCN_SUBSCRIPTION_TIMEOUT = int(os.getenv("DCN_SUBSCRIPTION_TIMEOUT"))
DCN_SUBSCRIPTION_NAME = os.getenv("DCN_SUBSCRIPTION_NAME")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

registered = True # definindo um status inicial padrao para a subscricao
filtered = False  #

def callback(message):
    global registered
    q = SQLiteQueue.SQLiteQueue()

    print("Message type:", message.type)

    if not message.registered:
        print("Deregistration has taken place...")
        registered = False
        return
        
    print("Message database name:", message.dbname)
    print("Message transaction id:", message.txid)
    print("=" * 60)
    
    print("Message tables:")
    for table in message.tables:
        print("--> Table:", table.name)
        print("--> Operation:", table.operation)
        print("=" * 120)
        if table.rows is not None:
            for row in table.rows:
                print("--> --> Row RowId:", row.rowid)
                print("--> --> Row Operation:", row.operation)

                # exclui do enfileiramento registros especificos
                if filtered and table.name == 'CHOCOSUL.PCVEICUL':
                    if row.rowid in set(FILTERS_TO_NOTIFICATIONS):
                        q.enqueue(message.type, message.dbname, message.txid, table.name, table.operation, row.rowid, row.operation)
                    else:
                        logger.info("Notificacao descartada por filtragem de ROWID.")
                
                # enfileiramento normal
                else:
                    q.enqueue(message.type, message.dbname, message.txid, table.name, table.operation, row.rowid, row.operation)
            
                print("-" * 60)

# TODO: PROBLEMA DO MONITORAMENTO DE ALTERAÇÕES NO BANCO
def begin():

    # # 1. Verificar se a subscrição já existe na visão do banco de dados
    # query = f"""
    # SELECT regid FROM USER_CHANGE_NOTIFICATION_REGS
    # WHERE client_identifier = :client_id_val AND table_name = :table_name_val
    # """
    # # Use um identificador único (client_identifier) para sua aplicação/sessão
    # client_id = f"my_app_dcn_sub_{subscription_name}"
    
    # cursor.execute(query, client_id_val=client_id, table_name_val=table_name.upper())
    # existing_reg = cursor.fetchone()
    # cursor.close()

    try:
        connection = OracleClient.create_connection(with_events=True)

        options = {
            "name": DCN_SUBSCRIPTION_NAME,
            "callback": callback,
            "timeout": DCN_SUBSCRIPTION_TIMEOUT,
            "qos": OracleClient.oracledb.SUBSCR_QOS_ROWIDS,
            "operations": OracleClient.oracledb.OPCODE_INSERT | OracleClient.oracledb.OPCODE_UPDATE | OracleClient.oracledb.OPCODE_DELETE,
            "client_initiated": True
        }

        sub = connection.subscribe(**options)

        print("\n")
        print("=" * 75)
        print(f"Subscription: {sub}")
        print("-" * 75)
        print(f"--> Connection: {sub.connection}")
        print(f"--> ID: {sub.id}")
        print(f"--> Callback: {sub.callback}")
        print(f"--> Name: {sub.name}")
        print(f"--> Namespace: {sub.namespace}")
        print(f"--> Protocol: {sub.protocol}")
        print(f"--> Timeout: {sub.timeout}")
        print(f"--> Operations: {sub.operations}")
        print(f"--> Rowids?: {bool(sub.qos & OracleClient.oracledb.SUBSCR_QOS_ROWIDS)}")

        print("-" * 75)
        for table_name in TABLES_TO_MONITOR:
            sub.registerquery(f"SELECT * FROM {table_name}")
            print(f"Tabela registrada para DCN → {table_name}")
        # for statement in QUERIES_TO_MONITOR:
        #     sub.registerquery(f"{statement}")
        #     print(f"{statement}")

        print("\n")
        print("=" * 75)
        logger.info("Listener DCN iniciado.")
        logger.info("Waiting for notifications...")
        print("-" * 75)

        # input("Hit enter to stop CQN demo\n\n")

        # countdown(sub.timeout)
        while registered:
            # logger.info("Waiting for notifications...")
            time.sleep(1)
            
    except OracleClient.oracledb.Error as e:
        print(f"Database error: {e}")
    finally:
        # Exclua explicitamente a assinatura para evitar que ela permaneça registrada indefinidamente
        if 'sub' in locals() and sub:
            del sub
        if 'connection' in locals() and connection:
            connection.close()

#if __name__ == "__main__":
#    begin()