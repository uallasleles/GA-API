import io
import pandas as pd
from fastapi import Depends, Security, APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Annotated, Dict, Any
import logging
from classes.db_queries import query_Execute, queryAll_Execute, queryAll2_Execute, queryAll_Execute2, load_query, _prepare_bind, row_to_jsonable, update_Execute
from auth.Auth import User, get_current_user, get_current_active_user


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# router = APIRouter()
router = APIRouter(
    prefix="/Buscar", 
    tags=["Queries"]
)

# router_estoque = APIRouter(
#     prefix="/Financeiro", 
#     tags=["Queries"]
# )



# ========================================================================
# Endpoints
# ========================================================================


# 1. Transportadora
# @router.get("/prestador/")
def query_Prestador(
    current_user: Annotated[None, Security(get_current_user, scopes=["prestador:read"])],
    row_id = None, national_id = None, hired_id = None
    ):
    """Código de Fornecedor Teste: 12086"""
    sql = "queries/prestador_json.sql"
    bind_variables = {
        "row_id": row_id, 
        "national_id": national_id, 
        "hired_id": hired_id
    }
    query = load_query(sql)
    result = query_Execute(query, bind_variables)

    return(result)


# @router.get("/prestador_atualizacao/")
def query_Prestador_Atualizacao(
    current_user: Annotated[None, Depends(get_current_active_user)],
    row_id = None, national_id = None, hired_id = None
    ):
    """Código de Fornecedor Teste: 12086"""
    sql = "queries/prestador_json_update.sql"
    bind_variables = {"row_id": row_id, "national_id": national_id, "hired_id": hired_id}
    query = load_query(sql)
    result = query_Execute(query, bind_variables)

    return(result)


# 2. Veículo
# @router.get("/veiculo/")
def query_Veiculo(
    current_user: Annotated[None, Depends(get_current_active_user)],
    row_id = None, license = None, vehicle_id = None
):
    """
    Consulta um veículo pelo documento (placa).  
    Exemplos:  
        - Placa: JMA5093  
        - RowID: AAAXU8AARAAAAlMAAB  
    """
    query = load_query("queries/veiculo_json.sql")
    bind_variables = {"row_id": row_id, "license": license, "vehicle_id": vehicle_id}
    result = query_Execute(query, bind_variables)
    return(result)


# 3. Motorista
# @router.get("/motorista/")
def query_Motorista(
    current_user: Annotated[None, Depends(get_current_active_user)],
    row_id = None, 
    national_id = None, 
    enrollment = None
):
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


# @router.get("/VinculoCartaoPrestadorMotorista/")
def query_VinculoCartao(
    current_user: Annotated[None, Depends(get_current_active_user)],
    row_id = None, driverNationalId = None, cardNumber = None, enrollment = None):
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


# Rota
# @router.get("/solicitarRota/")
def query_Rota(
    current_user: Annotated[None, Depends(get_current_active_user)],
    row_id = None, num_transacao = None, num_mdfe = None):
    sql = "queries/solicitar_rota_json.sql"
    query = load_query(sql)
    bind_variables = {"row_id": row_id, "num_transacao": num_transacao, "num_mdfe": num_mdfe}
    result = query_Execute(query, bind_variables)
    return(result)


# Viagem
# @router.get("/viagem/") 
def query_Viagem( 
    current_user: Annotated[None, Depends(get_current_active_user)],
    num_transacao = None, 
    nummdfe = None, 
    row_id: Annotated[str | None, Query] = None, 
    # nummdfe: Annotated[str | None, Query] = None 
    ): 
    """Apenas consulta uma viagem e retorna o JSON pronto para envio.""" 
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
# @router.get("/viagem/documentos/{id}") 
def query_Viagem_Documentos(
        current_user: Annotated[None, Depends(get_current_active_user)],
        id): 
    """RowID Exemplo: AAAYQEABTAABEl1AAB"""
    sql = "queries/viagem_documentos.sql"
    query = load_query(sql)
    result = queryAll_Execute(query, id)
    return(result)


# Motoristas da Viagem
# @router.get("/viagem/motoristas/{id}")
def query_Viagem_Motoristas(
        current_user: Annotated[None, Depends(get_current_active_user)],
        id):
    """Número da Transação de Exemplo: 38732"""
    sql = "queries/viagem_motoristas.sql"
    query = load_query(sql)
    result = queryAll_Execute(query, id)
    return(result)


# Veículos da Viagem
# @router.get("/viagem/veiculos/{id}")
def query_Viagem_Veiculos(
    current_user: Annotated[None, Depends(get_current_active_user)],    
    id):
    """Número da Transação de Exemplo: 38732"""
    sql = "queries/viagem_veiculos.sql"
    query = load_query(sql)
    result = queryAll_Execute(query, id)
    return(result)


# CONTROLL
@router.get("/controll/carregamentos/")
def query_Carregamentos(
    current_user: Annotated[None, Security(get_current_user, scopes=["carregamentos:read"])],
    num_dias: str = None,
    numcar: str = None
):
    """Número da Transação de Exemplo: 38732"""

    if numcar:
        num_dias = None
    elif not num_dias:
        num_dias = 1

    sql = "queries/controll_carregamentos.sql"
    query = load_query(sql)
    bind_variables = {
        "NUM_DIAS": num_dias,
        "NUMCAR": numcar
    }
    result = query_Execute(query, bind_variables)
    
    return(result)


@router.get("/controll/monitoros")
def query_Monitor_OS(
    current_user: Annotated[None, Security(get_current_user, scopes=["carregamentos:read"])],
    codfilial: str = None,
    numcar: str = None
):
    """Número da Transação de Exemplo: 38732"""
    sql = "queries/controll_monitor_os.sql"
    query = load_query(sql)
    bind_variables = {"CODFILIAL": codfilial, "NUMCAR": numcar} 
    result = queryAll2_Execute(query, bind_variables)
    return(result)


# @router.get("/apuracao-faturamento/")
def query_1464_Apuracao_Faturamento(
    # current_user: Annotated[None, Depends(get_current_active_user)],
    DTENT_INICIO,
    DTENT_FIM,
    codfilial,
    codfornec = None

    ):
    """Código de Fornecedor Teste: 715"""
    sql = "queries/apuracao_faturamento.sql"
    bind_variables = {
        "DTENT_INICIO": DTENT_INICIO,
        "DTENT_FIM": DTENT_FIM,
        "codfilial": codfilial,
        "codfornec": codfornec
    }
    query = load_query(sql)
    result = query_Execute(query, bind_variables)

    return(result)


# @router.get("/1203-extrato-cliente/financeiro/")
# def query_1203_Extrato_Cliente_Financeiro(
#     # current_user: Annotated[None, Depends(get_current_active_user)],
#     DATA_INICIAL: str = None,
#     DATA_FINAL: str = None,
#     # CODCLI = None,
#     ):
#     """Exemplo de Cliente: 118018"""

#     CODCLI = None
#     sql = "queries/1203-consulta-clientes.sql"
#     bind_variables = {
#         "DATA_INICIAL": DATA_INICIAL,
#         "DATA_FINAL": DATA_FINAL,
#         "CODCLI": CODCLI
#     }
#     query = load_query(sql)
#     result = queryAll2_Execute(query, bind_variables)

#     return result


# @router.get("/download/1203-extrato-cliente/financeiro/")
# def download_1203_Extrato_Cliente_Financeiro(
#     # current_user: Annotated[None, Depends(get_current_active_user)],
#     DATA_INICIAL: str = None,
#     DATA_FINAL: str = None,
#     # CODCLI = None,
#     ):
#     """Exemplo de Cliente: 118018"""

#     CODCLI = None
#     sql = "queries/1203-consulta-clientes.sql"
#     bind_variables = {
#         "DATA_INICIAL": DATA_INICIAL,
#         "DATA_FINAL": DATA_FINAL,
#         "CODCLI": CODCLI
#     }
#     query = load_query(sql)
#     result = queryAll2_Execute(query, bind_variables)

#     # 2. Converte para DataFrame do pandas
#     return download_tabela(result)


@router.get("/r410-acertos-de-carga/informacoes-do-carregamento/")
def r410_Acertos_de_Carga_Informacoes_do_Carregamento(
    current_user: Annotated[None, Security(get_current_user, scopes=["carregamento:read"])],
    NUMCAR: str,
    ):
    """Exemplo de Carregamento: 173990"""

    sql = "queries/R410-Informacoes-do-Carregamento.sql"
    bind_variables = {
        "NUMCAR": NUMCAR
    }

    query = load_query(sql)
    result = query_Execute(query, bind_variables)

    return result


@router.get("/r410-acertos-de-carga/notas-fiscais-romaneio/")
def r410_Acertos_de_Carga_Notas_Fiscais_Romaneio(
    NUMCAR: str,
    CODFILIAL: str
    ):
    """Exemplo de Carregamento: 173990"""

    sql = "queries/R410-Notas-Fiscais-Romaneio.sql"
    bind_variables = {
        "NUMCAR": NUMCAR,
        "CODFILIAL": CODFILIAL
    }
    
    query = load_query(sql)
    result = queryAll2_Execute(query, bind_variables)

    return result


@router.get("/consulta-lock-carregamento/")
def consulta_lock_carregamento(
    # current_user: Annotated[None, Security(get_current_user, scopes=["admin"])],
):
    """Consulta por carregamentos travados."""

    sql = "queries/consulta_lock_carregamento.sql"
    bind_variables = {}
    
    query = load_query(sql)
    result = queryAll2_Execute(query, bind_variables)

    return result


@router.post("/remove-lock-carregamento/")
def remove_lock_carregamento(
    current_user: Annotated[None, Security(get_current_user, scopes=["admin"])],
    CODUSUR = None,
    NUMCAR = None
):
    """Remove lock de carregamento."""

    sql = "queries/remove_lock_carregamento.sql"
    bind_variables = {
        "CODUSUR": CODUSUR,
        "NUMCAR": NUMCAR,
    }
    
    query = load_query(sql)
    result = update_Execute(query, bind_variables)

    return result


# @router.get("/download/financeiro/export_risco_zero")
# def export_risco_zero(
#     # current_user: Annotated[None, Depends(get_current_active_user)],
#     CODFILIAL = None,
#     DTEMISSAO_INICIAL: str = None,
#     DTEMISSAO_FINAL: str = None,
#     ):
#     """Exemplo de Cliente: 118018"""

#     sql = "queries/export-risco-zero.sql"
#     bind_variables = {
#         "CODFILIAL": CODFILIAL,
#         "DTEMISSAO_INICIAL": DTEMISSAO_INICIAL,
#         "DTEMISSAO_FINAL": DTEMISSAO_FINAL
#     }
#     query = load_query(sql)
#     result = queryAll2_Execute(query, bind_variables)

#     # 2. Converte para DataFrame do pandas
#     return download_tabela(result)


# @router.get("/download-tabela")
def download_tabela(dados):
    """Em teste!"""
    # 1. Dados que você quer colocar na tabela
    # dados = [
    #     {"id": 1, "nome": "Ana", "cargo": "Engenheira"},
    #     {"id": 2, "nome": "Bruno", "cargo": "Desenvolvedor"},
    # ]
    
    # 2. Converte para DataFrame do pandas
    df = pd.DataFrame(dados)
    
    # 3. Escreve o DataFrame em um buffer em memória (Excel)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    buffer.seek(0)
    
    # 4. Retorna o arquivo com o cabeçalho para download
    nome_arquivo = "tabela_dados.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{nome_arquivo}"'}
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )