"""Validação e conversão de CSVs para a API própria do RHGestor (Sólides).

Módulo puro (sem FastAPI, sem rede, sem banco) para poder ser testado
isoladamente. Regras de origem: explic_colab.txt e o guia
"[MANUAL INTERNO_EXTERNO] API Própria.pdf".
"""
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from classes import rhgestor_layouts as hdr

SEPARADOR = ";"

# nome do layout (rota) -> (código da Sólides, cabeçalho oficial)
LAYOUTS = {
    "colaboradores": ("101", hdr.COLABORADORES),
    "ferias": ("202", hdr.FERIAS),
    "atestados": ("303", hdr.ATESTADOS),
    "financeiro": ("404", hdr.FINANCEIRO),
}

# Tamanhos máximos (explic_colab.txt) por campo do layout 101.
TAMANHOS_COLABORADORES = {
    "CODIGO": 10, "NOME": 50, "ENDERECO": 100, "BAIRRO": 50, "CIDADE": 50,
    "ESTADO": 2, "CEP": 10, "NASCIMENTO": 10, "CPF": 18, "RG": 15,
    "TITULO_ELEITOR": 50, "CTPS": 25, "PASSAPORTE": 20, "HABILITACAO": 20,
    # explic_colab.txt cita 3 e 10 para TIPO_HABILITACAO; usamos o maior.
    "TIPO_HABILITACAO": 10, "ADMISSAO": 10, "DESLIGAMENTO": 10,
    "COD_CARGO_ATUAL": 10, "NOME_CARGO_ATUAL": 50, "COD_DPTO_ATUAL": 10,
    "NOME_DPTO_ATUAL": 50, "EMAIL": 50, "SEXO": 1, "FONE_RESIDENCIAL": 15,
    "CELULAR": 15, "FONE_COMERCIAL": 15, "ESTADO_CIVIL": 15, "QT_FILHOS": 2,
    "NOME_MAE": 50, "NOME_PAI": 50, "TP_SANGUE": 2, "SALARIO_NOMINAL": 15,
    "MINIMO_GARANTIDO": 15, "MEDIA_GANHO_VARIAVEIS": 15, "COD_EMPRESA": 10,
    "NOME_EMPRESA": 50, "COD_AREA": 10, "NOME_AREA": 50,
    "COD_DEPARTAMENTO": 10, "NOME_DEPARTAMENTO": 50, "COD_SETOR": 10,
    "NOME_SETOR": 50, "COD_CARGO": 10, "NOME_CARGO": 50,
    "CAUSA_DEMISSAO": 50, "PCD": 3, "NATURALIDADE": 50, "MENOR_APRENDIZ": 3,
    "PIS": 20, "DATA_EXPEDICAO_CTPS": 10, "UF_EXPEDIDOR_CTPS": 2,
    "DATA_EXPEDICAO_RG": 10, "UF_EXPEDIDOR_RG": 2, "RESERVISTA": 20,
    "CARTEIRA_HABILITACAO": 10, "EXPEDICAO_CARTEIRA_HABILITACAO": 10,
    "UF_EXPEDIDOR_HABILITACAO": 2, "VALIDADE_CNH": 10, "QTDE_HORAS_MES": 4,
    "ESCALA_COLABORADOR": 50, "COD_HORARIO_TRABALHO": 10,
    "MOTIVO_ADMISSAO": 50, "REGIME_CONTRATACAO": 30, "SUPERIOR_IMEDIATO": 10,
    "COD_ESCOLARIDADE": 10, "DESCRICAO_ESCOLARIDADE": 50,
    "DESCRICAO_RACA": 50, "NACIONALIDADE": 50, "CBO_CARGO": 10,
    "EMAIL_PESSOAL": 50, "COD_BANCO": 10, "AGENCIA": 10, "CONTA": 10,
    "TIPO_CONTA": 20, "PIX": 50,
}

CAMPOS_DATA = [
    "NASCIMENTO", "ADMISSAO", "DESLIGAMENTO", "DATA_EXPEDICAO_CTPS",
    "DATA_EXPEDICAO_RG", "EXPEDICAO_CARTEIRA_HABILITACAO", "VALIDADE_CNH",
]
CAMPOS_SALARIO = ["SALARIO_NOMINAL", "MINIMO_GARANTIDO", "MEDIA_GANHO_VARIAVEIS"]
CAMPOS_FONE = ["FONE_RESIDENCIAL", "CELULAR", "FONE_COMERCIAL"]

RE_CEP = re.compile(r"^\d{2}\.\d{3}-\d{3}$")
RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
RE_SALARIO = re.compile(r"^\d{15}$")
RE_DIGITOS = re.compile(r"^\d+$")

MAX_PROBLEMAS = 1000  # limite de itens detalhados devolvidos


class ErroConversao(Exception):
    """A conversão não pôde ser feita; carrega a lista de problemas."""

    def __init__(self, problemas: list):
        super().__init__("Conversão não realizada: o arquivo tem erros.")
        self.problemas = problemas


@dataclass
class Problema:
    nivel: str  # "erro" | "alerta"
    codigo: str
    mensagem: str
    linha: Optional[int] = None
    campo: Optional[str] = None

    def dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Linhas:
    """CSV decodificado: preserva o fim de linha de cada linha."""
    cabecalho: list
    registros: list  # lista de (numero_linha, campos)
    eols: dict  # numero_linha -> fim de linha original ("\r\n", "\n", "")
    bom: bool = False


def decodificar(conteudo: bytes) -> tuple:
    """Devolve (texto, bom) ou levanta UnicodeDecodeError."""
    bom = conteudo.startswith(b"\xef\xbb\xbf")
    texto = (conteudo[3:] if bom else conteudo).decode("utf-8")
    return texto, bom


def _separar_linhas(texto: str) -> list:
    """Divide em [(conteudo, eol)] sem perder o tipo de quebra de linha."""
    partes = re.split(r"(\r\n|\n)", texto)
    saida = []
    for i in range(0, len(partes), 2):
        conteudo = partes[i]
        eol = partes[i + 1] if i + 1 < len(partes) else ""
        if conteudo == "" and eol == "":
            continue
        saida.append((conteudo, eol))
    return saida


def _ler(conteudo: bytes) -> Linhas:
    texto, bom = decodificar(conteudo)
    linhas = _separar_linhas(texto)
    if not linhas:
        return Linhas(cabecalho=[], registros=[], eols={}, bom=bom)
    cab = linhas[0][0].split(SEPARADOR)
    registros = []
    eols = {1: linhas[0][1]}
    for n, (conteudo_linha, eol) in enumerate(linhas[1:], start=2):
        eols[n] = eol
        if conteudo_linha.strip() == "":
            continue  # linha em branco: ignorada
        registros.append((n, conteudo_linha.split(SEPARADOR)))
    return Linhas(cabecalho=cab, registros=registros, eols=eols, bom=bom)


def contar_linhas(conteudo: bytes) -> Optional[int]:
    """Número de linhas de dados (sem cabeçalho nem linhas em branco)."""
    try:
        return len(_ler(conteudo).registros)
    except UnicodeDecodeError:
        return None


# ---------------------------------------------------------------- validação

def validar(layout: str, conteudo: bytes) -> dict:
    """Valida o CSV sem enviar. Devolve resumo + lista de problemas."""
    codigo, cabecalho_oficial = LAYOUTS[layout]
    problemas: list = []
    erro = lambda c, m, l=None, f=None: problemas.append(Problema("erro", c, m, l, f))  # noqa: E731
    alerta = lambda c, m, l=None, f=None: problemas.append(Problema("alerta", c, m, l, f))  # noqa: E731

    try:
        dados = _ler(conteudo)
    except UnicodeDecodeError as exc:
        erro("ENCODING", f"O arquivo não é UTF-8 válido (byte inválido na posição {exc.start}).")
        return _resultado(layout, codigo, problemas, 0)

    if dados.bom:
        alerta("BOM", "Arquivo com BOM (marca de UTF-8). O recomendado é UTF-8 sem BOM.")
    if not dados.cabecalho:
        erro("VAZIO", "O arquivo está vazio.")
        return _resultado(layout, codigo, problemas, 0)

    # cabeçalho
    if dados.cabecalho != cabecalho_oficial:
        if len(dados.cabecalho) == 1 and any(s in dados.cabecalho[0] for s in (",", "\t", "|")):
            erro("SEPARADOR", "Separador inválido: o arquivo deve usar ponto e vírgula (;).", 1)
        else:
            _comparar_cabecalho(dados.cabecalho, cabecalho_oficial, erro)
    esperado = len(cabecalho_oficial)

    sizes = TAMANHOS_COLABORADORES if layout == "colaboradores" else {}
    vistos: dict = {}
    for n, campos in dados.registros:
        if len(campos) != esperado:
            erro("COLUNAS", f"Número de colunas incorreto: {len(campos)} (esperado {esperado}).", n)
            continue
        if layout == "colaboradores":
            _validar_colaborador(n, campos, vistos, erro, alerta, sizes)

    return _resultado(layout, codigo, problemas, len(dados.registros))


def _comparar_cabecalho(atual: list, oficial: list, erro) -> None:
    if len(atual) != len(oficial):
        erro("CABECALHO", f"Cabeçalho com {len(atual)} colunas (esperado {len(oficial)}).", 1)
    for i, (a, o) in enumerate(zip(atual, oficial), start=1):
        if a != o:
            erro("CABECALHO", f"Coluna {i} do cabeçalho é '{a}' (esperado '{o}').", 1, o)


def _validar_colaborador(n, campos, vistos, erro, alerta, sizes) -> None:
    linha = dict(zip(hdr.COLABORADORES, campos))

    # tamanhos máximos
    for nome, limite in sizes.items():
        valor = linha[nome]
        if len(valor) > limite:
            erro("TAMANHO", f"Valor com {len(valor)} caracteres (máximo {limite}).", n, nome)

    # CODIGO: numérico, até 10 dígitos, único
    codigo = linha["CODIGO"]
    if codigo == "":
        erro("CODIGO", "CODIGO vazio.", n, "CODIGO")
    elif not RE_DIGITOS.match(codigo):
        erro("CODIGO", "CODIGO deve ser numérico.", n, "CODIGO")
    else:
        if len(codigo) > 10:
            erro("CODIGO", "CODIGO com mais de 10 dígitos.", n, "CODIGO")
        if codigo in vistos:
            erro("CODIGO_DUPLICADO", f"CODIGO repetido (também na linha {vistos[codigo]}).", n, "CODIGO")
        else:
            vistos[codigo] = n

    # datas dd/mm/aaaa
    for nome in CAMPOS_DATA:
        valor = linha[nome]
        if valor and not _data_valida(valor):
            erro("DATA", "Data inválida; use dd/mm/aaaa.", n, nome)

    # sexo
    if linha["SEXO"] not in ("M", "F"):
        erro("SEXO", "SEXO deve ser M ou F.", n, "SEXO")

    # --- alertas
    for nome, valor in linha.items():
        if valor and any(ord(ch) > 127 for ch in valor):
            alerta("ACENTO", "Contém acentos/caracteres não ASCII (recomenda-se não usar).", n, nome)
    for nome in CAMPOS_SALARIO:
        valor = linha[nome]
        if valor and not RE_SALARIO.match(valor):
            alerta("SALARIO_FORMATO", "Fora do formato de 15 dígitos sem separador.", n, nome)
    if linha["CEP"] and not RE_CEP.match(linha["CEP"]):
        alerta("CEP_FORMATO", "CEP fora do formato 00.000-000.", n, "CEP")
    if linha["CPF"] and not RE_CPF.match(linha["CPF"]):
        alerta("CPF_FORMATO", "CPF fora do formato 000.000.000-00.", n, "CPF")
    for nome in CAMPOS_FONE:
        valor = linha[nome]
        if valor and RE_DIGITOS.match(valor):
            alerta("FONE_FORMATO", "Telefone sem pontuação (sugestão: (XX) XXXX-XXXX).", n, nome)


def _data_valida(valor: str) -> bool:
    if not RE_DATA.match(valor):
        return False
    try:
        datetime.strptime(valor, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def _resultado(layout, codigo, problemas, linhas) -> dict:
    erros = [p for p in problemas if p.nivel == "erro"]
    alertas = [p for p in problemas if p.nivel == "alerta"]
    por_tipo: dict = {}
    for p in problemas:
        chave = f"{p.nivel}:{p.codigo}"
        por_tipo[chave] = por_tipo.get(chave, 0) + 1
    # erros primeiro; alertas depois, dentro do limite
    ordenados = erros + alertas
    return {
        "layout": layout,
        "codigo_layout": codigo,
        "valido": not erros,
        "linhas": linhas,
        "total_erros": len(erros),
        "total_alertas": len(alertas),
        "resumo": por_tipo,
        "problemas": [p.dict() for p in ordenados[:MAX_PROBLEMAS]],
        "truncado": len(ordenados) > MAX_PROBLEMAS,
    }


# ---------------------------------------------------------------- conversão

def remover_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def converter_salario(valor: str) -> str:
    """'1621,00' -> '000000162100'. Vazio fica vazio. Levanta ValueError."""
    v = valor.strip()
    if v == "":
        return ""
    if RE_SALARIO.match(v):
        return v  # já está no formato final
    if "," in v:
        v = v.replace(".", "").replace(",", ".")
    elif v.count(".") == 1 and len(v.rsplit(".", 1)[1]) <= 2:
        pass  # ponto como separador decimal (1621.5)
    else:
        v = v.replace(".", "")  # pontos de milhar
    try:
        numero = Decimal(v)
    except InvalidOperation:
        raise ValueError("valor monetário inválido")
    if numero < 0:
        raise ValueError("valor negativo")
    centavos = int((numero * 100).to_integral_value())
    texto = str(centavos).zfill(15)
    if len(texto) > 15:
        raise ValueError("valor excede 15 dígitos")
    return texto


def converter_colaboradores(conteudo: bytes) -> tuple:
    """Aplica as conversões (a, b, c) ao layout 101.

    Devolve (novos_bytes, alteracoes). Levanta ErroConversao se houver erros
    (CODIGO não numérico, duplicados após concatenar etc.).
    """
    try:
        dados = _ler(conteudo)
    except UnicodeDecodeError as exc:
        raise ErroConversao([Problema("erro", "ENCODING", f"Arquivo não é UTF-8 válido (posição {exc.start}).").dict()])
    esperado = len(hdr.COLABORADORES)
    if dados.cabecalho != hdr.COLABORADORES:
        raise ErroConversao([Problema("erro", "CABECALHO", "Cabeçalho diferente do layout 101; rode a validação.", 1).dict()])

    idx = {nome: i for i, nome in enumerate(hdr.COLABORADORES)}
    erros: list = []
    novos: dict = {}  # numero_linha -> campos convertidos
    codigos_vistos: dict = {}
    cont = {"CODIGO": 0, "SUPERIOR_IMEDIATO": 0, "ACENTOS": 0, "SALARIOS": 0}
    exemplos = {"CODIGO": [], "SUPERIOR_IMEDIATO": []}

    for n, campos in dados.registros:
        if len(campos) != esperado:
            erros.append(Problema("erro", "COLUNAS", f"Número de colunas incorreto: {len(campos)} (esperado {esperado}).", n).dict())
            continue
        campos = list(campos)
        empresa = campos[idx["COD_EMPRESA"]]

        # (a) CODIGO e SUPERIOR_IMEDIATO
        for nome in ("CODIGO", "SUPERIOR_IMEDIATO"):
            valor = campos[idx[nome]]
            if nome == "SUPERIOR_IMEDIATO" and valor == "":
                continue
            novo = _concatenar(empresa, valor, nome, n, erros)
            if novo is not None:
                if novo != valor:
                    cont[nome] += 1
                    if len(exemplos[nome]) < 3:
                        exemplos[nome].append(f"{valor} -> {novo}")
                campos[idx[nome]] = novo
        novo_codigo = campos[idx["CODIGO"]]
        if RE_DIGITOS.match(novo_codigo) and len(novo_codigo) == 10:
            if novo_codigo in codigos_vistos:
                erros.append(Problema("erro", "CODIGO_DUPLICADO", f"CODIGO duplicado após concatenação (também na linha {codigos_vistos[novo_codigo]}).", n, "CODIGO").dict())
            else:
                codigos_vistos[novo_codigo] = n

        # (b) acentos, em todos os campos
        for i, valor in enumerate(campos):
            sem = remover_acentos(valor)
            if sem != valor:
                campos[i] = sem
                cont["ACENTOS"] += 1

        # (c) salários
        for nome in CAMPOS_SALARIO:
            valor = campos[idx[nome]]
            try:
                novo = converter_salario(valor)
            except ValueError as exc:
                erros.append(Problema("erro", "SALARIO", f"Não foi possível converter: {exc}.", n, nome).dict())
                continue
            if novo != valor:
                campos[idx[nome]] = novo
                cont["SALARIOS"] += 1
        novos[n] = campos

    if erros:
        raise ErroConversao(erros[:MAX_PROBLEMAS])

    # reconstrução preservando cabeçalho, ordem e fim de linha de cada linha
    mapa = dict(dados.registros)
    saida = [SEPARADOR.join(dados.cabecalho) + dados.eols.get(1, "")]
    texto, bom = decodificar(conteudo)
    originais = _separar_linhas(texto)
    for n, (original, eol) in enumerate(originais[1:], start=2):
        saida.append((SEPARADOR.join(novos[n]) if n in novos else original) + eol)
    resultado = "".join(saida).encode("utf-8")
    if bom:
        resultado = b"\xef\xbb\xbf" + resultado

    alteracoes = [
        {"campo": "CODIGO", "regra": "empresa(3) + colaborador(7) com zeros à esquerda",
         "valores_alterados": cont["CODIGO"], "exemplos": exemplos["CODIGO"]},
        {"campo": "SUPERIOR_IMEDIATO", "regra": "mesmo critério do CODIGO (usa a empresa da própria linha)",
         "valores_alterados": cont["SUPERIOR_IMEDIATO"], "exemplos": exemplos["SUPERIOR_IMEDIATO"]},
        {"campo": "todos", "regra": "remoção de acentos (NFKD)", "valores_alterados": cont["ACENTOS"]},
        {"campo": ", ".join(CAMPOS_SALARIO), "regra": "valor em 15 dígitos sem separador",
         "valores_alterados": cont["SALARIOS"]},
    ]
    return resultado, alteracoes


def _concatenar(empresa: str, valor: str, nome: str, n: int, erros: list) -> Optional[str]:
    if not RE_DIGITOS.match(valor):
        erros.append(Problema("erro", "CODIGO", f"{nome} deve ser numérico.", n, nome).dict())
        return None
    if not RE_DIGITOS.match(empresa):
        erros.append(Problema("erro", "CODIGO", "COD_EMPRESA vazio ou não numérico; não dá para concatenar.", n, "COD_EMPRESA").dict())
        return None
    if len(empresa) > 3 or len(valor) > 7:
        erros.append(Problema("erro", "CODIGO", f"{nome} (ou COD_EMPRESA) grande demais para 3+7 dígitos; arquivo já convertido?", n, nome).dict())
        return None
    return empresa.zfill(3) + valor.zfill(7)
