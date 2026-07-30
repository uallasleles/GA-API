> Na interface da API as operações ficam sempre visíveis mesmo que o usuário não esteja autenticado?
___

**Sim, por padrão, sim.** No FastAPI, toda a documentação interativa (Swagger UI, que fica em `/docs`, e o ReDoc, em `/redoc`) é **pública** e exibe todas as rotas e operações, independentemente de o usuário estar logado ou não.

---

### 🛡️ O que muda com a autenticação?

Embora qualquer visitante consiga **ver** quais endpoints existem, quais parâmetros eles aceitam e o que eles respondem (os schemas), a autenticação dita quem pode **executar** essas operações com sucesso.

* **Sem autenticação:** Se um usuário tentar testar uma rota protegida pelo Swagger (clicando em *Try it out* e *Execute*), a API responderá com um erro `401 Unauthorized` ou `403 Forbidden`.
* **Com autenticação:** O usuário clica no botão **Authorize** (o cadeado no topo da página), insere suas credenciais (ou token), e a partir daí o Swagger envia o cabeçalho `Authorization` correto, permitindo a execução bem-sucedida das rotas autorizadas.

---

### 🔒 Como esconder as operações ou a documentação?

Se o seu objetivo é fazer com que pessoas não autorizadas sequer saibam que essas rotas existem, você tem duas abordagens principais:

#### 1. Esconder endpoints específicos da documentação

Você pode manter a documentação pública, mas ocultar rotas sensíveis (como painéis administrativos) adicionando o parâmetro `include_in_schema=False` diretamente no decorador da rota:

```python
@app.get("/admin/dados-sensiveis", include_in_schema=False)
async def read_sensitive_data():
    return {"secret": "apenas admins deveriam saber que esta rota existe"}

```

#### 2. Proteger toda a página do Swagger (`/docs`)

Se você quer que apenas usuários autenticados consigam abrir a página do Swagger, você precisa desabilitar a documentação padrão do FastAPI e recriá-la atrás de uma rota protegida por senha.

Aqui está um exemplo prático de como fazer isso:

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(docs_url=None, redoc_url=None) # Desabilita as rotas públicas padrões
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    # Exemplo simples com HTTP Basic Auth para proteger a página
    correct_username = "admin"
    correct_password = "supersecretpassword"
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorreto username ou password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Nova rota do Swagger, agora protegida!
@app.get("/docs", include_in_schema=False)
async def Kohls_custom_swagger_ui(username: str = Depends(get_current_username)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs Protegida")

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(username: str = Depends(get_current_username)):
    from fastapi.openapi.utils import get_openapi
    return get_openapi(title="Minha API", version="1.0.0", routes=app.routes)

```

Dessa forma, sempre que alguém tentar acessar `/docs`, o navegador abrirá um pop-up pedindo usuário e senha antes de renderizar a interface e expor as operações da sua API.