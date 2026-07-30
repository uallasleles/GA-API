import json
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_Template(template):
    try:
        with open(template, 'r', encoding='utf-8') as f:
            return(json.load(f))
    except FileNotFoundError:
        logger.error(f"O arquivo '{template}' não foi encontrado.")
        exit()
    except json.JSONDecodeError:
        logger.error(f"Não foi possível decodificar o JSON do arquivo '{template}'.")
        exit()

def imprimir_chaves_recursivo(objeto, caminho_atual="payload", source="", source_object="data"):
    """
    Gera instruções no formato:
        payload["chave"]["sub"] = data["CHAVE_SUB"]
    Suporta objetos JSON iniciando como dict ou list.
    """

    # -------------------------------
    # Caso 1: objeto é uma LISTA
    # -------------------------------
    if isinstance(objeto, list):
        for indice, item in enumerate(objeto):
            novo_caminho = f'{caminho_atual}[{indice}]'
            new_source = f'{source}{indice}'.upper()

            # item é um dict → desce na recursão
            if isinstance(item, dict):
                imprimir_chaves_recursivo(
                    item,
                    novo_caminho,
                    f"{new_source}_",
                    source_object
                )

            # item é outra lista → recursão também
            elif isinstance(item, list):
                imprimir_chaves_recursivo(
                    item,
                    novo_caminho,
                    f"{new_source}_",
                    source_object
                )

            # item é valor primitivo
            else:
                print(f'{novo_caminho} = {source_object}["{new_source}"]')

        return  # evita continuar no bloco de dict abaixo

    # -------------------------------
    # Caso 2: objeto é um DICIONÁRIO
    # -------------------------------
    if isinstance(objeto, dict):
        for chave, valor in objeto.items():
            novo_caminho = f'{caminho_atual}["{chave}"]'
            new_source_key = f"{source}{chave}".upper()

            # Caso seja valor final (não dict, não lista)
            if not isinstance(valor, dict) and not isinstance(valor, list):
                print(f'{novo_caminho} = {source_object}["{new_source_key}"]')

            # Caso seja objeto aninhado (dict)
            if isinstance(valor, dict):
                imprimir_chaves_recursivo(
                    valor,
                    novo_caminho,
                    f"{new_source_key}_",
                    source_object
                )

            # Caso seja lista
            elif isinstance(valor, list):
                for indice, item in enumerate(valor):
                    caminho_lista = f'{novo_caminho}[{indice}]'
                    new_list_source = f"{new_source_key}_{indice}".upper()

                    if isinstance(item, dict) or isinstance(item, list):
                        imprimir_chaves_recursivo(
                            item,
                            caminho_lista,
                            f"{new_list_source}_",
                            source_object
                        )
                    else:
                        print(f'{caminho_lista} = {source_object}["{new_list_source}"]')


def imprimir_chaves_recursivo_2(objeto, caminho_atual="payload", source="", source_object="data"):
    """
    Gera instruções no formato:
        payload["chave"]["sub"] = data["CHAVE_SUB"]
    Suporta objetos JSON iniciando como dict ou list.
    """
    if isinstance(objeto, list):
        for indice, item in enumerate(objeto):
            novo_caminho = f'{caminho_atual}[{indice}]'
            new_source = source + str(indice)
            if isinstance(item, (dict, list)):
                imprimir_chaves_recursivo(item, novo_caminho, new_source + "_", source_object)
            else:
                print(f'{novo_caminho} = {source_object}["{new_source}"]')
    elif isinstance(objeto, dict):
        for chave, valor in objeto.items():
            novo_caminho = f'{caminho_atual}["{chave}"]'
            new_source = source + chave.upper()
            if isinstance(valor, (dict, list)):
                imprimir_chaves_recursivo(valor, novo_caminho, new_source + "_", source_object)
            else:
                print(f'{novo_caminho} = {source_object}["{new_source}"]')


def imprimir_nome_colunas(objeto, source=""):
    """
    Imprime todas as chaves de um objeto JSON aninhado no formato objeto["chave"].
    """
    if isinstance(objeto, dict):
        for chave, valor in objeto.items():

            # Cria o caminho completo para a chave atual
            new_source = f'{source}{chave}'.upper()

            if isinstance(valor, dict) is False and isinstance(valor, list) is False:
                print(f'{new_source}')
            
            # Chamada recursiva se o valor for outro dicionário (objeto aninhado)
            if isinstance(valor, dict):
                new_source = f'{new_source}_'
                imprimir_nome_colunas(valor, new_source)
            
            # Lida com listas, se necessário, iterando sobre seus elementos
            elif isinstance(valor, list):
                for indice, item in enumerate(valor):
                    new_item = f'{new_source}_{indice}'.upper()

                    # Se o item da lista for um dict, continua a recursão
                    if isinstance(item, dict):
                        new_item = f'{new_item}_'
                        imprimir_nome_colunas(item, new_item)

def limpar_numero_telefone(numero_bruto):
    """
    Remove todos os caracteres não numéricos de uma string de telefone.

    Argumentos:
        numero_bruto (str): A string original do número de telefone (ex: "(11) 98765-4321").

    Retorna:
        str: O número de telefone limpo, contendo apenas dígitos (ex: "11987654321").
    """

    # O padrão regex r'\D' corresponde a qualquer caractere que NÃO seja um dígito (0-9).
    # re.sub substitui todas as ocorrências desses caracteres por uma string vazia ('').
    numero_limpo = re.sub(r'\D', '', numero_bruto)
    return numero_limpo

def limpar_numero(numero_bruto):
    """
    Remove todos os caracteres não numéricos de uma string de telefone.

    Argumentos:
        numero_bruto (str): A string original do número de telefone (ex: "(11) 98765-4321").

    Retorna:
        str: O número de telefone limpo, contendo apenas dígitos (ex: "11987654321").
    """

    # O padrão regex r'\D' corresponde a qualquer caractere que NÃO seja um dígito (0-9).
    # re.sub substitui todas as ocorrências desses caracteres por uma string vazia ('').
    numero_limpo = re.sub(r'\D', '', numero_bruto)
    return numero_limpo

# Exemplo de uso:
# telefone1 = "(11) 98765-4321"
# telefone2 = "+55 11 98765.4321"
# telefone3 = "Ligue para: 123-4567"

# print(f"Original: {telefone1} | Limpo: {limpar_numero_telefone(telefone1)}")
# print(f"Original: {telefone2} | Limpo: {limpar_numero_telefone(telefone2)}")
# print(f"Original: {telefone3} | Limpo: {limpar_numero_telefone(telefone3)}")


def teste_schema(path="", name=""):
    schema = load_Template(path)
    imprimir_chaves_recursivo_2(schema, source_object=name)

def teste_colunas():
    schema = load_Template("templates/Shipping/Shipping.json")
    imprimir_nome_colunas(schema)
