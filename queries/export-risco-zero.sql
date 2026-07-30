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
                  como PCPREST.VALOR e PCPREST.DUPLIC — não vieram na
                  listagem de colunas que você me mandou (o script estava
                  truncado em NUMCAR), então vale conferir se existem mesmo
                  com esse nome antes de rodar em produção.
   ============================================================================= */

SELECT
      REGEXP_REPLACE(fl.CGC, '[^0-9]', '')      AS cnpjparceiro     -- CNPJ do Grupo Astoria (fixo/bind, não vem do banco)
    , REGEXP_REPLACE(cli.CGCENT, '[^0-9]', '')  AS cnpj             -- CNPJ (PJ) ou CPF (PF) do cliente na Receita Federal
    , REGEXP_REPLACE(cli.TELENT, '[^0-9]', '')  AS telefone         -- Telefone principal de contato do cliente     
    , TO_CHAR(pr.DTEMISSAO, 'YYYY-MM-DD')       AS dtalancto        -- Data de lançamento da compra/título no sistema
    , TRIM(pr.DUPLIC)                           AS numdocumento     -- Número do documento de registro no sistema
    , pr.VALOR                                  AS valor            -- Valor do título (compras parceladas: uma linha por parcela)
    , TO_CHAR(pr.DTBAIXA, 'YYYY-MM-DD')         AS dtacompensacao   -- Data em que foi efetuado o pagamento do título
    , TO_CHAR(pr.DTVENC, 'YYYY-MM-DD')          AS dtavencimento    -- Data de início de contagem para vencimento do título
FROM
    PCPREST pr
    INNER JOIN PCCLIENT cli
        ON cli.CODCLI = pr.CODCLI
	INNER JOIN PCFILIAL fl 
		ON pr.CODFILIAL = fl.CODIGO
WHERE
    pr.CODFILIAL = :CODFILIAL                     -- filtra a(s) filial(is) que farão parte do envio
    AND pr.DTEMISSAO >= TO_DATE(:DTEMISSAO_INICIAL, 'DD/MM/YYYY')        -- janela de extração (incremental) - ex: última data já exportada
    AND pr.DTEMISSAO <= TO_DATE(:DTEMISSAO_FINAL,   'DD/MM/YYYY')
    AND pr.CANCELDESD IS NULL                     -- exclui títulos com desdobramento cancelado
ORDER BY
    pr.DTEMISSAO