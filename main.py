import logging
from dotenv import load_dotenv
# FastAPI
from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
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


@app.get("/docs", include_in_schema=False, dependencies=[Depends(require_docs_session)])
async def swagger_ui():
    return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{app.title} - Docs")


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
