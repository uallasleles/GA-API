"""Testes da simulação de restrições de venda. Dados 100% sintéticos; nada acessa o Oracle."""
import io
import re
import zipfile

import openpyxl
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.Auth import User, get_current_user
from auth.database import get_session
from classes import restricao_venda as r
from classes import restricao_venda_scripts as s
from routers import restricoes


def xlsx(linhas):
    livro = openpyxl.Workbook()
    for linha in linhas:
        livro.active.append(linha)
    buffer = io.BytesIO()
    livro.save(buffer)
    return buffer.getvalue()


def dados(**kw):
    base = {
        "clientes": {10: {"ativo": True, "bloqueado": False}, 20: {"ativo": False, "bloqueado": False},
                     30: {"ativo": True, "bloqueado": True}},
        "planos": {2: {"descricao": "21/28/35", "ativo": True, "parcelas": 3},
                   13: {"descricao": "14/21", "ativo": True, "parcelas": 2}},
        "restricoes": [], "restricoes_sem_cliente": [], "uso": [], "parcelados": [],
    }
    base.update(kw)
    return base


def restricao(codcli, codplpag, origem="O", criterios=(), cod=1):
    return {"codrestricao": cod, "codcli": codcli, "codplpag": codplpag, "origem": origem,
            "motivo": "X", "outros_criterios": list(criterios)}


# ---------- entrada
def test_planilha_com_lista_de_prazos_por_linha():
    p = r.ler_planilha("a.xlsx", xlsx([["CÓDIGO DO CLIENTE", "CÓDIGO PRAZO"], [10, "2, 13"], [20, 2], [10, "2"]]), [])
    assert p["pares"] == [(10, 2), (10, 13), (20, 2)] and p["pares_repetidos"] == 1 and p["linhas_lidas"] == 3


def test_csv_com_prazos_do_parametro():
    p = r.ler_planilha("a.csv", b"CODCLI;NOME\n10;x\n20;y\n", [2])
    assert p["pares"] == [(10, 2), (20, 2)]


@pytest.mark.parametrize("conteudo, trecho", [
    (b"NOME;CODPLPAG\nx;2\n", "coluna de cliente"),
    (b"CODCLI\n10\n", "prazos"),
    (b"CODCLI;CODPLPAG\nabc;2\n10;\n20;2x\n", "Linha 2"),
    (b"CODCLI;CODPLPAG\n", "Nenhuma"),
])
def test_planilha_invalida(conteudo, trecho):
    with pytest.raises(r.ErroEntrada) as exc:
        r.ler_planilha("a.csv", conteudo, [])
    assert trecho in str(exc.value)


def test_limite_de_combinacoes(monkeypatch):
    monkeypatch.setattr(r, "MAX_COMBINACOES", 3)
    with pytest.raises(r.ErroEntrada):
        r.ler_planilha("a.csv", b"CODCLI\n1\n2\n3\n4\n", [2])


def test_motivo_normalizado_e_protegido():
    assert r.normalizar_motivo("  cliente não  parcela ") == "CLIENTE NAO PARCELA"
    for ruim in ["", "x" * 51, "a'b", "a;b", "a&b", "a -- b", "a /* b"]:
        with pytest.raises(r.ErroEntrada):
            r.normalizar_motivo(ruim)


def test_origem():
    assert r.normalizar_origem("w") == "W"
    with pytest.raises(r.ErroEntrada):
        r.normalizar_origem("Z")


# ---------- análise
def test_cobertura_parcial_inexistente_e_inativo():
    pares = [(10, 2), (10, 13), (20, 2), (30, 2), (99, 2), (10, 7)]
    d = dados(restricoes=[restricao(10, 2), restricao(10, 13, criterios=["TIPOFJ"]), restricao(30, 2, origem="W")])
    res = r.analisar(pares, "O", "M", d)
    assert [(x["codcli"], x["codplpag"]) for x in res["a_inserir"]] == [(10, 13), (20, 2), (30, 2)]
    assert res["resumo"]["combinacoes_ja_cobertas"] == 1
    assert res["clientes"] == {"inexistentes": [99], "inativos": [20], "bloqueados": [30]}
    assert len(res["restricoes_parciais"]) == 2
    assert any("inexistente" in a and "7" in a for a in res["alertas"])
    so_ativos = r.analisar(pares, "O", "M", d, somente_ativos=True)
    assert [(x["codcli"], x["codplpag"]) for x in so_ativos["a_inserir"]] == [(10, 13), (30, 2)]


def test_origem_especifica_e_coberta_por_todas_ou_pela_mesma():
    d = dados(restricoes=[restricao(10, 2, origem="W"), restricao(30, 2, origem="O")])
    res = r.analisar([(10, 2), (30, 2)], "W", "M", d)
    assert res["resumo"]["combinacoes_a_inserir"] == 0


def test_assinatura_muda_com_o_conteudo():
    a = r.assinatura([(1, 2), (3, 4)], "O", "M")
    assert a == r.assinatura([(3, 4), (1, 2)], "O", "M")
    assert a != r.assinatura([(1, 2)], "O", "M") and a != r.assinatura([(1, 2), (3, 4)], "W", "M")


# ---------- scripts
def test_scripts_so_com_o_que_falta_inserir():
    res = r.analisar([(10, 2), (10, 13), (30, 2)], "O", "MOTIVO", dados(restricoes=[restricao(10, 2)]))
    arq = s.gerar_arquivos(res)
    assert "incluir(10, 13);" in arq["02_insert_restricoes.sql"] and "incluir(30, 2);" in arq["02_insert_restricoes.sql"]
    # a combinação já coberta não aparece em nenhum script (a reversão não pode apagá-la)
    assert all("(10, 2);" not in t for n, t in arq.items() if n.endswith(".sql"))
    assert "(30, 2)" not in arq["02a_teste_um_cliente.sql"]
    assert "COMMIT;" not in re.sub(r"--.*", "", arq["02_insert_restricoes.sql"])
    for nome in ("01_pre_conferencia.sql", "03_conferencia.sql"):
        assert not re.search(r"\b(INSERT|UPDATE|DELETE|MERGE|COMMIT)\b", re.sub(r"--.*", "", arq[nome]))


# ---------- endpoint
@pytest.fixture
def cliente(monkeypatch):
    app = FastAPI()
    app.include_router(restricoes.router)
    app.dependency_overrides[get_session] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: User(username="teste", scopes=["restricao:read"])
    monkeypatch.setattr(restricoes.banco, "coletar", lambda c, p: dados(restricoes=[restricao(10, 2)]))
    return TestClient(app)


def enviar(cliente, conteudo=b"CODCLI;CODPLPAG\n10;2,13\n", **form):
    return cliente.post("/Vendas/restricoes/simular", files={"file": ("a.csv", conteudo)},
                        data={"motivo": "motivo", **form})


def test_endpoint_json(cliente):
    resp = enviar(cliente)
    assert resp.status_code == 200
    assert resp.json()["resumo"]["combinacoes_a_inserir"] == 1 and resp.json()["somente_simulacao"] is True


def test_endpoint_zip(cliente):
    resp = enviar(cliente, formato="zip")
    assert resp.status_code == 200 and resp.headers["content-type"] == "application/zip"
    nomes = zipfile.ZipFile(io.BytesIO(resp.content)).namelist()
    assert {"LEIAME.md", "02_insert_restricoes.sql", "04_rollback.sql", "analise.json"} <= set(nomes)


def test_endpoint_erros(cliente, monkeypatch):
    assert enviar(cliente, motivo="a'b").status_code == 400
    assert enviar(cliente, conteudo=b"CODCLI;CODPLPAG\n10;2\n", formato="zip").status_code == 409

    def falha(c, p):
        raise RuntimeError("ORA-12170 detalhe interno")

    monkeypatch.setattr(restricoes.banco, "coletar", falha)
    resp = enviar(cliente)
    assert resp.status_code == 503 and "detalhe interno" not in resp.text
