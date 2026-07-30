import time
from classes import SQLiteQueue
from classes import OracleClient
from listener.tables import TABLES_TO_MONITOR
from data.filters import FILTERS_TO_NOTIFICATIONS
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

registered = True

def callback(message):
    global registered
    q = SQLiteQueue.SQLiteQueue()

    for query in message.queries:
        print(query)
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
            print("--> Table Name:", table.name)
            print("--> Table Operation:", table.operation)
            print("=" * 60)
            if table.rows is not None:
                for row in table.rows:
                    print("--> --> Row RowId:", row.rowid)
                    print("--> --> Row Operation:", row.operation)

                    if table.name == 'CHOCOSUL.PCVEICUL':
                        if row.rowid in set(FILTERS_TO_NOTIFICATIONS):
                            q.enqueue(message.type, message.dbname, message.txid, table.name, table.operation, row.rowid, row.operation)
                        else:
                            logger.info("Notificacao descartada por filtragem de ROWID.")
                    else:
                        q.enqueue(message.type, message.dbname, message.txid, table.name, table.operation, row.rowid, row.operation)
                
                    print("-" * 60)


# TODO: PROBLEMA DO MONITORAMENTO DE ALTERAÇÕES NO BANCO
def begin():
    try:
        connection = OracleClient.create_connection(with_events=True)

        sub = connection.subscribe(
            callback=callback,
            timeout=60,
            qos=OracleClient.oracledb.SUBSCR_QOS_ROWIDS, 
            client_initiated=True
        )
        # oracledb.SUBSCR_QOS_ROWIDS
        # Esta constante é usada para especificar que os rowids das linhas inseridas, 
        # atualizadas ou excluídas devem ser incluídos nos objetos de mensagem enviados.

        # oracledb.SUBSCR_QOS_QUERY | 

        logger.info(f"\n\nSubscription: {sub}")
        logger.info(f"--> Connection: {sub.connection}")
        logger.info(f"--> ID: {sub.id}")
        logger.info(f"--> Callback: {sub.callback}")
        logger.info(f"--> Namespace: {sub.namespace}")
        logger.info(f"--> Protocol: {sub.protocol}")
        logger.info(f"--> Timeout: {sub.timeout}")
        logger.info(f"--> Operations: {sub.operations}")
        logger.info(f"--> Rowids?: {bool(sub.qos & OracleClient.oracledb.SUBSCR_QOS_ROWIDS)}")

        for table_name in TABLES_TO_MONITOR:
            sub.registerquery(f"SELECT * FROM {table_name}")
            logger.info(f"Tabela registrada para DCN → {table_name}")

        logger.info("Listener DCN iniciado.\n")

        # input("Hit enter to stop CQN demo\n\n")
        
        while registered:
            logger.info("Waiting for notifications...")
            time.sleep(1)
            
    except OracleClient.oracledb.Error as e:
        print(f"Database error: {e}")
    finally:
        # Exclua explicitamente a assinatura para evitar que ela permaneça registrada indefinidamente
        if 'sub' in locals() and sub:
            del sub
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    begin()