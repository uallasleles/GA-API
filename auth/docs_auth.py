import hashlib
import hmac
import os
import time

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

DOCS_USERNAME = os.getenv("DOCS_USERNAME")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")
DOCS_SESSION_SECRET = os.getenv("DOCS_SESSION_SECRET")

COOKIE_NAME = "docs_session"
SESSION_MAX_AGE = 8 * 60 * 60  # 8 horas

router = APIRouter(include_in_schema=False)

LOGIN_PAGE = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Astória API &middot; Login</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: linear-gradient(160deg, #0f172a, #1e293b);
    padding: 24px;
  }}
  .card {{
    width: 100%;
    max-width: 360px;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
    padding: 32px 28px;
  }}
  .card h1 {{
    margin: 0 0 4px;
    font-size: 1.25rem;
    color: #0f172a;
  }}
  .card p.subtitle {{
    margin: 0 0 24px;
    font-size: 0.875rem;
    color: #64748b;
  }}
  label {{
    display: block;
    font-size: 0.8rem;
    font-weight: 600;
    color: #334155;
    margin-bottom: 6px;
  }}
  input {{
    width: 100%;
    padding: 10px 12px;
    margin-bottom: 16px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.95rem;
  }}
  input:focus {{
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
  }}
  button {{
    width: 100%;
    padding: 10px 12px;
    border: none;
    border-radius: 8px;
    background: #0f172a;
    color: #fff;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
  }}
  button:hover {{ background: #1e293b; }}
  .error {{
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #b91c1c;
    font-size: 0.85rem;
    padding: 10px 12px;
    border-radius: 8px;
    margin-bottom: 16px;
  }}
</style>
</head>
<body>
  <div class="card">
    <h1>Astória API</h1>
    <p class="subtitle">Acesso à documentação (/docs)</p>
    {error}
    <form method="post" action="/docs-login">
      <label for="username">Usuário</label>
      <input id="username" name="username" type="text" autocomplete="username" required autofocus>
      <label for="password">Senha</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required>
      <button type="submit">Entrar</button>
    </form>
  </div>
</body>
</html>
"""


def _sign(value: str) -> str:
    mac = hmac.new(DOCS_SESSION_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{mac}"


def _verify(token: str) -> bool:
    try:
        issued_at, mac = token.rsplit(".", 1)
    except ValueError:
        return False
    expected = hmac.new(DOCS_SESSION_SECRET.encode(), issued_at.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, expected):
        return False
    try:
        return (time.time() - int(issued_at)) < SESSION_MAX_AGE
    except ValueError:
        return False


async def require_docs_session(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token or not _verify(token):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/docs-login"},
        )


@router.get("/docs-login", response_class=HTMLResponse)
async def docs_login_form():
    return LOGIN_PAGE.format(error="")


@router.post("/docs-login")
async def docs_login_submit(username: str = Form(...), password: str = Form(...)):
    valid = (
        hmac.compare_digest(username, DOCS_USERNAME or "")
        and hmac.compare_digest(password, DOCS_PASSWORD or "")
    )
    if not valid:
        error_html = '<p class="error">Usuário ou senha inválidos.</p>'
        return HTMLResponse(LOGIN_PAGE.format(error=error_html), status_code=status.HTTP_401_UNAUTHORIZED)

    token = _sign(str(int(time.time())))
    response = RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
    )
    return response
