# Restrições de venda (rotina 391) — simulação

`POST /Vendas/restricoes/simular` — escopo `restricao:read`.

Confere uma lista de clientes e prazos contra o ERP e gera os scripts para incluir as restrições na tabela `CHOCOSUL.PCRESTRICAOVENDA`. **A API não grava nada no Oracle**: os scripts são revisados e executados manualmente. A inclusão e a reversão pela própria API ficam para uma segunda fase.

## Entrada (`multipart/form-data`)

| Campo | Obrigatório | Descrição |
|---|---|---|
| `file` | sim | `.xlsx` (primeira aba) ou `.csv` (`;`, `,` ou tabulação), até 5 MB |
| `motivo` | sim | Até 50 caracteres; é convertido para maiúsculas sem acentos. Aceita letras, números, espaço e `. , / ( ) _ + -` |
| `prazos` | não | Ex.: `2,13,14`. Vale para todos os clientes e substitui a coluna da planilha |
| `origem` | não | `O` Todas (padrão), `T` Telemarketing, `B` Balcão, `R` Balcão Reserva, `C` Call Center, `F` Força de Vendas, `W` Web |
| `somente_ativos` | não | Deixa de fora os clientes inativos (padrão: não) |
| `formato` | não | `json` (padrão) ou `zip` |

Colunas aceitas na planilha:

- cliente: `CODCLI`, `CÓDIGO DO CLIENTE`, `CLIENTE` ou `CÓDIGO`;
- prazos (se `prazos` não for informado): `CODPLPAG`, `CÓDIGO PRAZO`, `PRAZO(S)` ou `PLANO(S)`, com um ou vários códigos por célula (`2, 13, 14`).

Limite de 10.000 combinações de cliente e prazo por arquivo. Nenhuma restrição é gerada sem cliente e sem prazo.

## Saída

`formato=json` devolve:

- `resumo`: contagens, combinações já cobertas e a inserir;
- `alertas`: clientes inexistentes, inativos ou bloqueados, prazos inexistentes ou inativos, restrições sem cliente, origem diferente de Todas e outros prazos parcelados;
- `a_inserir`, `clientes`, `prazos`, `restricoes_parciais`, `restricoes_sem_cliente`;
- `uso_12_meses`: pedidos não cancelados desses clientes por prazo;
- `outros_prazos_parcelados`: prazos ativos com duas ou mais parcelas fora da lista;
- `assinatura`: impressão digital do que seria gravado (a segunda fase vai exigir a mesma).

`formato=zip` devolve os mesmos dados (`analise.json`) e os arquivos `LEIAME.md`, `01_pre_conferencia.sql`, `02a_teste_um_cliente.sql`, `02_insert_restricoes.sql`, `03_conferencia.sql` e `04_rollback.sql`. Sem nada a inserir, responde `409`.

## Regras

- Uma combinação está **coberta** quando já existe restrição do mesmo cliente e prazo, sem outros critérios, com origem Todas (ou a mesma origem pedida). Restrições com outros critérios (filial, tipo de pessoa etc.) aparecem em `restricoes_parciais` e não impedem a inclusão.
- Os scripts levam **só o que falta inserir**, para a reversão nunca apagar restrições que já existiam.
- O código da restrição usa `MAX + 1`. A tabela tem gatilhos de integração: avise a TI antes de executar.

## Respostas de erro

| Código | Quando |
|---|---|
| 400 | Planilha, motivo, prazo ou origem inválidos (`detail.problemas`, com o número da linha) |
| 401 / 403 | Sem token ou sem o escopo `restricao:read` |
| 409 | `formato=zip` sem nada a inserir |
| 413 | Arquivo maior que 5 MB |
| 503 | Falha ao consultar o Oracle |

## Exemplo

```bash
curl -X POST "$API/Vendas/restricoes/simular" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@clientes.xlsx" \
  -F "motivo=CLIENTE NAO PARCELA BOLETO" \
  -F "prazos=2,13,14" \
  -F "formato=zip" -o restricoes.zip
```

## Liberar o acesso

No painel `/admin/roles`, marque o escopo `restricao:read` no papel de quem vai usar (não há migração: o papel Admin não o recebe automaticamente).

## Permissões no Oracle

Só leitura: `PCCLIENT`, `PCPLPAG`, `PCPEDC` e `PCRESTRICAOVENDA`.
