"""Testes do validador/conversor de CSV do RHGestor. Dados 100% sintéticos."""
import pytest

from classes import rhgestor_csv as r
from classes.rhgestor_layouts import COLABORADORES


def linha_colab(**kw):
    base = {c: "" for c in COLABORADORES}
    base.update(CODIGO="4065", NOME="JOAO DA SILVA", ESTADO="BA", CEP="45.000-000",
                NASCIMENTO="01/02/1990", CPF="000.000.000-00", ADMISSAO="10/03/2020",
                SEXO="M", SALARIO_NOMINAL="000000000162100", COD_EMPRESA="65")
    base.update(kw)
    return ";".join(base[c] for c in COLABORADORES)


def csv(*linhas, eol="\n", fim=True):
    cab = ";".join(COLABORADORES)
    return (eol.join([cab, *linhas]) + (eol if fim else "")).encode("utf-8")


def codigos(res, nivel=None):
    return {(p["codigo"], p.get("linha"), p.get("campo")) for p in res["problemas"] if nivel in (None, p["nivel"])}


# ---------- validação
def test_arquivo_valido_sem_erros():
    res = r.validar("colaboradores", csv(linha_colab(), linha_colab(CODIGO="1")))
    assert res["valido"] and res["total_erros"] == 0 and res["linhas"] == 2


def test_cabecalho_errado_e_colunas():
    res = r.validar("colaboradores", b"A;B;C\n1;2;3\n")
    assert not res["valido"]
    assert any(p["codigo"] == "CABECALHO" for p in res["problemas"])
    res = r.validar("colaboradores", csv(linha_colab() + ";X"))
    assert ("COLUNAS", 2, None) in codigos(res)


def test_separador_errado():
    res = r.validar("colaboradores", b"CODIGO,NOME,ENDERECO\n1,2,3\n")
    assert any(p["codigo"] == "SEPARADOR" for p in res["problemas"])


def test_nao_utf8():
    res = r.validar("colaboradores", csv(linha_colab(NOME="JOÃO")).replace("Ã".encode(), b"\xc3"))
    assert res["problemas"][0]["codigo"] == "ENCODING"


def test_codigo_duplicado_nao_numerico_e_grande():
    res = r.validar("colaboradores", csv(linha_colab(CODIGO="5"), linha_colab(CODIGO="5"),
                                         linha_colab(CODIGO="A1"), linha_colab(CODIGO="12345678901")))
    c = codigos(res, "erro")
    assert ("CODIGO_DUPLICADO", 3, "CODIGO") in c
    assert ("CODIGO", 4, "CODIGO") in c and ("CODIGO", 5, "CODIGO") in c


def test_datas_sexo_tamanho():
    res = r.validar("colaboradores", csv(linha_colab(NASCIMENTO="31/02/1990", ADMISSAO="1990-01-01",
                                                      SEXO="X", ESTADO="BAH")))
    c = codigos(res, "erro")
    assert ("DATA", 2, "NASCIMENTO") in c and ("DATA", 2, "ADMISSAO") in c
    assert ("SEXO", 2, "SEXO") in c and ("TAMANHO", 2, "ESTADO") in c


def test_alertas_nao_invalidam():
    res = r.validar("colaboradores", csv(linha_colab(NOME="JOÃO", SALARIO_NOMINAL="1621,00", CEP="45000000",
                                                      CPF="00000000000", CELULAR="73999999999")))
    assert res["valido"]
    c = codigos(res, "alerta")
    assert {("ACENTO", 2, "NOME"), ("SALARIO_FORMATO", 2, "SALARIO_NOMINAL"), ("CEP_FORMATO", 2, "CEP"),
            ("CPF_FORMATO", 2, "CPF"), ("FONE_FORMATO", 2, "CELULAR")} <= c


@pytest.mark.parametrize("layout,n", [("ferias", 19), ("atestados", 13), ("financeiro", 34)])
def test_outros_layouts_cabecalho_e_colunas(layout, n):
    cab = ";".join(r.LAYOUTS[layout][1])
    ok = r.validar(layout, f"{cab}\n{';'.join([''] * n)}\n".encode())
    assert ok["valido"]
    ruim = r.validar(layout, f"{cab}\n{';'.join([''] * (n - 1))}\n".encode())
    assert ("COLUNAS", 2, None) in codigos(ruim)


# ---------- conversão
def test_converter_codigo_acentos_salario_e_superior():
    entrada = csv(linha_colab(CODIGO="4065", COD_EMPRESA="65", NOME="JOÃO AÇÃO", SALARIO_NOMINAL="1621,00",
                              MINIMO_GARANTIDO="", MEDIA_GANHO_VARIAVEIS="1.234,5", SUPERIOR_IMEDIATO="10"))
    saida, alt = r.converter_colaboradores(entrada)
    linhas = saida.decode().split("\n")
    assert linhas[0] == ";".join(COLABORADORES)
    d = dict(zip(COLABORADORES, linhas[1].split(";")))
    assert d["CODIGO"] == "0650004065" and d["SUPERIOR_IMEDIATO"] == "0650000010"
    assert d["NOME"] == "JOAO ACAO"
    assert d["SALARIO_NOMINAL"] == "000000000162100"
    assert d["MINIMO_GARANTIDO"] == ""
    assert d["MEDIA_GANHO_VARIAVEIS"] == "000000000123450"
    assert d["CPF"] == "000.000.000-00" and d["CEP"] == "45.000-000"  # não convertidos
    assert {a["campo"]: a["valores_alterados"] for a in alt}["CODIGO"] == 1


def test_converter_superior_vazio_continua_vazio():
    saida, _ = r.converter_colaboradores(csv(linha_colab()))
    assert dict(zip(COLABORADORES, saida.decode().split("\n")[1].split(";")))["SUPERIOR_IMEDIATO"] == ""


@pytest.mark.parametrize("eol,fim", [("\n", True), ("\r\n", True), ("\r\n", False), ("\n", False)])
def test_converter_preserva_fim_de_linha(eol, fim):
    saida, _ = r.converter_colaboradores(csv(linha_colab(), linha_colab(CODIGO="9"), eol=eol, fim=fim))
    esperado_crlf = (2 + (1 if fim else 0)) if eol == "\r\n" else 0
    assert saida.count(b"\r\n") == esperado_crlf
    assert saida.endswith(eol.encode()) == fim
    assert not saida.startswith(b"\xef\xbb\xbf")


def test_converter_arquivo_ja_convertido_da_erro():
    saida, _ = r.converter_colaboradores(csv(linha_colab()))
    with pytest.raises(r.ErroConversao):  # CODIGO já com 10 dígitos
        r.converter_colaboradores(saida)


def test_converter_erros():
    with pytest.raises(r.ErroConversao) as e:
        r.converter_colaboradores(csv(linha_colab(CODIGO="A1")))
    assert e.value.problemas[0]["campo"] == "CODIGO"
    with pytest.raises(r.ErroConversao) as e:  # duplicado após concatenar (mesma empresa e código)
        r.converter_colaboradores(csv(linha_colab(CODIGO="7"), linha_colab(CODIGO="7")))
    assert e.value.problemas[0]["codigo"] == "CODIGO_DUPLICADO"
    # mesmo CODIGO em empresas diferentes NÃO é duplicado
    saida, _ = r.converter_colaboradores(csv(linha_colab(CODIGO="7", COD_EMPRESA="1"), linha_colab(CODIGO="7", COD_EMPRESA="2")))
    assert b"0010000007" in saida and b"0020000007" in saida


@pytest.mark.parametrize("entrada,saida", [
    ("1621,00", "000000000162100"), ("2.123,45", "000000000212345"), ("1621", "000000000162100"),
    ("", ""), ("000000000162100", "000000000162100"), ("1621.5", "000000000162150"),
])
def test_converter_salario(entrada, saida):
    assert r.converter_salario(entrada) == saida


def test_salario_invalido():
    for ruim in ("abc", "-5,00", "99999999999999,99"):
        with pytest.raises(ValueError):
            r.converter_salario(ruim)


def test_remover_acentos():
    assert r.remover_acentos("AÇÃO JOÃO ÁÉÍÓÚ ñ º") == "ACAO JOAO AEIOU n o"
