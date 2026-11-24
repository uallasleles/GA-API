# Envio de CSVs ao RHGestor (Sólides)

Router `routers/rhgestor.py` (prefixo `/RHGestor`, tag **RHGestor**). Envia arquivos `.csv` à API própria da Sólides (`POST /api/fileimport`), valida antes de enviar e guarda o histórico no Postgres. Lógica de validação/conversão em `classes/rhgestor_csv.py`; cabeçalhos oficiais em `classes/rhgestor_layouts.py`.

## Permissão

Escopo **`rhgestor:importar`** (catálogo em `auth/scopes.py`). Cobre as três rotas. Para dar acesso a um usuário restrito (ex.: contabilidade), crie em `/admin` um papel só com esse escopo e atribua ao usuário. Papéis existentes (ex.: Admin) **não** ganham o escopo sozinhos: adicione-o no `/admin`.

A documentação `/docs` já fica atrás de login próprio (ver `docs/api-doc-visibilidade.md`); o projeto não filtra operações por escopo, então o Swagger mostra as rotas a quem logar nele, mas só executa com o escopo.

## Credenciais (somente variáveis de ambiente)

| Variável | Uso |
|---|---|
| `RHGESTOR_EMAIL_TESTE`, `RHGESTOR_KEY_TESTE` | base de testes (padrão de `ambiente`) |
| `RHGESTOR_EMAIL_PRODUCAO`, `RHGESTOR_KEY_PRODUCAO` | base de produção; sem elas, `ambiente=producao` devolve 400 |
| `RHGESTOR_BASE_URL` | opcional; padrão `https://apisecure.rhgestor.com.br` (a mesma URL serve teste e produção: quem decide a base é a credencial) |

Local: preencha o `.env` (ignorado pelo git). Produção: cadastre as variáveis na stack do Portainer. A chave nunca é gravada em log, resposta ou histórico.

## Rotas

Layouts: `colaboradores` (101), `ferias` (202), `atestados` (303), `financeiro` (404).

### `POST /RHGestor/Validar/{layout}` — não envia nada
Multipart com `file`. Devolve `valido`, `linhas`, `total_erros`, `total_alertas`, `resumo` (contagem por tipo) e `problemas` (`nivel` erro/alerta, `codigo`, `linha`, `campo`, `mensagem`; até 1000, `truncado` indica corte). Linha 1 é o cabeçalho.

- Todos os layouts: UTF-8, separador `;`, cabeçalho idêntico ao guia, número de colunas por linha.
- `colaboradores`: CODIGO numérico, ≤10 dígitos e único; datas `dd/mm/aaaa` válidas; SEXO `M`/`F`; tamanhos máximos de `explic_colab.txt` (erros). **Alertas:** acentos, salário fora de 15 dígitos, CEP/CPF fora do formato pontuado, telefone só com dígitos, BOM.
- `converter=true` (só colaboradores): valida o arquivo já convertido e lista o que mudou.

### `POST /RHGestor/Importar/{layout}?ambiente=teste|producao&converter=false`
Multipart com `file`. Autentica na Sólides, envia `layout` + `file` sem alterar o arquivo e devolve a resposta dela em `resposta_solides` (200 se a Sólides respondeu `success`; 502 caso contrário). A Sólides não informa linhas nem erros por linha — valide antes. Não bloqueia por erros de validação.

### `GET /RHGestor/Historico?layout=&ambiente=&sucesso=&limit=50&offset=0`
Mais recentes primeiro: data/hora, usuário, layout, ambiente, arquivo, tamanho, linhas, convertido, HTTP status, sucesso e mensagem. Tabela `rhgestor_envio` (migração `0004`, aplicada pelo `entrypoint.sh` no próximo deploy).

## Conversões (`converter=true`, desligadas por padrão, só colaboradores)

1. **CODIGO** e **SUPERIOR_IMEDIATO** (se preenchido): `COD_EMPRESA` com 3 dígitos + código com 7 dígitos, zeros à esquerda (`65` + `4065` → `0650004065`). O superior usa o `COD_EMPRESA` da própria linha. Erro (422, nada é enviado) se não numérico, se o arquivo já parecer convertido (código >7 ou empresa >3 dígitos) ou se houver CODIGO duplicado após concatenar.
2. **Acentos** removidos de todos os campos (NFKD sem marcas combinantes).
3. **SALARIO_NOMINAL, MINIMO_GARANTIDO, MEDIA_GANHO_VARIAVEIS**: `1621,00` → `000000000162100`; vazio continua vazio.

Não converte CEP, CPF, telefone nem CNPJ (aguardando orientação da Sólides). Preserva cabeçalho, ordem, `;`, UTF-8 sem BOM e o tipo de quebra de linha. A resposta traz `conversao.alteracoes` (campo, regra, quantidade).

## Testes

```powershell
uv run pytest
```

Usam só CSV sintético e a Sólides simulada (nenhum envio real).
