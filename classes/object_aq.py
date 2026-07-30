# -----------------------------------------------------------------------------
# object_aq.py
#
# Demonstra como usar o enfileiramento avançado com objetos. 
# Ele faz uso de um tipo simples e de uma fila 
# criada na configuração da amostra.
# -----------------------------------------------------------------------------

import decimal

import oracledb
import sample_env

# determinar se deve usar o modo fino ou o modo grosso do python-oracledb
if sample_env.run_in_thick_mode():
    oracledb.init_oracle_client(lib_dir=sample_env.get_oracle_client())

BOOK_TYPE_NAME = "UDT_BOOK"
QUEUE_NAME = "DEMO_BOOK_QUEUE"
BOOK_DATA = [
    (
        "The Fellowship of the Ring",
        "Tolkien, J.R.R.",
        decimal.Decimal("10.99"),
    ),
    (
        "Harry Potter and the Philosopher's Stone",
        "Rowling, J.K.",
        decimal.Decimal("7.99"),
    ),
]

# connect to database
connection = oracledb.connect(
    user=sample_env.get_main_user(),
    password=sample_env.get_main_password(),
    dsn=sample_env.get_connect_string(),
)

# create a queue
books_type = connection.gettype(BOOK_TYPE_NAME)
queue = connection.queue(QUEUE_NAME, payload_type=books_type)
queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG

# dequeue all existing messages to ensure the queue is empty, just so that
# the results are consistent
while queue.deqone():
    pass

# enqueue a few messages
print("Enqueuing messages...")
for title, authors, price in BOOK_DATA:
    book = books_type.newobject()
    book.TITLE = title
    book.AUTHORS = authors
    book.PRICE = price
    print(title)
    queue.enqone(connection.msgproperties(payload=book))
connection.commit()

# dequeue the messages
print("\nDequeuing messages...")
while True:
    props = queue.deqone()
    if not props:
        break
    print(props.payload.TITLE)
connection.commit()
print("\nDone.")
