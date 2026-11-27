"""
Regras da simulação de restrições de venda (rotina 391, tabela PCRESTRICAOVENDA).

Este módulo não acessa o banco: lê a planilha, valida as entradas e cruza o
pedido com os dados consultados em `restricao_venda_db`.
"""
import csv
import hashlib
import io
import re
import unicodedata

import openpyxl

ORIGENS = {
    "O": "Todas",
    "T": "Telemarketing",
    "B": "Balcão",
    "R": "Balcão Reserva",
    "C": "Call Center",
    "F": "Força de Vendas",
    "W": "Web",
}
MOTIVO_MAX = 50
MAX_COMBINACOES = 10_000

_CAB_CLIENTE = {"CODCLI", "CLIENTE", "CODIGO", "CODIGO DO CLIENTE", "COD CLIENTE", "CODIGO CLIENTE"}
_CAB_PRAZO = {"CODPLPAG", "PRAZO", "PRAZOS", "PLANO", "PLANOS", "CODIGO PRAZO", "CODIGO DO PRAZO", "COD PRAZO"}


class ErroEntrada(ValueError):
    """Entrada inválida; `problemas` é uma lista de mensagens."""

    def __init__(self, problemas):
        self.problemas = [problemas] if isinstance(problemas, str) else list(problemas)
        super().__init__("; ".join(self.problemas))


def _sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def normalizar_motivo(motivo: str) -> str:
    """
    O motivo vai para dentro dos scripts SQL gerados: só aceita um conjunto
    restrito de caracteres (sem aspas, ponto e vírgula, `&` etc.).
    """
    texto = re.sub(r"\s+", " ", _sem_acentos(motivo or "")).strip().upper()
    if not texto:
        raise ErroEntrada("Informe o motivo da restrição.")
    if len(texto) > MOTIVO_MAX:
        raise ErroEntrada(f"Motivo com {len(texto)} caracteres; o máximo é {MOTIVO_MAX}.")
    if not re.fullmatch(r"[A-Z0-9 .,/()_+-]+", texto) or "--" in texto or "/*" in texto:
        raise ErroEntrada("Motivo com caracteres não permitidos. Use letras, números, espaço e . , / ( ) _ + -")
    return texto


def normalizar_origem(origem: str) -> str:
    codigo = (origem or "O").strip().upper()
    if codigo not in ORIGENS:
        raise ErroEntrada(f"Origem inválida: {origem}. Use uma de: " + ", ".join(f"{k} ({v})" for k, v in ORIGENS.items()))
    return codigo


def _inteiro(valor):
    """Converte célula em inteiro positivo; None se não for."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor if valor > 0 else None
    if isinstance(valor, float):
        return int(valor) if valor.is_integer() and valor > 0 else None
    texto = str(valor).strip()
    return int(texto) if re.fullmatch(r"\d{1,10}", texto) and int(texto) > 0 else None


def lista_de_codigos(valor, rotulo="código") -> list:
    """'2, 13;14' -> [2, 13, 14]. Aceita também um número solto."""
    if valor is None or str(valor).strip() == "":
        return []
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        n = _inteiro(valor)
        if n is None:
            raise ErroEntrada(f"{rotulo} inválido: {valor}")
        return [n]
    saida = []
    for parte in re.split(r"[,;\s]+", str(valor).strip()):
        if not parte:
            continue
        n = _inteiro(parte)
        if n is None:
            raise ErroEntrada(f"{rotulo} inválido: {parte[:20]}")
        saida.append(n)
    return saida


def _linhas(nome: str, conteudo: bytes) -> list:
    if (nome or "").lower().endswith(".xlsx") or conteudo[:2] == b"PK":
        try:
            livro = openpyxl.load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
        except Exception as exc:
            raise ErroEntrada(f"Não foi possível ler o arquivo como .xlsx ({type(exc).__name__}).")
        return [list(linha) for linha in livro.worksheets[0].iter_rows(values_only=True)]
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = conteudo.decode("latin-1")
    primeira = texto.split("\n", 1)[0]
    separador = ";" if ";" in primeira else "\t" if "\t" in primeira else ","
    return list(csv.reader(io.StringIO(texto), delimiter=separador))


def ler_planilha(nome: str, conteudo: bytes, prazos_padrao: list) -> dict:
    """
    Lê a primeira aba (.xlsx) ou o CSV. Precisa de uma coluna de cliente; a de
    prazos é opcional quando `prazos_padrao` é informado (e, se informado, ele
    substitui a coluna da planilha).

    Devolve {"pares": [(codcli, codplpag)], "linhas_lidas", "pares_repetidos"}.
    """
    linhas = [l for l in _linhas(nome, conteudo) if any(c not in (None, "") for c in l)]
    if not linhas:
        raise ErroEntrada("Arquivo sem dados.")
    cabecalho = [re.sub(r"\s+", " ", _sem_acentos(str(c or ""))).strip().upper() for c in linhas[0]]
    i_cli = next((i for i, c in enumerate(cabecalho) if c in _CAB_CLIENTE), None)
    i_prazo = next((i for i, c in enumerate(cabecalho) if c in _CAB_PRAZO), None)
    if i_cli is None:
        raise ErroEntrada("Não encontrei a coluna de cliente. Use o cabeçalho 'CODCLI' ou 'CÓDIGO DO CLIENTE'.")
    if i_prazo is None and not prazos_padrao:
        raise ErroEntrada("Informe o parâmetro 'prazos' ou inclua a coluna 'CODPLPAG' / 'CÓDIGO PRAZO' na planilha.")

    problemas, pares, vistos, repetidos = [], [], set(), 0
    for numero, linha in enumerate(linhas[1:], start=2):
        celula = linha[i_cli] if i_cli < len(linha) else None
        codcli = _inteiro(celula) if celula not in (None, "") else None
        if codcli is None:
            problemas.append(f"Linha {numero}: código de cliente vazio ou inválido.")
            continue
        try:
            prazos = prazos_padrao or lista_de_codigos(linha[i_prazo] if i_prazo < len(linha) else None, "Prazo")
        except ErroEntrada as exc:
            problemas.append(f"Linha {numero}: {exc.problemas[0]}")
            continue
        if not prazos:
            problemas.append(f"Linha {numero}: sem prazo.")
            continue
        for plano in prazos:
            if (codcli, plano) in vistos:
                repetidos += 1
            else:
                vistos.add((codcli, plano))
                pares.append((codcli, plano))
        if len(pares) > MAX_COMBINACOES:
            raise ErroEntrada(f"Mais de {MAX_COMBINACOES} combinações de cliente e prazo; divida o arquivo.")
    if problemas:
        extras = len(problemas) - 50
        raise ErroEntrada(problemas[:50] + ([f"... e mais {extras} problemas."] if extras > 0 else []))
    if not pares:
        raise ErroEntrada("Nenhuma combinação de cliente e prazo no arquivo.")
    return {"pares": sorted(pares), "linhas_lidas": len(linhas) - 1, "pares_repetidos": repetidos}


def assinatura(pares: list, origem: str, motivo: str) -> str:
    """Impressão digital do que seria gravado (a fase de aplicação vai exigir a mesma)."""
    base = f"{origem}|{motivo}|" + ";".join(f"{c}:{p}" for c, p in sorted(pares))
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def analisar(pares: list, origem: str, motivo: str, dados: dict, somente_ativos: bool = False) -> dict:
    """
    Cruza o pedido com os dados do banco.

    `dados`: clientes {codcli: {ativo, bloqueado}}, planos {codplpag: {descricao,
    ativo, parcelas}}, restricoes [linhas de cliente x prazo], restricoes_sem_cliente,
    uso [{CODPLPAG, PEDIDOS, VALOR, CLIENTES}], parcelados [{...}].
    """
    clientes, planos = dados["clientes"], dados["planos"]
    pedidos_cli = sorted({c for c, _ in pares})
    pedidos_pl = sorted({p for _, p in pares})

    inexistentes = [c for c in pedidos_cli if c not in clientes]
    planos_inexistentes = [p for p in pedidos_pl if p not in planos]
    inativos = [c for c in pedidos_cli if c in clientes and not clientes[c]["ativo"]]
    bloqueados = [c for c in pedidos_cli if c in clientes and clientes[c]["bloqueado"]]

    fora = set(inexistentes) | (set(inativos) if somente_ativos else set())
    validos = [(c, p) for c, p in pares if c not in fora and p not in planos_inexistentes]

    # Coberta = restrição sem nenhum outro critério e com origem Todas (ou a mesma pedida).
    cobertas, parciais = set(), {}
    for r in dados["restricoes"]:
        par = (r["codcli"], r["codplpag"])
        origem_ok = r["origem"] in (None, "O") or r["origem"] == origem
        if origem_ok and not r["outros_criterios"]:
            cobertas.add(par)
        else:
            parciais.setdefault(par, []).append(
                {"codrestricao": r["codrestricao"], "origem": r["origem"], "criterios": r["outros_criterios"], "motivo": r["motivo"]}
            )

    a_inserir = [par for par in validos if par not in cobertas]
    ja_cobertas = [par for par in validos if par in cobertas]

    alertas = []
    if inexistentes:
        alertas.append(f"{len(inexistentes)} cliente(s) não existem no cadastro e ficaram de fora.")
    if planos_inexistentes:
        alertas.append(f"Prazo(s) inexistente(s), fora da simulação: {', '.join(map(str, planos_inexistentes))}.")
    inativos_pl = [p for p in pedidos_pl if p in planos and not planos[p]["ativo"]]
    if inativos_pl:
        alertas.append(f"Prazo(s) inativo(s) na lista: {', '.join(map(str, inativos_pl))}.")
    if inativos:
        alertas.append(f"{len(inativos)} cliente(s) inativo(s) " + ("ficaram de fora." if somente_ativos else "estão incluídos."))
    if bloqueados:
        alertas.append(f"{len(bloqueados)} cliente(s) estão bloqueados no cadastro.")
    n_parciais = sum(1 for par in a_inserir if par in parciais)
    if n_parciais:
        alertas.append(f"{n_parciais} combinação(ões) já têm restrição com outros critérios ou outra origem; "
                       "uma nova linha seria incluída mesmo assim.")
    if dados["restricoes_sem_cliente"]:
        alertas.append(f"ATENÇÃO: há {len(dados['restricoes_sem_cliente'])} restrição(ões) desses prazos sem cliente.")
    if origem != "O":
        alertas.append(f"Origem {origem} ({ORIGENS[origem]}): pedidos de outras origens continuam liberados.")
    parcelados = dados.get("parcelados") or []
    if parcelados and any(planos.get(p, {}).get("parcelas", 0) >= 2 for p in pedidos_pl):
        alertas.append(f"Há {len(parcelados)} outro(s) prazo(s) parcelado(s) ativo(s) fora da lista, que continuariam liberados.")

    return {
        "somente_simulacao": True,
        "motivo": motivo,
        "origem": {"codigo": origem, "descricao": ORIGENS[origem]},
        "assinatura": assinatura(a_inserir, origem, motivo),
        "resumo": {
            "clientes_informados": len(pedidos_cli),
            "clientes_inexistentes": len(inexistentes),
            "clientes_inativos": len(inativos),
            "clientes_bloqueados": len(bloqueados),
            "prazos_informados": len(pedidos_pl),
            "combinacoes_informadas": len(pares),
            "combinacoes_ja_cobertas": len(ja_cobertas),
            "combinacoes_a_inserir": len(a_inserir),
        },
        "alertas": alertas,
        "clientes": {"inexistentes": inexistentes, "inativos": inativos, "bloqueados": bloqueados},
        "prazos": [
            {"codplpag": p, **(planos.get(p) or {"descricao": None, "ativo": False, "parcelas": 0}), "existe": p in planos}
            for p in pedidos_pl
        ],
        "restricoes_parciais": [
            {"codcli": c, "codplpag": p, "existentes": v} for (c, p), v in sorted(parciais.items())
        ],
        "restricoes_sem_cliente": dados["restricoes_sem_cliente"],
        "uso_12_meses": dados["uso"],
        "outros_prazos_parcelados": parcelados,
        "a_inserir": [{"codcli": c, "codplpag": p} for c, p in a_inserir],
    }
