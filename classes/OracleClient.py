import oracledb
from classes import db_config
from dotenv import load_dotenv
import os
import re

load_dotenv()

# instant_client_dir = r"C:\Users\uallas.pereira\Oracle\lib\instantclient_19_29"
instant_client_dir = os.getenv("ORACLEDB_INSTANT_CLIENT_DIR")

class MyCursor(oracledb.Cursor):
    """Cursor personalizado com logging de operações."""
    
    def execute(self, statement, args=None):
        # Permite que args seja None
        if args is None:
            args = []
            
        # Extrai o nome da tabela da consulta SQL
        # table_name = self._extract_table_name(statement)
        # print(f"Target table: {table_name}")
        
        print("Arguments:")
        for arg_index, arg in enumerate(args):
            print(f"  Bind {arg_index + 1} has value {repr(arg)}")
        
        return super().execute(statement, args or [])

    def _extract_table_name(self, statement):
        """
        Extrai o nome da tabela de uma consulta SQL.
        Suporta SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, etc.
        """
        if not statement or not isinstance(statement, str):
            return "Unable to extract table name"
            
        # Limpa espaços em branco e converte para minúsculas para análise mais fácil
        sql = statement.strip()
        
        # Remove comentários
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Padrões para diferentes tipos de consultas
        patterns = [
            # SELECT FROM tabela (com possíveis subqueries)
            (r'select\s+(?:.*?\s+)?from\s+([\w\.]+(?:\s+as\s+\w+)?)', 'select'),
            # INSERT INTO tabela
            (r'insert\s+(?:.*?\s+)?into\s+([\w\.]+)', 'insert'),
            # UPDATE tabela
            (r'update\s+([\w\.]+)', 'update'),
            # DELETE FROM tabela
            (r'delete\s+(?:.*?\s+)?from\s+([\w\.]+)', 'delete'),
            # CREATE TABLE tabela
            (r'create\s+(?:.*?\s+)?table\s+([\w\.]+)', 'create table'),
            # DROP TABLE tabela
            (r'drop\s+(?:.*?\s+)?table\s+([\w\.]+)', 'drop table'),
            # TRUNCATE TABLE tabela
            (r'truncate\s+(?:.*?\s+)?table\s+([\w\.]+)', 'truncate'),
            # ALTER TABLE tabela
            (r'alter\s+(?:.*?\s+)?table\s+([\w\.]+)', 'alter table'),
        ]
        
        sql_lower = sql.lower()
        for pattern, query_type in patterns:
            match = re.search(pattern, sql_lower, re.DOTALL)
            if match:
                # Extrai apenas o nome da tabela (remove alias se houver)
                table_part = match.group(1).strip()
                # Remove qualquer coisa após a primeira palavra (para lidar com "tabela alias")
                table_name = re.split(r'\s+', table_part)[0]
                # Remove parênteses se houver (caso de funções ou subqueries)
                table_name = table_name.split('(')[0]
                return table_name
        
        return "Unable to extract table name"

    def fetchone(self):
        print("Fetchone()")
        return super().fetchone()
    
    def executemany(self, statement, args):
        """Override do executemany para logging."""
        table_name = self._extract_table_name(statement)
        print(f"Target table (executemany): {table_name}")
        print(f"Number of rows: {len(args)}")
        
        return super().executemany(statement, args)


class MyCursorWithEvents(MyCursor):
    """Cursor personalizado com suporte a eventos."""
    pass


class MyConnection(oracledb.Connection):
    """Conexão personalizada com logging."""
    
    def __init__(self, *args, **kwargs):
        # Se não foram fornecidos parâmetros, usa os padrões de db_config
        if not args and not kwargs:
            kwargs = {
                'user': db_config.username,
                'password': db_config.password,
                'dsn': db_config.dsn
            }
        
        print("-"*75)
        print("Connecting to database")
        super().__init__(*args, **kwargs)
    
    def cursor(self):
        return MyCursor(self)


class MyConnectionWithEvents(oracledb.Connection):
    """Conexão personalizada com eventos."""
    
    def __init__(self, *args, **kwargs):
        # Inicializa o cliente Oracle se necessário
        try:
            oracledb.init_oracle_client(lib_dir=instant_client_dir)
        except oracledb.ProgrammingError:
            # Já inicializado, continua normalmente
            pass
        
        # Se não foram fornecidos parâmetros, usa os padrões de db_config
        if not args and not kwargs:
            kwargs = {
                'user': db_config.username,
                'password': db_config.password,
                'dsn': db_config.dsn,
                'events': True
            }
        elif 'events' not in kwargs:
            kwargs['events'] = True
        
        print("-"*75)
        print("Connecting to database (with events)")
        super().__init__(*args, **kwargs)
    
    def cursor(self):
        return MyCursorWithEvents(self)


# Funções de fábrica para conveniência
def create_connection(with_events=False):
    """Cria uma conexão com ou sem eventos."""
    if with_events:
        return MyConnectionWithEvents()
    else:
        return MyConnection()

def create_connection_custom(user, password, dsn, with_events=False):
    """Cria uma conexão personalizada com parâmetros específicos."""
    kwargs = {
        'user': user,
        'password': password,
        'dsn': dsn
    }
    
    if with_events:
        kwargs['events'] = True
        return MyConnectionWithEvents(**kwargs)
    else:
        return MyConnection(**kwargs)


# Exemplo de uso:
if __name__ == "__main__":
    # Conexão padrão
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = :1", [1])
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    # Conexão com eventos
    conn_events = create_connection(with_events=True)
    cursor_events = conn_events.cursor()
    cursor_events.execute("INSERT INTO logs (mensagem) VALUES (:1)", ["Teste"])
    conn_events.commit()
    cursor_events.close()
    conn_events.close()



# Considerações importantes:

# Permissões: 
#   O usuário do banco de dados requer GRANT CHANGE NOTIFICATION TO user_name; privilégio.

# Configuração de rede: 
#   por padrão, o banco de dados Oracle precisa ser capaz de iniciar uma conexão com a 
#   máquina que executa o script Python para que as notificações funcionem.
#   Regras de firewall ou configurações específicas de endereço/porta IP podem ser 
#   necessárias, ou você pode usar conexões iniciadas pelo cliente 
#   com versões mais recentes do Oracle.

# Limpeza: 
#   As assinaturas podem persistir no banco de dados se o aplicativo travar.
#   É crucial excluir explicitamente o objeto de assinatura ou usar um tempo 
#   limite curto durante o desenvolvimento para evitar assinaturas órfãs.