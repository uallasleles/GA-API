import os
from classes import OracleClient
from classes.db_queries import query_Execute, queryAll_Execute, load_query, _prepare_bind, row_to_jsonable
import pandas as pd
import datetime
from classes.Logger import Logger
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String, DateTime, Float
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
import time
from classes.Logger import Logger
import urllib

# MySQL Connection Params
user="mastt901_admincontroll"
password=urllib.parse.quote("!control2025@")
host="192.185.213.192"
port="3306"
#database="mastt901_integracao_controll"
database="mastt901_controllbaseeunapolis"
#database="mastt901_controllbaseitabuna"

tabela = "PCCARREG"
table_id = f"{database}.{tabela}"

# Use URL encoding para caracteres especiais se necessário
connection_string = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
engine = create_engine(connection_string)
# Cria uma sessão de escopo
session_factory = sessionmaker(bind=engine)
session = scoped_session(session_factory)

# Get current Year
currentYear = datetime.datetime.now().strftime("%Y")
pastYear = (datetime.datetime.now() - datetime.timedelta(days=366)).strftime("%Y")
print("Variables initialized")

print("----------------------------------------------")

#Initialize start time
start_time = time.time()

#Initialize the timestamp id
UPD_TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
print("UPD_TIMESTAMP : " + UPD_TIMESTAMP)

# Get the data
queryOracle = """
SELECT DISTINCT
  c.NUMCAR
  ,t2.ORIGEM
  ,c.DESTINO
  ,CASE 
    WHEN (COUNT(m.DTINICIOOS) >= 1 AND COUNT(m.DTFIMOS) < COUNT(1)) AND COUNT(1) > 0 
    THEN 'S' 
    ELSE 'N' 
  END AS EM_SEPARACAO
  ,CASE 
    WHEN (COUNT(m.DTFIMSEPARACAO) = COUNT(1) OR COUNT(m.DTFIMOS) = COUNT(1)) AND COUNT(1) > 0 
    THEN 'S' 
    ELSE 'N' 
  END AS SEPARADO
  ,CASE 
    WHEN (COUNT(m.DTINICIOCONFERENCIA) >= 1 AND COUNT(m.DTFIMOS) < COUNT(1)) AND COUNT(1) > 0 
    THEN 'S' 
    ELSE 'N' 
  END AS EM_CONFERENCIA
  ,CASE 
    WHEN (COUNT(m.DTFIMCONFERENCIA) = COUNT(1)OR COUNT(m.DTFIMOS) = COUNT(1)) AND COUNT(1) > 0 
    THEN 'S' 
    ELSE 'N' 
  END AS CONFERIDO
  ,c.DTSAIDA
  ,c.DATAMON
  ,c.HORAMON
  ,c.MINUTOMON
  ,c.DTFECHA
  ,c.CODMOTORISTA
  ,e1.NOME AS MOTORISTA
  ,c.CODVEICULO
  ,c.TOTPESO
  ,c.TOTVOLUME
  ,c.VLTOTAL
  ,c.CODROTAPRINC
  ,r.CODROTA
  ,r.DESCRICAO AS ROTA
  ,c.NUMNOTAS
  ,c.QTITENS
  ,c.OBSFATUR
  ,c.TIPOCARGA
  ,c.OBSDESTINO
  ,c.CARGASECUNDARIA
  ,r.SITUACAO
  ,r.KMROTA
  ,r.VLMINCARREG
  ,r.PRAZOPREVENT
  ,r.TIPOCOMISSAO
  ,r.VLDIARIA
  ,r.NUMDIARIA
  ,r.RASTREADA
  ,r.DIASENTREGA
  ,COALESCE(MAX(m.NUMPALETE), 0) AS QT_PALETES
  ,COUNT(DISTINCT p.CODCLI) AS QT_ENTREGAS
  ,LISTAGG(DISTINCT m.TIPOOS, ', ') AS TIPOOS_LIST
FROM CHOCOSUL.PCCARREG c
  INNER JOIN CHOCOSUL.PCROTAEXP r   ON r.CODROTA = c.CODROTAPRINC
  INNER JOIN CHOCOSUL.PCPEDC p    ON p.NUMCAR = c.NUMCAR
  LEFT JOIN CHOCOSUL.PCEMPR e1    ON c.CODMOTORISTA = e1.MATRICULA
  LEFT JOIN CHOCOSUL.PCMOVENDPEND m   ON c.NUMCAR = m.NUMCAR
  LEFT JOIN CHOCOSUL.PCTIPOOS o     ON m.TIPOOS = o.CODIGO
  INNER JOIN (
    SELECT DISTINCT
      c.NUMCAR
      ,CASE 
        WHEN p.CODFILIAL IN (1, 2)    THEN 'EUNÁPOLIS' 
        WHEN p.CODFILIAL IN (12, 13)  THEN 'ITABUNA'
        ELSE 'OUTRA'
      END AS ORIGEM
    FROM CHOCOSUL.PCCARREG c
      INNER JOIN CHOCOSUL.PCPEDC p    ON p.NUMCAR = c.NUMCAR
      LEFT JOIN CHOCOSUL.PCMOVENDPEND m   ON c.NUMCAR = m.NUMCAR
    WHERE 
      NVL(c.DATAMON, c.DTSAIDA) >= TRUNC(SYSDATE)-4 
      AND m.DTESTORNO IS NULL
    GROUP BY c.NUMCAR, p.CODFILIAL
  ) t2 ON t2.NUMCAR = c.NUMCAR
WHERE 
  NVL(c.DATAMON, c.DTSAIDA) >= TRUNC(SYSDATE)-4
  AND m.DTESTORNO IS NULL
  -- AND p.CODFILIAL IN (1, 2)
GROUP BY 
   c.NUMCAR
  ,t2.ORIGEM
  ,c.DTSAIDA
  ,c.DATAMON
  ,c.HORAMON
  ,c.MINUTOMON
  ,c.DESTINO
  ,c.DTFECHA
  ,c.CODMOTORISTA
  ,e1.NOME
  ,c.CODVEICULO
  ,c.TOTPESO
  ,c.TOTVOLUME
  ,c.VLTOTAL
  ,c.CODROTAPRINC
  ,r.CODROTA
  ,r.DESCRICAO
  ,c.NUMNOTAS
  ,c.QTITENS
  ,c.OBSFATUR
  ,c.TIPOCARGA
  ,c.OBSDESTINO
  ,c.CARGASECUNDARIA
  ,r.SITUACAO
  ,r.KMROTA
  ,r.VLMINCARREG
  ,r.PRAZOPREVENT
  ,r.TIPOCOMISSAO
  ,r.VLDIARIA
  ,r.NUMDIARIA
  ,r.RASTREADA
  ,r.DIASENTREGA
ORDER BY c.NUMCAR
"""

# ================================================================================
bind_variables = {"row_id": None}
result = queryAll_Execute(queryOracle, bind_variables)
OracleDf = pd.DataFrame(result)
print(OracleDf)

#columns = []
# for column in cursorOracle.description:
#    columns.append(column[0])
# OracleDf.columns = columns
# print(str(len(OracleDf)) + " rows loaded from Oracle")

#Input data into MySQL
rows_to_insert = OracleDf.values

# ================================================================================
primary_keys=["NUMCAR"]

# Definir metadados
metadata = MetaData()

# Definir schema da tabela
table_obj = Table(
    'PCCARREG',
    metadata,
   Column('NUMCAR', Integer, primary_key=True), 
   Column('ORIGEM', String(20)),
   Column('DESTINO', String(20)),
   Column('EM_SEPARACAO', String(1)), 
   Column('SEPARADO', String(1)), 
   Column('EM_CONFERENCIA', String(1)),
   Column('CONFERIDO', String(1)), 
   Column('DTSAIDA', DateTime), 
   Column('DATAMON', DateTime),
   Column('HORAMON', String(2)),
   Column('MINUTOMON', String(2)), 
   Column('DTFECHA', DateTime), 
   Column('CODMOTORISTA', Integer), 
   Column('MOTORISTA', String(80)),
   Column('CODVEICULO', Integer), 
   Column('TOTPESO', Integer), 
   Column('TOTVOLUME', Integer), 
   Column('VLTOTAL', Integer), 
   Column('CODROTAPRINC', Integer), 
   Column('CODROTA', Integer), 
   Column('ROTA', String(40)), 
   Column('NUMNOTAS', Integer), 
   Column('QTITENS', Integer), 
   Column('OBSFATUR', String(255)), 
   Column('TIPOCARGA', String(1)), 
   Column('OBSDESTINO', String(80)), 
   Column('CARGASECUNDARIA', String(1)), 
   Column('SITUACAO', String(1)), 
   Column('KMROTA', Integer), 
   Column('VLMINCARREG', Integer), 
   Column('PRAZOPREVENT', Integer), 
   Column('TIPOCOMISSAO', String(1)), 
   Column('VLDIARIA', Integer), 
   Column('NUMDIARIA', Integer), 
   Column('RASTREADA', String(1)), 
   Column('DIASENTREGA', Integer), 
   Column('QT_PALETES', Integer),
   Column('QT_ENTREGAS', Integer),
   Column('TIPOOS_LIST', String(20)),
    mysql_charset='utf8mb4',
)

# Criar a tabela se não existir
metadata.create_all(engine)

if OracleDf.empty:
   print("DataFrame está vazio. Nada a inserir.")
else:
   with engine.begin() as conn:
      for _, row in OracleDf.iterrows():
         data = row.to_dict()

         stmt = mysql_insert(table_obj).values(**data)

         # Definir campos a serem atualizados no conflito
         update = {k: data[k] for k in data if k not in primary_keys}
         stmt = stmt.on_duplicate_key_update(**update)

         conn.execute(stmt)

      print(f"{len(OracleDf)} registros upsertados na tabela `PCCARREG`.")
      Logger().add("INFO", f"OK - ATUALIZAÇÃO DA TABELA {table_id}", 'CONTROLL_ETL')

session.remove()
engine.dispose()

print("Execution Time : " + (str(round(time.time() - start_time))))

