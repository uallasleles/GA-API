# GA API

API FastAPI de integração entre o ERP (Oracle/WinThor) e sistemas parceiros, com autenticação JWT e usuários persistidos em PostgreSQL.

## Build e teste local (Docker)

```bash
cp .env.example .env
# preencher .env com os valores reais
docker build -t ga-api:latest .
```

Para testar localmente com um Postgres descartável:

```bash
docker network create ga_api_test_net
docker run -d --name ga-api-postgres --network ga_api_test_net \
  -e POSTGRES_USER=ga_api -e POSTGRES_PASSWORD=ga_api -e POSTGRES_DB=ga_api \
  postgres:16-alpine

docker run --rm -p 8088:8088 --network ga_api_test_net \
  --env-file .env \
  -e DATABASE_URL=postgresql+psycopg://ga_api:ga_api@ga-api-postgres:5432/ga_api \
  ga-api:latest
```

Acesse `http://localhost:8088/docs`. O `entrypoint.sh` roda `alembic upgrade head` (cria a tabela `user` e semeia os usuários existentes) antes de subir o Uvicorn.

## CI/CD

Todo push na branch `main` dispara o workflow [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml), que builda a imagem e publica em `ghcr.io/uallasleles/ga-api` com as tags `latest` e `sha-<commit curto>`. Não precisa de nenhum secret adicional — usa o `GITHUB_TOKEN` automático da Action.

Na primeira publicação, o pacote é criado como **privado** por padrão em `github.com/uallasleles?tab=packages`. Para o Portainer conseguir dar `docker pull`, é preciso cadastrar essa registry no Portainer (**Registries → Add registry → GitHub Container Registry**) com um Personal Access Token (`read:packages`) — ou tornar o pacote público em suas configurações no GitHub.

## Deploy (via Portainer)

O deploy desta stack é gerenciado pelo Portainer, não por `docker stack deploy` direto na linha de comando. Mesmo padrão usado na stack RepomFrete: Action builda e publica a imagem, Portainer só dá "Pull and redeploy".

A stack (`docker-compose.yml`) sobe dois serviços:

- `ga-api`: a aplicação, sem publicar a porta 8088 no host — exposta apenas via Traefik (`Host(gaapi.grupoastoria.com.br)`, `letsencryptresolver`). Usa a imagem `ghcr.io/uallasleles/ga-api:latest`.
- `postgres`: banco de dados da aplicação (usuários/credenciais), acessível só pela rede interna `ga_api_internal`, com volume nomeado `ga_api_pgdata` para persistência.

`ga-api` se conecta à rede externa `network_public` (nome real do Docker: `minha_rede`), já usada pelo Traefik. O label `traefik.docker.network=minha_rede` usa o nome real da rede (necessário porque o serviço está em duas redes — a pública e a interna do Postgres — e o Traefik precisa saber qual delas usar).

**Primeiro deploy:**
1. Garantir que o workflow já rodou pelo menos uma vez (push na `main`) e que o registry GHCR está cadastrado no Portainer (ver seção CI/CD acima).
2. No Portainer, **Stacks → Add stack**:
   - **Repository**: apontar para este repositório Git (`https://github.com/uallasleles/GA-API`), arquivo `docker-compose.yml`; ou colar o conteúdo do compose diretamente.
   - **Environment variables**: preencher todas as variáveis listadas em [.env.example](.env.example) (o Portainer não lê o `.env` do repositório — as variáveis são cadastradas na própria UI da stack).
3. **Deploy the stack**.

**Redeploys seguintes** (depois de um novo push/merge na `main`): esperar o workflow do GitHub Actions terminar de publicar a imagem, então no Portainer ir em **Stacks → ga-api → Pull and redeploy**.

Para rodar migrations manualmente (ex.: depois de alterar modelos), sem esperar o próximo redeploy — via **Containers → ga-api → Console** no Portainer, ou por SSH:
```bash
docker exec -it $(docker ps -qf name=ga-api_ga-api) alembic upgrade head
```

## Variáveis de ambiente

Ver [.env.example](.env.example) para a lista completa. Resumo:

| Variável | Descrição |
|---|---|
| `API_BASE_URL`, `API_SERVER`, `API_GRANT_TYPE`, `API_VERSION`, `API_TIMEOUT` | Configuração da API Repom (produção) |
| `API_USERNAME_*`, `API_PASSWORD_*`, `API_PARTNER_*` (Chocosul/Mastter/LazaroLog) e `API_USERNAME`/`API_PASSWORD`/`API_PARTNER` (fallback) | Credenciais por parceiro |
| `ORACLEDB_USERNAME`, `ORACLEDB_PASSWORD`, `ORACLEDB_DSN` | Conexão com o Oracle (ERP WinThor), modo thin — não requer Instant Client |
| `LOGGER_API_URL`, `LOGGER_API_KEY` | API de logging externa |
| `JWT_SECRET_KEY` | Chave de assinatura dos tokens JWT — gerar com `openssl rand -hex 32` |
| `MYAPI_ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do token de acesso, em minutos |
| `DOCS_USERNAME`, `DOCS_PASSWORD` | Credenciais de acesso à página de login de `/docs` e `/openapi.json` |
| `DOCS_SESSION_SECRET` | Chave de assinatura do cookie de sessão do login de `/docs` — gerar com `openssl rand -hex 32` |
| `ADMIN_SESSION_SECRET` | Chave de assinatura do cookie de sessão do painel `/admin` — gerar com `openssl rand -hex 32` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Credenciais do Postgres da aplicação (usuários) |
| `DATABASE_URL` | Montada automaticamente no `docker-compose.yml` a partir das variáveis `POSTGRES_*` |

> `ORACLE_HOME`, `LD_LIBRARY_PATH`, `ORACLEDB_INSTANT_CLIENT_DIR` e as variáveis `DCN_*` não são usadas por este serviço (só por processos separados de listener/worker que não fazem parte desta imagem).

## Documentação (/docs)

`/docs` e `/openapi.json` ficam atrás de uma tela de login própria (`/docs-login`) — cookie de sessão assinado, válido por 8h, credenciais fixas em `DOCS_USERNAME`/`DOCS_PASSWORD` (não tem relação com os usuários do Postgres nem com o fluxo de token via `/Auth/token`, que continua público e sem essa proteção). Ver [auth/docs_auth.py](auth/docs_auth.py).

## Usuários e permissões (/admin)

Os usuários antes hardcoded em `auth/Auth.py` (`fake_users_db`) agora vivem na tabela `user` do Postgres. Permissões não são mais uma lista de scopes por usuário — são atribuídas via **papéis (roles)**: cada papel tem um conjunto de scopes, e cada usuário tem um ou mais papéis. Os scopes efetivos de um usuário são a união dos scopes de todos os seus papéis (calculado em `auth/Auth.py:get_user`).

Gerenciamento é feito pelo painel `/admin` (`GET /admin/users`, `GET /admin/roles`) — login com uma conta do Postgres que tenha o scope `admin` (ex.: `uallasleles`, já semeado com o papel "Admin" pela migration `0003_roles_and_permissions`). O painel permite:
- Criar usuários, definir senha, bloquear/desbloquear login (campo `disabled`) e atribuir papéis.
- Criar/editar papéis e escolher quais scopes (do catálogo em `auth/scopes.py`) cada um concede.

Sessão do `/admin` é independente da sessão do `/docs-login` e do token JWT usado pelos clientes da API — são três mecanismos de autenticação separados, cada um com seu próprio cookie/segredo.
