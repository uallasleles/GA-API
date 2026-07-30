# -----------------------------------------------------------------------------
# aq_notification.py
# 
# Demonstra o uso da notificação de fila avançada. Assim que este script 
# estiver em execução, execute object_aq.py em outro terminal para enfileirar 
# algumas mensagens na fila "DEMO_BOOK_QUEUE".
# -----------------------------------------------------------------------------

import time

import oracledb
import sample_env

# este script é atualmente suportado apenas no modo grosso python-oracledb
oracledb.init_oracle_client(lib_dir=sample_env.get_oracle_client())

registered = True


def process_messages(message):
    global registered
    print("Message type:", message.type)
    if message.type == oracledb.EVENT_DEREG:
        print("Deregistration has taken place...")
        registered = False
        return
    print("Queue name:", message.queue_name)
    print("Consumer name:", message.consumer_name)
    print("Message id:", message.msgid)


connection = oracledb.connect(
    user=sample_env.get_main_user(),
    password=sample_env.get_main_password(),
    dsn=sample_env.get_connect_string(),
    events=True,
)

sub = connection.subscribe(
    namespace=oracledb.SUBSCR_NAMESPACE_AQ,
    name="DEMO_BOOK_QUEUE",
    callback=process_messages,
    timeout=300,
)
print("Subscription:", sub)
print("--> Connection:", sub.connection)
print("--> Callback:", sub.callback)
print("--> Namespace:", sub.namespace)
print("--> Protocol:", sub.protocol)
print("--> Timeout:", sub.timeout)

while registered:
    print("Waiting for notifications....")
    time.sleep(5)
