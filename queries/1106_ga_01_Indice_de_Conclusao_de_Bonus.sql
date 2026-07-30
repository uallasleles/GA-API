-- ========================================================================================
-- Script 1106-GA-01 - DASHBOARD / KPI DE ÍNDICE DE CONCLUSÃO DE BÔNUS
-- OBJETIVO: Calcular a volumetria de bônus por status (Fechados, Pendentes, Cancelados)
--           e extrair o índice percentual de eficiência/vazão de recebimento do CD.
-- ========================================================================================

SELECT 
    filial,
    total_gerado,
    total_fechados,
    total_pendentes,
    total_cancelados,
    valor_total_patio,
    
    -- CÁLCULO DO ÍNDICE: (Fechados / Total Gerado) * 100
    ROUND(
        CASE 
            WHEN total_gerado = 0 THEN 0 
            ELSE (total_fechados / total_gerado) * 100 
        END, 2
    ) AS indice_conclusao_pct

FROM (
    -- SUBSELECT: Consolida os contadores utilizando a lógica de filtros dos seus scripts
    SELECT 
        c.codfilial AS filial,
        COUNT(c.numbonus) AS total_gerado,
        
        -- Conta bônus fechados (dtfechamento preenchida e não cancelado)
        COUNT(CASE WHEN c.dtfechamento IS NOT NULL AND c.dtcancel IS NULL THEN 1 END) AS total_fechados,
        
        -- Conta bônus pendentes (dtfechamento nula e não cancelado)
        COUNT(CASE WHEN c.dtfechamento IS NULL AND c.dtcancel IS NULL THEN 1 END) AS total_pendentes,
        
        -- Conta bônus abortados/cancelados
        COUNT(CASE WHEN c.dtcancel IS NOT NULL THEN 1 END) AS total_cancelados,
        
        -- Valor financeiro total que entrou no pátio do CD
        SUM(NVL(c.valortotal, 0)) AS valor_total_patio

    FROM pcbonusc c
    
    WHERE c.codfilial = :CODFILIAL
      AND TRUNC(c.databonus) BETWEEN TO_DATE(:DT_INICIO, 'DD-MM-YYYY') AND TO_DATE(:DT_FIM, 'DD-MM-YYYY')
      
    GROUP BY 
        c.codfilial
)