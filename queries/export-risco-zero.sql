/* =============================================================================
   FINALIDADE ..: Extração de dados de Contas a Receber para exportação ao
                  BigQuery da Risco Zero (gestão de dados, análise de crédito
                  e avaliação de risco de inadimplência).
   ORIGEM ......: WinThor (PCPREST - títulos de cobrança / PCCLIENT - cadastro
                  de clientes)
   LAYOUT ......: cnpjparceiro (STRING) | cnpj (STRING) | telefone (STRING)
                  | dtalancto (DATE) | numdocumento (STRING) | valor (FLOAT)
                  | dtacompensacao (DATE) | dtavencimento (DATE)
   OBSERVAÇÃO ..: Ajustei nomes de coluna do PCCLIENT (CGCENT, TELENT) pelo
                  padrão usual do WinThor — confirme no seu ambiente, pois
                  pode variar conforme customização/versão (ex.: TELENT1,
                  TELCOM, FONE). Da PCPREST usei DTEMISSAO, DTVENC e DTBAIXA,
                  que já documentamos juntos; VALOR e NUMDOCUMENTO eu supus
                  como prest.VALOR e prest.DUPLIC — não vieram na
                  listagem de colunas que você me mandou (o script estava
                  truncado em NUMCAR), então vale conferir se existem mesmo
                  com esse nome antes de rodar em produção.
   ============================================================================= */

SELECT
      REGEXP_REPLACE(filial.CGC, '[^0-9]', '')     AS cnpjparceiro     -- CNPJ da Filial do Grupo Astoria
    , REGEXP_REPLACE(client.CGCENT, '[^0-9]', '')  AS cnpj             -- CNPJ (PJ) ou CPF (PF) do cliente na Receita Federal
    , REGEXP_REPLACE(client.TELENT, '[^0-9]', '')  AS telefone         -- Telefone principal de contato do cliente
    , TO_CHAR(prest.DTEMISSAO, 'DD/MM/YYYY')       AS dtalancto        -- Data de lançamento da compra/título no sistema
    , TRIM(prest.DUPLIC)                           AS numdocumento     -- Número do documento de registro no sistema
    , prest.VALOR                                  AS valor            -- Valor do título (compras parceladas: uma linha por parcela)
    , TO_CHAR(prest.DTBAIXA, 'DD/MM/YYYY')         AS dtacompensacao   -- Data em que foi efetuado o pagamento do título
    , TO_CHAR(prest.DTVENC, 'DD/MM/YYYY')          AS dtavencimento    -- Data de início de contagem para vencimento do título
	
FROM
    PCPREST prest
    INNER JOIN PCCLIENT client
        ON client.CODCLI = prest.CODCLI
	INNER JOIN PCFILIAL filial 
		ON prest.CODFILIAL = filial.CODIGO

WHERE 1=1
    AND prest.CODFILIAL = NVL(:CODFILIAL, prest.CODFILIAL)           	-- filtra a(s) filial(is) que farão parte do envio
    AND prest.DTEMISSAO >= TO_DATE(:DTEMISSAO_INICIAL, 'DD/MM/YYYY') 	-- janela de extração (incremental) - ex: última data já exportada
    AND prest.DTEMISSAO <= TO_DATE(:DTEMISSAO_FINAL,   'DD/MM/YYYY')  
    AND prest.CANCELDESD IS NULL                                     	-- exclui títulos com desdobramento cancelado
    AND prest.CODCOB NOT IN ('DEVT', 'BNF', 'CAN')    					-- Exclui devoluções, bonificações e cancelados
    AND prest.VALOR > 0                               					-- Garante apenas títulos com valor a receber
    -- AND prest.DTPAG IS NULL                        					-- Apenas títulos não baixados

ORDER BY 
    prest.DTEMISSAO