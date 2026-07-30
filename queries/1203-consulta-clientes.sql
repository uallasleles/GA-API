-- ==============================================================================
-- ERP WINTHOR - ROTINA 1203 (SIMPLIFICADA)
-- Retorno: Dados Básicos, Bloqueio, Limites e Última Compra Válida
-- ==============================================================================

SELECT 
    -- Dados Básicos do Cliente
    C.CODCLI,
    C.CLIENTE,
    C.FANTASIA,
    C.CGCENT,
    
    -- Status de Bloqueio
    CASE WHEN C.BLOQUEIO = 'S' THEN 'S' ELSE 'N' END AS BLOQUEIO,
    C.MOTIVOBLOQ,
    C.DTBLOQ,
    
    -- Limites de Crédito
    COALESCE(C.LIMCRED, 0) AS LIMCREDORIGINAL,
    COALESCE(C.LIMCREDCPF, 0) AS LIMCREDCPF,
    
    -- Data da última compra válida do período
    FILTRO_PERIODO.DTULTCOMP_VALIDA,

    -- Informações de Controle e Contatos
    C.DTREGLIM,
    C.DTVENCLIMCRED,
    C.CODCOB,
    C.CODPLPAG,
    TRUNC(C.DTULTALTER1203) AS DTULTALTER1203,
    C.FANTASIA,
    C.OBS2,
    C.OBS3,
    C.OBS4,
    C.OBS5

FROM 
    PCCLIENT C
    
-- Limita a consulta apenas aos clientes que compraram no período enviado
INNER JOIN (
    SELECT 
        PC.CODCLI, 
        MAX(PC.DATA) AS DTULTCOMP_VALIDA
    FROM PCPEDC PC
    WHERE PC.CONDVENDA IN (1, 5, 8, 14, 20)
    GROUP BY PC.CODCLI
    HAVING MAX(PC.DATA) BETWEEN TO_DATE(:DATA_INICIAL, 'DD/MM/YYYY') AND TO_DATE(:DATA_FINAL, 'DD/MM/YYYY')
) FILTRO_PERIODO ON C.CODCLI = FILTRO_PERIODO.CODCLI

WHERE 
    -- Filtro opcional por código do cliente (se nulo, traz todos do período)
    (:CODCLI IS NULL OR C.CODCLI = :CODCLI)