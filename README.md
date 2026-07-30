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

## Deploy no Swarm

A stack (`docker-compose.yml`) sobe dois serviços:

- `ga-api`: a aplicação, sem publicar a porta 8088 no host — exposta apenas via Traefik (`Host(gaapi.grupoastoria.com.br)`, `letsencryptresolver`).
- `postgres`: banco de dados da aplicação (usuários/credenciais), acessível só pela rede interna `ga_api_internal`, com volume nomeado `ga_api_pgdata` para persistência.

`ga-api` se conecta à rede externa `network_public` (nome real do Docker: `minha_rede`), já usada pelo Traefik. O label `traefik.docker.network=minha_rede` usa o nome real da rede (necessário porque o serviço está em duas redes — a pública e a interna do Postgres — e o Traefik precisa saber qual delas usar).

1. Buildar e publicar a imagem em um registry acessível pela VM (ou buildar direto na VM/manager node):
   ```bash
   docker build -t ga-api:latest .
   ```
2. Garantir que o arquivo `.env` (baseado no `.env.example`) esteja na mesma pasta do `docker-compose.yml` no manager node — o `docker stack deploy` usa esse `.env` para interpolar as variáveis `${...}` do compose. (Alternativa: colar as mesmas variáveis na tela de "Environment variables" do stack no Portainer.)
3. Deploy:
   ```bash
   docker stack deploy -c docker-compose.yml ga-api
   ```

Para rodar migrations manualmente (ex.: depois de alterar modelos), sem esperar o próximo redeploy:
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
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Credenciais do Postgres da aplicação (usuários) |
| `DATABASE_URL` | Montada automaticamente no `docker-compose.yml` a partir das variáveis `POSTGRES_*` |

> `ORACLE_HOME`, `LD_LIBRARY_PATH`, `ORACLEDB_INSTANT_CLIENT_DIR` e as variáveis `DCN_*` não são usadas por este serviço (só por processos separados de listener/worker que não fazem parte desta imagem).

## Usuários

Os usuários antes hardcoded em `auth/Auth.py` (`fake_users_db`) agora vivem na tabela `user` do Postgres, criada e semeada pela migration Alembic (`alembic/versions/0002_seed_users.py`) com os mesmos hashes de senha já existentes. Para criar/alterar usuários depois do deploy, use uma sessão SQLModel contra o Postgres da stack (ou uma nova migration).
