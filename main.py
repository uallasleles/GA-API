import logging
from dotenv import load_dotenv
# FastAPI
from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
# Autenticacao
from auth import Auth
from auth.docs_auth import require_docs_session
from auth.docs_auth import router as docs_auth_router
# Admin
from admin.router import router as admin_router
# Rotas
from routers import (
    queries,
    financeiro,
    estoque
)

# Carregar variáveis de ambiente primeiro
load_dotenv()

# Configurar logging antes de outros imports
logging.basicConfig(
    filename='data/ga-api.log',
    filemode='a',
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
# logger = logging.getLogger(__name__)
logger = logging.getLogger()


# Criar aplicação FastAPI
app = FastAPI(
    title="Astória API",
    description="API para integração entre sistemas",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

app.include_router(docs_auth_router)
app.include_router(admin_router)


RAPIDOC_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>__TITLE__ - Docs</title>
  <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
</head>
<body>
  <rapi-doc
    id="doc"
    spec-url="/openapi.json"
    render-style="read"
    show-header="false"
    allow-authentication="true"
    persist-auth="true"
    theme="light"
    primary-color="#0f172a"
  ></rapi-doc>

  <script>
    // O RapiDoc (assim como o Swagger UI) nao transforma parametros
    // "format: date" em <input type="date"> por conta propria -- so faz
    // isso pra campos de requestBody. Aqui a gente busca o schema, acha
    // quais parametros sao "date" e troca o input depois que renderiza.
    (async () => {
      let dateParamNames = new Set();
      try {
        const spec = await (await fetch('/openapi.json')).json();
        for (const path of Object.values(spec.paths || {})) {
          for (const op of Object.values(path)) {
            for (const p of (op.parameters || [])) {
              if (p.schema && p.schema.format === 'date') {
                dateParamNames.add(p.name);
              }
            }
          }
        }
      } catch (e) {
        return;
      }
      if (dateParamNames.size === 0) return;

      function patch(root) {
        root.querySelectorAll('input[data-pname]').forEach((input) => {
          if (dateParamNames.has(input.getAttribute('data-pname')) && input.type !== 'date') {
            input.type = 'date';
          }
        });
        root.querySelectorAll('*').forEach((el) => {
          if (el.shadowRoot) patch(el.shadowRoot);
        });
      }

      const doc = document.getElementById('doc');
      doc.addEventListener('spec-loaded', () => patch(document));
      // fallback: garante que roda mesmo se o evento ja tiver disparado
      [300, 800, 1500, 3000].forEach((ms) => setTimeout(() => patch(document), ms));
    })();
  </script>
</body>
</html>
"""


@app.get("/docs", include_in_schema=False, dependencies=[Depends(require_docs_session)])
async def rapidoc_ui():
    return HTMLResponse(RAPIDOC_HTML.replace("__TITLE__", app.title))


@app.get("/redoc", include_in_schema=False, dependencies=[Depends(require_docs_session)])
async def redoc_ui():
    return get_redoc_html(openapi_url="/openapi.json", title=f"{app.title} - ReDoc")


@app.get("/openapi.json", include_in_schema=False, dependencies=[Depends(require_docs_session)])
async def openapi_schema():
    return get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redireciona para a documentação da API"""
    return RedirectResponse(url="/docs")

# Endpoints WinThor
WINTHOR_PREFIX = "/WinThor"
app.include_router(financeiro.router)
app.include_router(estoque.router)
app.include_router(queries.router,              prefix=WINTHOR_PREFIX, tags=["Queries"])
app.include_router(Auth.router,                 prefix="/Auth", tags=["Authentication"])

# Função principal para execução direta 
async def main():
    """
    Função principal para execução direta do script.
    Nota: A aplicação FastAPI será executada pelo servidor ASGI (uvicorn/gunicorn).
    Esta função é mantida para compatibilidade.
    """ 
    logger.info("Iniciando aplicação GA API...")     
    

if __name__ == "__main__": 
    # Para execução direta (desenvolvimento) 
    import uvicorn 
    uvicorn.run( 
        "main:app",  # Ajuste conforme o nome do arquivo 
        host="0.0.0.0", 
        port=8088, 
        reload=True 
    ) 
