import sqlite3
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQLiteQueue:
    def __init__(self, queue_db_path='data/queue.db', queue_table_name='tasks'):
        self.queue_db_path = queue_db_path
        self.queue_table_name = queue_table_name
        self.queue_conn = sqlite3.connect(queue_db_path, isolation_level=None) # isolation_level=None para autocommit
        self.queue_cursor = self.queue_conn.cursor()
        self._create_table()

    def _create_table(self):

        self.queue_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.queue_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_type INT NOT NULL,
                message_dbname TEXT NOT NULL,
                message_txid BLOB NOT NULL,
                table_name TEXT NOT NULL,
                table_operation INT NOT NULL,
                row_rowid BLOB NOT NULL,
                row_operation INT NOT NULL,
                timestamp REAL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.queue_conn.commit()

    def enqueue(self, message_type, message_dbname, message_txid, table_name, table_operation, row_rowid, row_operation):

        logger.info(f"Inserindo registro na fila: table_name: {table_name}, row_rowid: {row_rowid}, row_operation: {row_operation}.")
        try:
            self.queue_cursor.execute(f"INSERT INTO {self.queue_table_name} (message_type, message_dbname, message_txid, table_name, table_operation, row_rowid, row_operation) VALUES (?, ?, ?, ?, ?, ?, ?)", (message_type, message_dbname, message_txid, table_name, table_operation, row_rowid, row_operation))
            return True
        except sqlite3.Error as e:
            logger.info(f"Erro ao inserir item na fila: {e}")
            return False

    def dequeue(self):
        # Remove e retorna o item mais antigo (primeiro a entrar) da fila (FIFO)
        try:
            # Seleciona o item mais antigo (menor ID)
            keys = ('id', 'message_type', 'message_dbname', 'message_txid', 'table_name', 'table_operation', 'row_rowid', 'row_operation', 'timestamp')
            columns = ', '.join(keys)

            qry = f"SELECT {columns} FROM {self.queue_table_name} ORDER BY id ASC LIMIT 1"
            
            self.queue_cursor.execute(qry)
            values = self.queue_cursor.fetchone()

            if values:
                record = dict(zip(keys, values))
                # id, message_type, message_dbname, message_txid, table_name, table_operation, row_rowid, row_operation, timestamp = record
                # Remove o item selecionado da tabela
                self.queue_cursor.execute(f"DELETE FROM {self.queue_table_name} WHERE id = ?", (record["id"],))
                logger.info("Notificação removida da fila.")
                return(record)
            else:
                return None # Fila vazia

        except sqlite3.Error as e:
            logger.exception(f"Erro ao remover item da fila: {e}")
            return None

    def size(self):
        # Retorna o número atual de itens na fila
        self.queue_cursor.execute(f"SELECT COUNT(*) FROM {self.queue_table_name}")
        try:
            count = self.queue_cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.exception(f"Não há itens na fila: {e}")
        finally:
            pass

    def remove(self, id):
        # Deleta o registro da fila
        try:
            self.queue_cursor.execute(f"DELETE FROM {self.queue_table_name} WHERE id = ?", (id,))
            return True
        except sqlite3.Error as e:
            logger.info(f"Erro ao deletar item na fila: {e}")
            return False
        finally:
            pass

    def close(self):
        # Fecha a conexão com o banco de dados
        self.queue_conn.close()

if __name__ == "__main__":
    q = SQLiteQueue()

    # Adicionando itens à fila
    q.enqueue("primeira_tarefa")
    q.enqueue("segunda_tarefa")
    q.enqueue("terceira_tarefa")
    print(f"Tamanho da fila após adicionar 3 itens: {q.size()}")

    # Removendo itens da fila (deve seguir a ordem FIFO)
    item1 = q.dequeue()
    print(f"Processando item: {item1}")

    item2 = q.dequeue()
    print(f"Processando item: {item2}")
    
    q.enqueue("quarta_tarefa") # Adiciona outro item

    item3 = q.dequeue()
    print(f"Processando item: {item3}")
    
    print(f"Tamanho da fila restante: {q.size()}")

    q.close()