"""
Gera os scripts SQL de uma simulação de restrições de venda. Os scripts são
para revisão e execução manual: a API não os executa.

Só entram nos scripts as combinações ainda não cobertas na hora da simulação;
assim a reversão (04) nunca remove restrições que já existiam.
"""
import io
import zipfile

from classes.restricao_venda import ORIGENS
from classes.restricao_venda_db import OUTROS_CRITERIOS


def _criterios_nulos() -> str:
    partes = [f"R.{c} IS NULL" for c in OUTROS_CRITERIOS]
    return "\n           AND ".join(" AND ".join(partes[i:i + 4]) for i in range(0, len(partes), 4))


def _condicao_origem(origem: str) -> str:
    if origem == "O":
        return "(R.ORIGEMPED IS NULL OR R.ORIGEMPED = 'O')"
    return f"(R.ORIGEMPED IS NULL OR R.ORIGEMPED IN ('O', '{origem}'))"


def _chamadas(procedimento: str, pares: list) -> str:
    return "\n".join(f"  {procedimento}({int(c)}, {int(p)});" for c, p in pares)


def _bloco_leitura(titulo: str, pares: list, origem: str, motivo: str) -> str:
    return f"""{titulo}
SET SERVEROUTPUT ON
SET DEFINE OFF

DECLARE
  v_cobertas NUMBER := 0;
  v_total    NUMBER := 0;
  PROCEDURE conferir(p_cli NUMBER, p_plano NUMBER) IS
    v_qt NUMBER;
  BEGIN
    SELECT COUNT(*) INTO v_qt FROM CHOCOSUL.PCRESTRICAOVENDA R
     WHERE R.CODCLI = p_cli AND R.CODPLPAG = p_plano
       AND {_condicao_origem(origem)}
       AND {_criterios_nulos()};
    v_total := v_total + 1;
    IF v_qt > 0 THEN v_cobertas := v_cobertas + 1; END IF;
  END;
BEGIN
{_chamadas("conferir", pares)}
  DBMS_OUTPUT.PUT_LINE('Combinacoes cobertas: ' || v_cobertas || ' de ' || v_total);
END;
/

-- Linhas ja gravadas com este motivo, por prazo
SELECT CODPLPAG, COUNT(*) RESTRICOES, MIN(CODRESTRICAO) PRIMEIRO_COD, MAX(CODRESTRICAO) ULTIMO_COD
  FROM CHOCOSUL.PCRESTRICAOVENDA
 WHERE MOTIVO = '{motivo}'
 GROUP BY CODPLPAG ORDER BY 1;
"""


def _insert(nome: str, pares: list, origem: str, motivo: str, nota: str) -> str:
    return f"""-- {nome}  (GRAVA NO BANCO - executar somente apos revisar e aprovar)
-- Insere {len(pares)} restricao(oes) na tabela da rotina 391. Origem {origem}, todas as filiais.
-- NAO faz COMMIT. Pula a combinacao que ja tenha restricao igual. Se houver erro, nada e gravado.
-- {nota}

SET SERVEROUTPUT ON
SET DEFINE OFF
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

DECLARE
  v_prox NUMBER;
  v_ins  NUMBER := 0;
  v_pula NUMBER := 0;
  PROCEDURE incluir(p_cli NUMBER, p_plano NUMBER) IS
    v_qt NUMBER;
  BEGIN
    SELECT COUNT(*) INTO v_qt FROM CHOCOSUL.PCRESTRICAOVENDA R
     WHERE R.CODCLI = p_cli AND R.CODPLPAG = p_plano
       AND {_condicao_origem(origem)}
       AND {_criterios_nulos()};
    IF v_qt = 0 THEN
      v_prox := v_prox + 1;
      INSERT INTO CHOCOSUL.PCRESTRICAOVENDA
             (CODRESTRICAO, CODCLI, CODPLPAG, ORIGEMPED, VALORMINIMOVENDA, MOTIVO, DTMXSALTER)
      VALUES (v_prox, p_cli, p_plano, '{origem}', 0, '{motivo}', SYSDATE);
      v_ins := v_ins + 1;
    ELSE
      v_pula := v_pula + 1;
    END IF;
  END;
BEGIN
  SELECT NVL(MAX(CODRESTRICAO), 0) INTO v_prox FROM CHOCOSUL.PCRESTRICAOVENDA;
{_chamadas("incluir", pares)}
  DBMS_OUTPUT.PUT_LINE('Inseridas: ' || v_ins || ' | ja existiam (puladas): ' || v_pula || ' | ultimo CODRESTRICAO: ' || v_prox);
  DBMS_OUTPUT.PUT_LINE('Falta o COMMIT.');
END;
/
"""


def _rollback(pares: list, origem: str, motivo: str) -> str:
    return f"""-- 04_rollback.sql  (GRAVA NO BANCO) - desfaz o 02 depois do COMMIT (antes dele basta ROLLBACK;).
-- Remove somente as combinacoes desta simulacao, com o mesmo motivo e origem.

SET SERVEROUTPUT ON
SET DEFINE OFF
WHENEVER SQLERROR EXIT FAILURE ROLLBACK

DECLARE
  v_removidas NUMBER := 0;
  PROCEDURE remover(p_cli NUMBER, p_plano NUMBER) IS
  BEGIN
    DELETE FROM CHOCOSUL.PCRESTRICAOVENDA R
     WHERE R.CODCLI = p_cli AND R.CODPLPAG = p_plano
       AND R.ORIGEMPED = '{origem}' AND R.MOTIVO = '{motivo}'
       AND {_criterios_nulos()};
    v_removidas := v_removidas + SQL%ROWCOUNT;
  END;
BEGIN
{_chamadas("remover", pares)}
  IF v_removidas > {len(pares)} THEN
    RAISE_APPLICATION_ERROR(-20001, 'Mais linhas que o esperado ({len(pares)}); nada foi removido.');
  END IF;
  DBMS_OUTPUT.PUT_LINE('Removidas: ' || v_removidas || ' (maximo esperado: {len(pares)}). Falta o COMMIT.');
END;
/
"""


def gerar_arquivos(resultado: dict) -> dict:
    """Devolve {nome_do_arquivo: texto}. Exige ao menos uma combinação a inserir."""
    pares = [(r["codcli"], r["codplpag"]) for r in resultado["a_inserir"]]
    if not pares:
        raise ValueError("Não há combinação a inserir.")
    origem = resultado["origem"]["codigo"]
    motivo = resultado["motivo"]
    primeiro = pares[0][0]
    teste = [par for par in pares if par[0] == primeiro]
    resumo = resultado["resumo"]

    leia = f"""# Restrições de venda (rotina 391) — simulação

**Nada foi executado no banco.** Estes scripts são para revisão e execução manual.

- Motivo: `{motivo}`
- Origem: {origem} ({ORIGENS[origem]}), todas as filiais, valor mínimo 0
- Combinações a inserir: **{len(pares)}** (já cobertas e fora dos scripts: {resumo["combinacoes_ja_cobertas"]})
- Assinatura da simulação: `{resultado["assinatura"]}`

## Alertas

{chr(10).join("- " + a for a in resultado["alertas"]) or "- Nenhum."}

## Ordem

| Arquivo | Grava? | Resultado esperado |
|---|---|---|
| `01_pre_conferencia.sql` | Não | 0 combinações cobertas de {len(pares)} |
| `02a_teste_um_cliente.sql` | **Sim** (sem COMMIT) | {len(teste)} inserida(s), cliente {primeiro} |
| `02_insert_restricoes.sql` | **Sim** (sem COMMIT) | {len(pares) - len(teste)} inseridas e {len(teste)} puladas, se o teste foi gravado; senão {len(pares)} e 0 |
| `03_conferencia.sql` | Não | {len(pares)} cobertas de {len(pares)} |
| `04_rollback.sql` | **Sim** | Só para desfazer depois do COMMIT |

1. Rode o `01`.
2. Rode o `02a`, dê `COMMIT` e confira o efeito (rotina 316 e um pedido de teste pela Força de Vendas, cancelado antes de faturar).
3. Rode o `02`, confira com o `03` e só então dê `COMMIT`.

## Cuidados

- A tabela tem gatilhos de integração que disparam a cada inclusão e exclusão; avise a TI.
- O código da restrição usa `MAX + 1`. Se outra pessoa incluir ao mesmo tempo, o script falha e nada é gravado.
- Se a situação mudou desde a simulação, simule de novo.
"""
    return {
        "LEIAME.md": leia,
        "01_pre_conferencia.sql": _bloco_leitura(
            f"-- 01_pre_conferencia.sql  (SOMENTE LEITURA) - esperado: 0 cobertas de {len(pares)}", pares, origem, motivo),
        "02a_teste_um_cliente.sql": _insert(
            "02a_teste_um_cliente.sql", teste, origem, motivo, f"TESTE com o cliente {primeiro} antes do 02 completo."),
        "02_insert_restricoes.sql": _insert(
            "02_insert_restricoes.sql", pares, origem, motivo, "Lista completa."),
        "03_conferencia.sql": _bloco_leitura(
            f"-- 03_conferencia.sql  (SOMENTE LEITURA) - esperado: {len(pares)} cobertas de {len(pares)}", pares, origem, motivo),
        "04_rollback.sql": _rollback(pares, origem, motivo),
    }


def gerar_zip(arquivos: dict) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as pacote:
        for nome, texto in arquivos.items():
            pacote.writestr(nome, texto.encode("utf-8"))
    return buffer.getvalue()
