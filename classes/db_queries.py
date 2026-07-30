from fastapi import APIRouter
# from typing import Annotated
import logging
import re
from classes import OracleClient
import json
import oracledb
# Adicione esta linha global. Ela transforma automaticamente LOBs em Strings/Bytes
oracledb.defaults.fetch_lobs = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

def load_query(sql_path):
    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(sql_path, "r", encoding="latin-1") as f:
            return f.read()

def _prepare_bind(query, id):
    named = re.findall(r':([A-Za-z_][A-Za-z0-9_]*)', query)
    if isinstance(id, dict):
        return id
    if named:
        if len(named) == 1:
            return {named[0]: id}
        else:
            if isinstance(id, (list, tuple)) and len(id) == len(named):
                return dict(zip(named, id))
            else:
                return {named[0]: id}
    else:
        return [id]

def lob_to_value(v):
    # Trata LOBs do oracledb (ThickLobImpl)
    try:
        if isinstance(v, oracledb.LOB):
            s = v.read()
            # se for JSON, desserializa; caso contrário retorna string/bruto
            try:
                return json.loads(s)
            except Exception:
                return s
    except Exception:
        pass
    return v

# supondo row como dict-like: {'JSON_DOCUMENT': <LOB>, ...}
def row_to_jsonable(row):
    return {k: lob_to_value(v) for k, v in row.items()}

# 1. Transportadora
# @router.get("/prestador", tags=["Queries"])
def query_Prestador(row_id = None, national_id = None, hired_id = None):
    """Código de Fornecedor Teste: 12086"""
    sql = "queries/prestador_json.sql"
    bind_variables = {"row_id": row_id, "national_id": national_id, "hired_id": hired_id}

    query = load_query(sql)
    result = query_Execute(query, bind_variables)

    return(result)

# 2. Veículo
# @router.get("/veiculo/", tags=["Queries"])
def query_Veiculo(
    row_id = None,
    license = None,
    vehicle_id = None
    ):
    sql = "queries/veiculo_json.sql"
    query = load_query(sql)

    # Inicializa com o que é obrigatório
    bind_variables = {
        "row_id": row_id,
        "license": license,
        "vehicle_id": vehicle_id
    }

    result = query_Execute(query, bind_variables)
    return(result)

# 3. Motorista
# @router.get("/motorista/", tags=["Queries"])
def query_Motorista(row_id = None, national_id = None, enrollment = None):
    """Exemplos  
    Código: 2006387  
    RowID: AAAYPnAAOAAFhzXAAB  
    """
    query = load_query("queries/motorista_json.sql")

    bind_variables = {
        "row_id": row_id,
        "national_id": national_id,
        "enrollment": enrollment
    }

    result = query_Execute(query, bind_variables)
    return(result)

# Rota
# @router.get("/solicitarRota/", tags=["Queries"])
def query_Rota(row_id=None, num_transacao=None, num_mdfe=None):
    sql = "queries/solicitar_rota_json.sql"
    query = load_query(sql)
    bind_variables = {
        "row_id":        row_id,
        "num_transacao": num_transacao,
        "num_mdfe":      num_mdfe
    }
    result = query_Execute(query, bind_variables)
    return result

# Viagem
# @router.get("/viagem/", tags=["Queries"])
def query_Viagem(
    num_transacao = None,
    nummdfe = None,
    row_id = None
    ):
    """RowID Exemplo: AAAYQEABTAABEkhAAE"""

    query = load_query("queries/viagem_json.sql")
    
    # Inicializa com o que é obrigatório
    bind_variables = {
        "num_transacao": num_transacao,
        "nummdfe": nummdfe, 
        "row_id": row_id
    }
    
    result = query_Execute(query, bind_variables)
    return result

# Documentos da Viagem
# @router.get("/viagem/documentos/{row_id}", tags=["Queries"])
def query_Viagem_Documentos(row_id):
    """RowID Exemplo: AAAYQEABTAABEl1AAB"""
    from builders.shipping_documents_builder import build_insert_payload
    sql = "queries/viagem_documentos.sql"
    query = load_query(sql)
    qry_rs = queryAll_Execute(query, row_id)
    result = build_insert_payload(qry_rs)
    return(result)

# Movimento
# @router.get("/movimento/{id}", tags=["Queries"])
def query_Movimento(id):
    sql = "queries/movimento.sql"
    query = load_query(sql)
    result = query_Execute(query, id)
    return(result)

# Motoristas da Viagem
# @router.get("/viagem/motoristas/{row_id}", tags=["Queries"])
def query_Viagem_Motoristas(row_id):
    """Número da Transação de Exemplo: 38732"""
    sql = "queries/viagem_motoristas.sql"
    query = load_query(sql)
    result = queryAll_Execute(query, row_id)
    # result = build_insert_payload(qry_rs)
    return(result)

# Veículos da Viagem 
# @router.get("/viagem/veiculos/{row_id}", tags=["Queries"])
def query_Viagem_Veiculos(row_id): 
    """Número da Transação de Exemplo: 38732"""
    # from builders.shipping_vehicles_builder import build_insert_payload
    sql = "queries/viagem_veiculos.sql"
    query = load_query(sql)
    result = queryAll_Execute(query, row_id)
    # result = build_insert_payload(qry_rs)
    return(result)

def query_Verifica_OperationKey(row_id): 
    """Número da Transação de Exemplo: 38732"""
    # from builders.shipping_vehicles_builder import build_insert_payload
    sql = "queries/viagem_veiculos.sql"
    query = load_query(sql)
    result = queryAll_Execute(query, row_id)
    # result = build_insert_payload(qry_rs)
    return(result)
     

def update_viagem_repom1(response_json):
    if isinstance(response_json, str):
        try:
            response_json = json.loads(response_json)
        except (json.JSONDecodeError, TypeError):
            print(f"update_viagem_repom1: resposta não é JSON válido: {response_json}")
            return None

    errors = response_json.get("Errors", [])
    if errors:
        print(f"Erro retornado pela API: {errors}")
        return errors

    # Extração dos dados do JSON de resposta
    data = response_json.get("Data", {})
    r_status = data.get("Status")

    if r_status != 1:  # 1 = sucesso conforme resposta observada
        print(f"Status inesperado da API: {r_status}")
        return None

    route_code       = data.get("RouteCode")
    trace_code       = data.get("TraceCodeRepom")
    trace_identifier = data.get("ExternalTraceCode")  # Seu NUMMDFE enviado

    if not route_code or not trace_code:
        print("Erro: Resposta da API não contém códigos válidos.")
        return

    # Query de Update conforme sua estrutura
    sql_update = load_query("queries/update_MDFe_TraceIdentifier.sql")

    bind_variables = {
        "routeCode": route_code,
        "traceCode": trace_code,
        "traceIdentifier": trace_identifier
    }

    result = update_Execute(sql_update, bind_variables)

    print(f"Sucesso: Manifesto {trace_identifier} atualizado com RouteCode {route_code}.")

    return result

def update_viagem_repom2(response_json): 
    """ 
    Atualiza a tabela CHO_VIAGENS com os códigos de retorno da Repom. 
    """ 
    # Extração dos dados do JSON de resposta 
    data = response_json.get("Result", {}) 
    route_code = data.get("RouteCode") 
    trace_code = data.get("TraceCode") 
    trace_identifier = int(data.get("TraceIdentifier")) # Seu NUMMDFE enviado 

    if not route_code or not trace_code:
        print("Erro: Resposta da API não contém códigos válidos.")
        return

    # Query de Update conforme sua estrutura
    sql_update = load_query("queries/update_MDFe_TraceIdentifier.sql")

    bind_variables = {
        "routeCode": route_code,
        "traceCode": trace_code,
        "traceIdentifier": trace_identifier
    }

    result = update_Execute(sql_update, bind_variables)

    print(f"Sucesso: Manifesto {trace_identifier} atualizado com RouteCode {route_code}.")

    return result

def update_viagem_repom3(response_json, numMDFe):
    """
    Guarda a resposta de newShipping.
    response_api = {
        "Response": {
            "StatusCode": 201,
            "Message": "OperationKey: a0c97908-c550-42f3-94b9-1362699ffa50"
        }
    }
    """
    r_StatusCode = response_json["Response"]["StatusCode"]
    if r_StatusCode == 201:
        # 1. Acessar o valor da chave 'Message' dentro de 'Response'
        message_text = response_json["Response"]["Message"]
        # 2. (Opcional) Se precisar apenas do UUID, você pode limpar a string
        operation_key = message_text.replace("OperationKey: ", "")
        
    sql_update = load_query("queries/update_MDFe_OperationKey.sql")
    bind_variables = {
        "operationKey": operation_key,
        "numMDFe": numMDFe
    }
    result = update_Execute(sql_update, bind_variables)
    return result

# Métodos de consulta
# =================================================================
# @router.get("/VinculoCartaoPrestadorMotorista/", tags=["Queries"])
def query_VinculoCartao(row_id = None, driverNationalId = None, cardNumber = None, enrollment = None):
    sql = "queries/vinculo_cartao.sql"
    query = load_query(sql)
    bind_variables = {
        "row_id": row_id,
        "driverNationalId": driverNationalId,
        "cardNumber": cardNumber,
        "enrollment": enrollment
    }
    result = query_Execute(query, bind_variables)
    return(result)

def query_Execute(query, bind_variables):
    with OracleClient.MyConnection() as connection:
        print(f"Oracle {connection.version}")
        with connection.cursor() as cursor:
            cursor.execute(query, bind_variables)
            columns = [col.name for col in cursor.description] if cursor.description else []
            cursor.rowfactory = (lambda *args: dict(zip(columns, args))) if columns else (lambda *args: args)
            row = cursor.fetchone()
            if row is None:
                logger.warning("Nenhum registro encontrado para %s", bind_variables)
                return f"Nenhum registro encontrado para {bind_variables}"
            else:
                json_document = row_to_jsonable(row)
                result = json_document.get('JSON_DOCUMENT') or row 
                return json.loads(result) if isinstance(result, str) else result
        
def update_Execute(query, bind_variables):
    with OracleClient.MyConnection() as connection:
        print(f"Oracle {connection.version}")
        with connection.cursor() as cursor:
            cursor.execute(query, bind_variables)
            connection.commit()
            print(f"{cursor.rowcount} linha(s) atualizada(s).")
            return f"{cursor.rowcount} linha(s) atualizada(s)."

def queryAll_Execute(query, id):
    with OracleClient.MyConnection() as connection:
        print(f"Oracle {connection.version}")
        with connection.cursor() as cursor:
            cursor.execute(query, [id])
            columns = [col.name for col in cursor.description] if cursor.description else []
            cursor.rowfactory = (lambda *args: dict(zip(columns, args))) if columns else (lambda *args: args)
            result = cursor.fetchall()
            return json.loads(result) if isinstance(result, str) else result

def queryAll2_Execute(query, bind_variables=None):
    with OracleClient.MyConnection() as connection:
        print(f"Oracle {connection.version}")
        with connection.cursor() as cursor:
            # 1. Trata os parâmetros de forma flexível:
            # - Se params for um dicionário, passa direto para o execute (Named Binds)
            # - Se params for uma lista ou tupla, passa direto (Positional Binds)
            # - Se for um valor único (ex: int ou str), encapsula em uma lista para manter compatibilidade
            # - Se for None, executa sem parâmetros
            if bind_variables is None:
                bind_args = []
            elif isinstance(bind_variables, (dict, list, tuple)):
                bind_args = bind_variables
            else:
                bind_args = [bind_variables]

            # 2. Executa a query com os argumentos tratados
            cursor.execute(query, bind_args)
            
            columns = [col.name for col in cursor.description] if cursor.description else []
            cursor.rowfactory = (lambda *args: dict(zip(columns, args))) if columns else (lambda *args: args)
            
            result = cursor.fetchall()
            return json.loads(result) if isinstance(result, str) else result


def queryAll_Execute2(query):
    with OracleClient.MyConnection() as connection:
        print(f"Oracle {connection.version}")
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col.name for col in cursor.description] if cursor.description else []
            cursor.rowfactory = (lambda *args: dict(zip(columns, args))) if columns else (lambda *args: args)
            result = cursor.fetchall()
            return json.loads(result) if isinstance(result, str) else result

