# -----------------------------------------------------------------------------

import oracledb
import platform
import os
import getpass

######################################################################

#
# Oracle Client library configuration
# Configuração da biblioteca do cliente Oracle
#

# No Linux, deve ser None.
# Em vez disso, o ambiente Oracle deve ser definido antes do início do Python.
instant_client_dir = None

# No Windows, se o seu banco de dados estiver na mesma máquina, comente essas 
# linhas e deixe instant_client_dir como None.  Caso contrário, defina-o para 
# o diretório do Instant Client.  Observe o uso da string bruta r"..." para 
# que barras invertidas possam ser usadas como separadores de diretório.
if platform.system() == "Windows":
    instant_client_dir = r"C:\Users\uallas.pereira\OneDrive\Code\RepomFrete\lib\Oracle\instantclient_23_0"

# No macOS, defina o diretório para o diretório do Instant Client
if platform.system() == "Darwin":
    instant_client_dir = (
        os.environ.get("HOME") + "/Downloads/instantclient_23_3"
    )

# Você deve sempre chamar init_oracle_client() para usar o modo grosso em qualquer plataforma
oracledb.init_oracle_client(lib_dir=instant_client_dir)

######################################################################

#
# Tutorial credentials and connection string.
# Environment variable values are used, if they are defined.
#

user = os.environ.get("PYTHON_USER", "pythondemo")

dsn = os.environ.get("PYTHON_CONNECT_STRING", "localhost/freepdb1")

pw = os.environ.get("PYTHON_PASSWORD")
if pw is None:
    pw = getpass.getpass("Enter password for %s: " % user)
