"""Testes do router /RHGestor com a API da Sólides simulada (nada sai da máquina)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from auth.Auth import User, get_current_user
from auth.database import get_session
from auth.models.rhgestor import RHGestorEnvioDB
from classes.rhgestor_layouts import COLABORADORES
from routers import rhgestor

SEGREDO = "chave-secreta-de-teste"


class Resp:
    def __init__(self, code, body):
        self.status_code, self._b = code, body
        self.ok = 200 <= code < 300
        self.text = str(body)

    def json(self):
        return self._b


@pytest.fixture
def ctx(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine, tables=[RHGestorEnvioDB.__table__])
    app = FastAPI()
    app.include_router(rhgestor.router)

    def sessao():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = sessao
    app.dependency_overrides[get_current_user] = lambda: User(username="carlos", scopes=["rhgestor:importar"])
    monkeypatch.setenv("RHGESTOR_EMAIL_TESTE", "t@exemplo.com")
    monkeypatch.setenv("RHGESTOR_KEY_TESTE", SEGREDO)
    monkeypatch.delenv("RHGESTOR_EMAIL_PRODUCAO", raising=False)
    monkeypatch.delenv("RHGESTOR_KEY_PRODUCAO", raising=False)
    chamadas = []

    def post(url, **kw):
        chamadas.append((url, kw))
        if url.endswith("/api/auth"):
            return Resp(200, {"Status": None, "Data": {"Token": "tok"}, "Message": None})
        return Resp(200, {"Status": "success", "Data": None, "Message": "Arquivo enviado com sucesso"})

    monkeypatch.setattr(rhgestor.requests, "post", post)
    return TestClient(app), chamadas


def csv_bytes():
    cab = ";".join(COLABORADORES)
    d = {c: "" for c in COLABORADORES}
    d.update(CODIGO="4065", COD_EMPRESA="65", SEXO="M", NOME="JOÃO")
    return (cab + "\r\n" + ";".join(d[c] for c in COLABORADORES) + "\r\n").encode()


def test_importar_repassa_arquivo_sem_alterar_e_grava_historico(ctx):
    client, chamadas = ctx
    conteudo = csv_bytes()
    r = client.post("/RHGestor/Importar/colaboradores", files={"file": ("c.csv", conteudo, "text/csv")})
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["sucesso"] and corpo["codigo_layout"] == "101" and corpo["linhas"] == 1
    assert SEGREDO not in r.text
    url, kw = chamadas[1]
    assert url.endswith("/api/fileimport") and kw["data"] == {"layout": "101"}
    assert kw["files"]["file"][1] == conteudo  # idêntico
    assert kw["headers"]["Authorization"] == "Bearer tok"
    h = client.get("/RHGestor/Historico").json()
    assert len(h) == 1 and h[0]["usuario"] == "carlos" and h[0]["ambiente"] == "teste" and h[0]["sucesso"]
    assert SEGREDO not in str(h)


def test_importar_com_converter(ctx):
    client, chamadas = ctx
    r = client.post("/RHGestor/Importar/colaboradores?converter=true", files={"file": ("c.csv", csv_bytes(), "text/csv")})
    assert r.status_code == 200
    enviado = chamadas[1][1]["files"]["file"][1]
    assert b"0650004065" in enviado and b"JOAO" in enviado and b"\r\n" in enviado
    assert r.json()["conversao"]["aplicada"]


def test_converter_so_colaboradores(ctx):
    client, _ = ctx
    r = client.post("/RHGestor/Importar/ferias?converter=true", files={"file": ("f.csv", b"x\n", "text/csv")})
    assert r.status_code == 400


def test_producao_sem_credencial_erro_claro(ctx):
    client, chamadas = ctx
    r = client.post("/RHGestor/Importar/colaboradores?ambiente=producao", files={"file": ("c.csv", csv_bytes(), "text/csv")})
    assert r.status_code == 400 and "producao" in r.json()["detail"] and not chamadas


def test_falha_na_solides_vira_502_e_historico(ctx, monkeypatch):
    client, _ = ctx
    monkeypatch.setattr(rhgestor.requests, "post", lambda url, **kw: Resp(401, {"Message": "credencial inválida"}))
    r = client.post("/RHGestor/Importar/colaboradores", files={"file": ("c.csv", csv_bytes(), "text/csv")})
    assert r.status_code == 502 and not r.json()["sucesso"]
    assert SEGREDO not in r.text
    assert client.get("/RHGestor/Historico?sucesso=false").json()[0]["http_status"] == 401


def test_validar_nao_envia(ctx):
    client, chamadas = ctx
    r = client.post("/RHGestor/Validar/colaboradores", files={"file": ("c.csv", csv_bytes(), "text/csv")})
    assert r.status_code == 200 and r.json()["valido"] and not chamadas
    assert client.get("/RHGestor/Historico").json() == []
