No FastAPI, o controle de permissões de um usuário é feito utilizando o sistema OAuth2 com Escopos (Scopes). Um escopo é apenas uma string (ex: `"users:read"`, `"items:write"`, `"admin"`) que representa uma permissão específica. O fluxo envolve definir a permissão no token JWT, extraí-la e exigi-la nos endpoints.

Abaixo está o passo a passo prático para implementar essa lógica na sua API:
___

1. Definir os Escopos e as Regras da Aplicação
Primeiro, você declara os escopos válidos e a chave que assina os tokens na sua configuração do OAuth2. O FastAPI integra esses escopos nativamente na documentação do OpenAPI (`/docs`).

---

```python
from fastapi import FastAPI, Depends, Security, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import BaseModel
from typing import List

# 1. Definir os escopos que existem na sua aplicação
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "items:read": "Permissão para visualizar itens",
        "items:write": "Permissão para criar/editar itens",
        "admin": "Permissão de administrador total",
    }
)

app = FastAPI()
```

---

2. Criar o Modelo de Usuário e Permissões
Quando você cria ou busca o usuário no banco de dados, você deve associar uma lista de escopos a ele.


---

```python
class Usuario(BaseModel):
    username: str
    email: str
    scopes: List[str] # Ex: ["items:read", "items:write"]
```

---

3. Criar a Dependência para Validar o Usuário e Escopos
A função que valida o usuário atual deve receber um `SecurityScopes`. Ela verifica se o usuário autenticado possui os escopos necessários para executar a ação que está tentando acessar.

---

```python
async def get_current_user(
    security_scopes: SecurityScopes, 
    token: str = Depends(oauth2_scheme)
):
    # Aqui você decodifica o JWT e busca o usuário no banco
    # Simulando um usuário com permissões:
    usuario_autenticado = Usuario(
        username="joao", 
        email="joao@exemplo.com", 
        scopes=["items:read", "items:write"] # Escopos do usuário salvo
    )
    
    # Valida se o endpoint exige escopos e se o usuário os possui
    for scope in security_scopes.scopes:
        if scope not in usuario_autenticado.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão negada: escopo insuficiente",
                headers={"WWW-Authenticate": f"Bearer scope=\"{security_scopes.scope_str}\""}
            )
    
    return usuario_autenticado
```

---

4. Proteger os Endpoints (Definindo Permissões)
Para proteger uma rota e definir exatamente quais permissões são exigidas, utilize `Security()` ao invés de `Depends()`, passando os escopos no argumento `scopes`.

---

```python
# Qualquer usuário autenticado (autenticação base, sem exigir escopo específico)
@app.get("/users/me")
async def read_own_me(current_user: Usuario = Depends(get_current_user)):
    return current_user

# Exige a permissão "items:read"
@app.get("/items/")
async def read_items(current_user: Usuario = Security(get_current_user, scopes=["items:read"])):
    return {"message": "Lista de itens", "usuario": current_user.username}

# Exige a permissão "items:write"
@app.post("/items/")
async def create_item(current_user: Usuario = Security(get_current_user, scopes=["items:write"])):
    return {"message": "Item criado", "usuario": current_user.username}
```

---