"""
Consultas (somente leitura) usadas na simulação de restrições de venda.

Todas as consultas usam variáveis de ligação e o prefixo CHOCOSUL.
Este módulo não tem nenhum comando de gravação.
"""

# Colunas de PCRESTRICAOVENDA que, preenchidas, estreitam o alcance da restrição.
OUTROS_CRITERIOS = [
    "CODPROD", "NUMREGIAO", "CODFORNEC", "CODPRACA", "CODUSUR", "CODATIV", "CLASSEPRODUTO", "CODEPTO",
    "CODSEC", "CODSUPERVISOR", "TIPOFJ", "CODFILIAL", "FRETEDESPACHO", "CONDVENDA", "CODAUXILIAR",
    "CODCOB", "CODMARCA",
]
_PARCELAS = " + ".join(f"CASE WHEN NVL(G.PRAZO{i},0) > 0 THEN 1 ELSE 0 END" for i in range(1, 13))
_LOTE = 900  # limite de itens por lista IN do Oracle é 1000


def _lotes(valores):
    valores = list(valores)
    for i in range(0, len(valores), _LOTE):
        yield valores[i:i + _LOTE]


def _in(prefixo, valores):
    binds = {f"{prefixo}{i}": v for i, v in enumerate(valores)}
    return ", ".join(f":{n}" for n in binds), binds


def _consultar(cursor, sql, binds=None):
    cursor.execute(sql, binds or {})
    colunas = [c[0] for c in cursor.description]
    return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]


def coletar(clientes: list, planos: list) -> dict:
    # Importação tardia: a configuração do Oracle só é exigida quando há consulta de fato.
    from classes import OracleClient

    with OracleClient.MyConnection() as conexao:
        with conexao.cursor() as cursor:
            return coletar_com_cursor(cursor, clientes, planos)


def coletar_com_cursor(cursor, clientes: list, planos: list) -> dict:
    lista_pl, binds_pl = _in("p", planos)

    info_clientes = {}
    restricoes = []
    uso = {}
    for lote in _lotes(clientes):
        lista_cli, binds_cli = _in("c", lote)
        for r in _consultar(cursor, f"""
            SELECT CODCLI, DTEXCLUSAO, BLOQUEIO FROM CHOCOSUL.PCCLIENT WHERE CODCLI IN ({lista_cli})""", binds_cli):
            info_clientes[int(r["CODCLI"])] = {"ativo": r["DTEXCLUSAO"] is None, "bloqueado": r["BLOQUEIO"] == "S"}

        for r in _consultar(cursor, f"""
            SELECT CODRESTRICAO, CODCLI, CODPLPAG, ORIGEMPED, MOTIVO, {", ".join(OUTROS_CRITERIOS)}
              FROM CHOCOSUL.PCRESTRICAOVENDA
             WHERE CODCLI IN ({lista_cli}) AND CODPLPAG IN ({lista_pl})""", {**binds_cli, **binds_pl}):
            restricoes.append({
                "codrestricao": int(r["CODRESTRICAO"]),
                "codcli": int(r["CODCLI"]),
                "codplpag": int(r["CODPLPAG"]),
                "origem": r["ORIGEMPED"],
                "motivo": r["MOTIVO"],
                "outros_criterios": [c for c in OUTROS_CRITERIOS if r[c] is not None],
            })

        for r in _consultar(cursor, f"""
            SELECT CODPLPAG, COUNT(*) PEDIDOS, COUNT(DISTINCT CODCLI) CLIENTES, ROUND(SUM(VLATEND), 2) VALOR
              FROM CHOCOSUL.PCPEDC
             WHERE CODCLI IN ({lista_cli})
               AND DATA >= ADD_MONTHS(TRUNC(SYSDATE), -12)
               AND POSICAO <> 'C'
             GROUP BY CODPLPAG""", binds_cli):
            if r["CODPLPAG"] is None:
                continue
            acumulado = uso.setdefault(int(r["CODPLPAG"]), {"pedidos": 0, "clientes": 0, "valor": 0.0})
            acumulado["pedidos"] += int(r["PEDIDOS"])
            acumulado["clientes"] += int(r["CLIENTES"])  # lotes não repetem cliente
            acumulado["valor"] = round(acumulado["valor"] + float(r["VALOR"] or 0), 2)

    info_planos = {}
    for r in _consultar(cursor, f"""
        SELECT G.CODPLPAG, G.DESCRICAO, G.STATUS, {_PARCELAS} PARCELAS FROM CHOCOSUL.PCPLPAG G"""):
        info_planos[int(r["CODPLPAG"])] = {
            "descricao": r["DESCRICAO"], "ativo": r["STATUS"] == "A", "parcelas": int(r["PARCELAS"]),
        }

    sem_cliente = [
        {"codrestricao": int(r["CODRESTRICAO"]), "codplpag": int(r["CODPLPAG"]), "origem": r["ORIGEMPED"], "motivo": r["MOTIVO"]}
        for r in _consultar(cursor, f"""
            SELECT CODRESTRICAO, CODPLPAG, ORIGEMPED, MOTIVO FROM CHOCOSUL.PCRESTRICAOVENDA
             WHERE CODPLPAG IN ({lista_pl}) AND CODCLI IS NULL
               AND {" AND ".join(f"{c} IS NULL" for c in OUTROS_CRITERIOS)}""", binds_pl)
    ]

    usados = set(planos)
    return {
        "clientes": info_clientes,
        "planos": {p: info_planos[p] for p in planos if p in info_planos},
        "restricoes": restricoes,
        "restricoes_sem_cliente": sem_cliente,
        "uso": [
            {"codplpag": p, "descricao": info_planos.get(p, {}).get("descricao"), "na_lista": p in usados, **v}
            for p, v in sorted(uso.items(), key=lambda item: -item[1]["pedidos"])
        ],
        "parcelados": [
            {"codplpag": p, "descricao": i["descricao"], "parcelas": i["parcelas"],
             "pedidos_12_meses": uso.get(p, {}).get("pedidos", 0)}
            for p, i in sorted(info_planos.items())
            if i["ativo"] and i["parcelas"] >= 2 and p not in usados
        ],
    }
