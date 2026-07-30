import logging
from dotenv import load_dotenv
# FastAPI
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
# Autenticacao
from auth import Auth
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
    version="1.0.0"
)
# app = FastAPI(docs_url=None, redoc_url=None)
# security = HTTPBasic()

# def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
#     # Exemplo simples com HTTP Basic Auth para proteger a página
#     correct_username = "admin"
#     correct_password = "<definir via variável de ambiente>"
#     if credentials.username != correct_username or credentials.password != correct_password:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorreto username ou password",
#             headers={"WWW-Authenticate": "Basic"},
#         )
#     return credentials.username

# # Nova rota do Swagger, agora protegida!
# @app.get("/docs", include_in_schema=False)
# async def Kohls_custom_swagger_ui(username: str = Depends(get_current_username)):
#     return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs Protegida")

# @app.get("/openapi.json", include_in_schema=False)
# async def get_open_api_endpoint(username: str = Depends(get_current_username)):
#     from fastapi.openapi.utils import get_openapi
#     return get_openapi(title="Minha API", version="1.0.0", routes=app.routes)

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
